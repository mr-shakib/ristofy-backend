from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from users.audit import log_activity

from .models import Device, OutboxEvent, SyncPushRecord
from .serializers import (
    DeviceHeartbeatSerializer,
    DeviceRegisterSerializer,
    DeviceSerializer,
    OutboxEventSerializer,
    SyncPullSerializer,
    SyncPushSerializer,
)


class DeviceRegisterView(APIView):
    """Register a new device or update an existing one for a branch."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = DeviceRegisterSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        device, created = Device.objects.update_or_create(
            device_uuid=data["device_uuid"],
            defaults={
                "tenant": request.user.tenant,
                "branch": data["branch"],
                "name": data["name"],
                "device_type": data["device_type"],
                "app_version": data["app_version"],
                "is_active": True,
            },
        )

        if created:
            log_activity(
                actor_user=request.user,
                action="device_registered",
                entity_type="device",
                entity_id=str(device.id),
                tenant=request.user.tenant,
                branch=data["branch"],
                metadata={"device_uuid": device.device_uuid, "name": device.name},
            )
        else:
            log_activity(
                actor_user=request.user,
                action="device_updated",
                entity_type="device",
                entity_id=str(device.id),
                tenant=request.user.tenant,
                branch=data["branch"],
                metadata={"device_uuid": device.device_uuid, "name": device.name},
            )

        return Response(
            DeviceSerializer(device).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class DeviceHeartbeatView(APIView):
    """Update last_seen_at for a registered device."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = DeviceHeartbeatSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        device = serializer.get_device()

        if data["app_version"]:
            device.app_version = data["app_version"]
        device.touch()

        return Response(
            {
                "device_uuid": device.device_uuid,
                "last_seen_at": device.last_seen_at,
                "status": "ok",
            },
            status=status.HTTP_200_OK,
        )


class SyncPushView(APIView):
    """
    Device pushes locally-created or locally-modified records.

    Conflict policy:
    - If server entity was updated after device_updated_at, the item is marked CONFLICT
      and the server version wins (the push is not applied).
    - Idempotency: re-submitting an already-processed idempotency_key returns the stored
      result without re-processing.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = SyncPushSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        device = serializer.get_device()

        results = []
        for item in data["items"]:
            idempotency_key = item["idempotency_key"]

            # Idempotency: return stored result if already processed
            existing = SyncPushRecord.objects.filter(idempotency_key=idempotency_key).first()
            if existing:
                results.append(
                    {
                        "idempotency_key": idempotency_key,
                        "entity_type": existing.entity_type,
                        "entity_id": existing.entity_id,
                        "status": existing.status,
                        "conflict_detail": existing.conflict_detail,
                    }
                )
                continue

            entity_type = item["entity_type"]
            entity_id = item["entity_id"]
            device_updated_at = item.get("device_updated_at")
            payload = item.get("payload", {})

            push_status = SyncPushRecord.PushStatus.ACCEPTED
            conflict_detail = ""
            server_entity_updated_at = None

            # Conflict detection: resolve using server timestamp
            if device_updated_at is not None:
                server_updated_at = _get_server_entity_updated_at(entity_type, entity_id, request.user.tenant)
                if server_updated_at is not None:
                    server_entity_updated_at = server_updated_at
                    if server_updated_at > device_updated_at:
                        push_status = SyncPushRecord.PushStatus.CONFLICT
                        conflict_detail = (
                            f"Server version updated at {server_updated_at.isoformat()} "
                            f"is newer than device version at {device_updated_at.isoformat()}."
                        )

            SyncPushRecord.objects.create(
                tenant=request.user.tenant,
                branch=device.branch,
                device=device,
                idempotency_key=idempotency_key,
                entity_type=entity_type,
                entity_id=entity_id,
                payload_json=payload,
                status=push_status,
                conflict_detail=conflict_detail,
                device_updated_at=device_updated_at,
                server_entity_updated_at=server_entity_updated_at,
            )

            results.append(
                {
                    "idempotency_key": idempotency_key,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "status": push_status,
                    "conflict_detail": conflict_detail,
                }
            )

        device.touch()

        return Response({"device_uuid": device.device_uuid, "results": results}, status=status.HTTP_200_OK)


class SyncPullView(APIView):
    """
    Device pulls server-side events since its last cursor.

    cursor: the id of the last OutboxEvent the device received (0 = first pull).
    Returns events with id > cursor up to `limit`, plus a next_cursor for subsequent calls.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = SyncPullSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        device = data["device"]
        branch = data["branch"]
        cursor = data["cursor"]
        limit = data["limit"]

        events = (
            OutboxEvent.objects.filter(
                tenant=request.user.tenant,
                branch=branch,
                id__gt=cursor,
            )
            .order_by("id")[:limit]
        )

        event_list = list(events)
        next_cursor = event_list[-1].id if event_list else cursor

        device.touch()

        return Response(
            {
                "device_uuid": device.device_uuid,
                "cursor": cursor,
                "next_cursor": next_cursor,
                "has_more": len(event_list) == limit,
                "events": OutboxEventSerializer(event_list, many=True).data,
            },
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# Internal helper — resolve server-side updated_at for a given entity
# ---------------------------------------------------------------------------

def _get_server_entity_updated_at(entity_type, entity_id, tenant):
    """
    Return the server-side updated_at for a known entity, or None if not found.
    Covers the most common sync-able entities: order, menu_item, ingredient.
    """
    try:
        entity_id_int = int(entity_id)
    except (ValueError, TypeError):
        return None

    if entity_type == "order":
        from orders.models import Order
        obj = Order.objects.filter(id=entity_id_int, tenant=tenant).only("updated_at").first()
        return obj.updated_at if obj else None

    if entity_type == "menu_item":
        from menu.models import MenuItem
        obj = MenuItem.objects.filter(id=entity_id_int, tenant=tenant).only("updated_at").first()
        return obj.updated_at if obj else None

    if entity_type == "ingredient":
        from inventory.models import Ingredient
        obj = Ingredient.objects.filter(id=entity_id_int, tenant=tenant).only("updated_at").first()
        return obj.updated_at if obj else None

    return None
