from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import StandardResultsSetPagination
from users.audit import log_activity
from users.permissions import IsOwnerOrManager

from .models import DiningTable, FloorPlan, Reservation, TableMergeSession, TableSession, WaitlistEntry
from .serializers import (
    DiningTableSerializer,
    FloorPlanSerializer,
    ReservationSerializer,
    TableMergeSessionSerializer,
    TableSessionSerializer,
    WaitlistEntrySerializer,
)
from .services import sync_table_state_for_reservation, sync_table_state_for_table, sync_table_state_for_waitlist


class FloorPlanListCreateView(generics.ListCreateAPIView):
    serializer_class = FloorPlanSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = (
            FloorPlan.objects.filter(branch__tenant=self.request.user.tenant)
            .select_related("branch")
            .order_by("id")
        )
        params = self.request.query_params

        branch = params.get("branch")
        if branch:
            queryset = queryset.filter(branch_id=branch)

        is_active = params.get("is_active")
        if is_active is not None:
            is_active_value = is_active.lower() in {"1", "true", "yes", "on"}
            queryset = queryset.filter(is_active=is_active_value)

        q = params.get("q")
        if q:
            queryset = queryset.filter(name__icontains=q)

        return queryset

    def perform_create(self, serializer):
        floor_plan = serializer.save()
        log_activity(
            actor_user=self.request.user,
            action="floor_plan_created",
            entity_type="floor_plan",
            entity_id=str(floor_plan.id),
            tenant=self.request.user.tenant,
            branch=floor_plan.branch,
        )


class FloorPlanDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FloorPlanSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def get_queryset(self):
        return FloorPlan.objects.filter(branch__tenant=self.request.user.tenant).select_related("branch")

    def perform_update(self, serializer):
        floor_plan = serializer.save()
        log_activity(
            actor_user=self.request.user,
            action="floor_plan_updated",
            entity_type="floor_plan",
            entity_id=str(floor_plan.id),
            tenant=self.request.user.tenant,
            branch=floor_plan.branch,
        )

    def perform_destroy(self, instance):
        log_activity(
            actor_user=self.request.user,
            action="floor_plan_deleted",
            entity_type="floor_plan",
            entity_id=str(instance.id),
            tenant=self.request.user.tenant,
            branch=instance.branch,
        )
        instance.delete()


class DiningTableListCreateView(generics.ListCreateAPIView):
    serializer_class = DiningTableSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = (
            DiningTable.objects.filter(branch__tenant=self.request.user.tenant)
            .select_related("branch", "floor_plan")
            .order_by("id")
        )
        params = self.request.query_params

        branch = params.get("branch")
        if branch:
            queryset = queryset.filter(branch_id=branch)

        floor_plan = params.get("floor_plan")
        if floor_plan:
            queryset = queryset.filter(floor_plan_id=floor_plan)

        state = params.get("state")
        if state:
            queryset = queryset.filter(state=state)

        q = params.get("q")
        if q:
            queryset = queryset.filter(code__icontains=q)

        return queryset

    def perform_create(self, serializer):
        table = serializer.save()
        log_activity(
            actor_user=self.request.user,
            action="table_created",
            entity_type="table",
            entity_id=str(table.id),
            tenant=self.request.user.tenant,
            branch=table.branch,
        )


class DiningTableDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DiningTableSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def get_queryset(self):
        return DiningTable.objects.filter(branch__tenant=self.request.user.tenant).select_related("branch", "floor_plan")

    def perform_update(self, serializer):
        table = serializer.save()
        log_activity(
            actor_user=self.request.user,
            action="table_updated",
            entity_type="table",
            entity_id=str(table.id),
            tenant=self.request.user.tenant,
            branch=table.branch,
        )

    def perform_destroy(self, instance):
        log_activity(
            actor_user=self.request.user,
            action="table_deleted",
            entity_type="table",
            entity_id=str(instance.id),
            tenant=self.request.user.tenant,
            branch=instance.branch,
        )
        instance.delete()


class ReservationListCreateView(generics.ListCreateAPIView):
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = (
            Reservation.objects.filter(branch__tenant=self.request.user.tenant)
            .select_related("branch", "table")
            .order_by("id")
        )
        params = self.request.query_params

        branch = params.get("branch")
        if branch:
            queryset = queryset.filter(branch_id=branch)

        table = params.get("table")
        if table:
            queryset = queryset.filter(table_id=table)

        status = params.get("status")
        if status:
            queryset = queryset.filter(status=status)

        reserved_from = params.get("reserved_from")
        if reserved_from:
            queryset = queryset.filter(reserved_for__gte=reserved_from)

        reserved_to = params.get("reserved_to")
        if reserved_to:
            queryset = queryset.filter(reserved_for__lte=reserved_to)

        q = params.get("q")
        if q:
            queryset = queryset.filter(customer_name__icontains=q)

        return queryset

    def perform_create(self, serializer):
        reservation = serializer.save()
        sync_table_state_for_reservation(reservation)
        log_activity(
            actor_user=self.request.user,
            action="reservation_created",
            entity_type="reservation",
            entity_id=str(reservation.id),
            tenant=self.request.user.tenant,
            branch=reservation.branch,
        )


class ReservationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def get_queryset(self):
        return Reservation.objects.filter(branch__tenant=self.request.user.tenant).select_related("branch", "table")

    def perform_update(self, serializer):
        reservation = serializer.save()
        sync_table_state_for_reservation(reservation)
        log_activity(
            actor_user=self.request.user,
            action="reservation_updated",
            entity_type="reservation",
            entity_id=str(reservation.id),
            tenant=self.request.user.tenant,
            branch=reservation.branch,
        )

    def perform_destroy(self, instance):
        table = instance.table
        log_activity(
            actor_user=self.request.user,
            action="reservation_deleted",
            entity_type="reservation",
            entity_id=str(instance.id),
            tenant=self.request.user.tenant,
            branch=instance.branch,
        )
        instance.delete()
        sync_table_state_for_table(table)


class ReservationArrivedView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def post(self, request, pk):
        try:
            reservation = Reservation.objects.select_related("branch", "table").get(pk=pk, branch__tenant=request.user.tenant)
        except Reservation.DoesNotExist:
            return Response({"detail": "Reservation not found."}, status=status.HTTP_404_NOT_FOUND)

        if reservation.status == Reservation.Status.CANCELED:
            return Response(
                {"detail": "Canceled reservations cannot be marked as arrived."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reservation.status = Reservation.Status.ARRIVED
        reservation.save(update_fields=["status", "updated_at"])
        sync_table_state_for_reservation(reservation)

        log_activity(
            actor_user=request.user,
            action="reservation_arrived",
            entity_type="reservation",
            entity_id=str(reservation.id),
            tenant=request.user.tenant,
            branch=reservation.branch,
        )

        return Response(ReservationSerializer(reservation, context={"request": request}).data, status=status.HTTP_200_OK)


class ReservationCancelView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def post(self, request, pk):
        try:
            reservation = Reservation.objects.select_related("branch", "table").get(pk=pk, branch__tenant=request.user.tenant)
        except Reservation.DoesNotExist:
            return Response({"detail": "Reservation not found."}, status=status.HTTP_404_NOT_FOUND)

        reservation.status = Reservation.Status.CANCELED
        reservation.save(update_fields=["status", "updated_at"])
        sync_table_state_for_reservation(reservation)

        log_activity(
            actor_user=request.user,
            action="reservation_canceled",
            entity_type="reservation",
            entity_id=str(reservation.id),
            tenant=request.user.tenant,
            branch=reservation.branch,
        )

        return Response(ReservationSerializer(reservation, context={"request": request}).data, status=status.HTTP_200_OK)


class WaitlistEntryListCreateView(generics.ListCreateAPIView):
    serializer_class = WaitlistEntrySerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = (
            WaitlistEntry.objects.filter(branch__tenant=self.request.user.tenant)
            .select_related("branch", "table")
            .order_by("id")
        )
        params = self.request.query_params

        branch = params.get("branch")
        if branch:
            queryset = queryset.filter(branch_id=branch)

        table = params.get("table")
        if table:
            queryset = queryset.filter(table_id=table)

        status_value = params.get("status")
        if status_value:
            queryset = queryset.filter(status=status_value)

        q = params.get("q")
        if q:
            queryset = queryset.filter(customer_name__icontains=q)

        return queryset

    def perform_create(self, serializer):
        waitlist_entry = serializer.save()
        sync_table_state_for_waitlist(waitlist_entry)
        log_activity(
            actor_user=self.request.user,
            action="waitlist_entry_created",
            entity_type="waitlist_entry",
            entity_id=str(waitlist_entry.id),
            tenant=self.request.user.tenant,
            branch=waitlist_entry.branch,
        )


class WaitlistEntryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = WaitlistEntrySerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def get_queryset(self):
        return WaitlistEntry.objects.filter(branch__tenant=self.request.user.tenant).select_related("branch", "table")

    def perform_update(self, serializer):
        previous_table = serializer.instance.table
        waitlist_entry = serializer.save()
        sync_table_state_for_waitlist(waitlist_entry)
        if previous_table and previous_table != waitlist_entry.table:
            sync_table_state_for_table(previous_table)
        log_activity(
            actor_user=self.request.user,
            action="waitlist_entry_updated",
            entity_type="waitlist_entry",
            entity_id=str(waitlist_entry.id),
            tenant=self.request.user.tenant,
            branch=waitlist_entry.branch,
        )

    def perform_destroy(self, instance):
        table = instance.table
        log_activity(
            actor_user=self.request.user,
            action="waitlist_entry_deleted",
            entity_type="waitlist_entry",
            entity_id=str(instance.id),
            tenant=self.request.user.tenant,
            branch=instance.branch,
        )
        instance.delete()
        sync_table_state_for_table(table)


class WaitlistEntryCallView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def post(self, request, pk):
        try:
            waitlist_entry = WaitlistEntry.objects.select_related("branch", "table").get(
                pk=pk,
                branch__tenant=request.user.tenant,
            )
        except WaitlistEntry.DoesNotExist:
            return Response({"detail": "Waitlist entry not found."}, status=status.HTTP_404_NOT_FOUND)

        if waitlist_entry.status == WaitlistEntry.Status.CANCELED:
            return Response(
                {"detail": "Canceled waitlist entries cannot be called."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        waitlist_entry.status = WaitlistEntry.Status.CALLED
        waitlist_entry.save(update_fields=["status", "updated_at"])
        sync_table_state_for_waitlist(waitlist_entry)
        log_activity(
            actor_user=request.user,
            action="waitlist_entry_called",
            entity_type="waitlist_entry",
            entity_id=str(waitlist_entry.id),
            tenant=request.user.tenant,
            branch=waitlist_entry.branch,
        )
        return Response(WaitlistEntrySerializer(waitlist_entry, context={"request": request}).data, status=status.HTTP_200_OK)


class WaitlistEntrySeatView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def post(self, request, pk):
        try:
            waitlist_entry = WaitlistEntry.objects.select_related("branch", "table").get(
                pk=pk,
                branch__tenant=request.user.tenant,
            )
        except WaitlistEntry.DoesNotExist:
            return Response({"detail": "Waitlist entry not found."}, status=status.HTTP_404_NOT_FOUND)

        if waitlist_entry.status == WaitlistEntry.Status.CANCELED:
            return Response(
                {"detail": "Canceled waitlist entries cannot be seated."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not waitlist_entry.table_id:
            return Response(
                {"detail": "A table must be assigned before seating this waitlist entry."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        waitlist_entry.status = WaitlistEntry.Status.SEATED
        waitlist_entry.seated_at = timezone.now()
        waitlist_entry.save(update_fields=["status", "seated_at", "updated_at"])
        sync_table_state_for_waitlist(waitlist_entry)
        log_activity(
            actor_user=request.user,
            action="waitlist_entry_seated",
            entity_type="waitlist_entry",
            entity_id=str(waitlist_entry.id),
            tenant=request.user.tenant,
            branch=waitlist_entry.branch,
        )
        return Response(WaitlistEntrySerializer(waitlist_entry, context={"request": request}).data, status=status.HTTP_200_OK)


class WaitlistEntryCancelView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def post(self, request, pk):
        try:
            waitlist_entry = WaitlistEntry.objects.select_related("branch", "table").get(
                pk=pk,
                branch__tenant=request.user.tenant,
            )
        except WaitlistEntry.DoesNotExist:
            return Response({"detail": "Waitlist entry not found."}, status=status.HTTP_404_NOT_FOUND)

        waitlist_entry.status = WaitlistEntry.Status.CANCELED
        waitlist_entry.save(update_fields=["status", "updated_at"])
        sync_table_state_for_waitlist(waitlist_entry)
        log_activity(
            actor_user=request.user,
            action="waitlist_entry_canceled",
            entity_type="waitlist_entry",
            entity_id=str(waitlist_entry.id),
            tenant=request.user.tenant,
            branch=waitlist_entry.branch,
        )
        return Response(WaitlistEntrySerializer(waitlist_entry, context={"request": request}).data, status=status.HTTP_200_OK)


class TableOpenSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def post(self, request, pk):
        try:
            table = DiningTable.objects.select_related("branch").get(pk=pk, branch__tenant=request.user.tenant)
        except DiningTable.DoesNotExist:
            return Response({"detail": "Table not found."}, status=status.HTTP_404_NOT_FOUND)

        if table.state == DiningTable.State.OCCUPIED:
            return Response({"detail": "Table already has an open session."}, status=status.HTTP_400_BAD_REQUEST)

        covers = request.data.get("covers", 1)
        seat_map_json = request.data.get("seat_map_json", {})

        session = TableSession.objects.create(
            branch=table.branch,
            table=table,
            opened_by=request.user,
            covers=covers,
            seat_map_json=seat_map_json,
        )
        table.state = DiningTable.State.OCCUPIED
        table.save(update_fields=["state", "updated_at"])

        log_activity(
            actor_user=request.user,
            action="table_session_opened",
            entity_type="table_session",
            entity_id=str(session.id),
            tenant=request.user.tenant,
            branch=table.branch,
        )
        return Response(TableSessionSerializer(session).data, status=status.HTTP_201_CREATED)


class TableCloseSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def post(self, request, pk):
        try:
            table = DiningTable.objects.select_related("branch").get(pk=pk, branch__tenant=request.user.tenant)
        except DiningTable.DoesNotExist:
            return Response({"detail": "Table not found."}, status=status.HTTP_404_NOT_FOUND)

        session = TableSession.objects.filter(table=table, closed_at__isnull=True).first()
        if not session:
            return Response({"detail": "No open session for this table."}, status=status.HTTP_400_BAD_REQUEST)

        session.closed_at = timezone.now()
        session.save(update_fields=["closed_at"])

        table.state = DiningTable.State.FREE
        table.save(update_fields=["state", "updated_at"])

        log_activity(
            actor_user=request.user,
            action="table_session_closed",
            entity_type="table_session",
            entity_id=str(session.id),
            tenant=request.user.tenant,
            branch=table.branch,
        )
        return Response(TableSessionSerializer(session).data, status=status.HTTP_200_OK)


class TableMergeView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def post(self, request):
        primary_table_id = request.data.get("primary_table")
        merged_table_ids = request.data.get("merged_table_ids", [])

        if not primary_table_id:
            return Response({"detail": "primary_table is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not merged_table_ids:
            return Response({"detail": "merged_table_ids must not be empty."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            primary_table = DiningTable.objects.select_related("branch").get(
                pk=primary_table_id, branch__tenant=request.user.tenant
            )
        except DiningTable.DoesNotExist:
            return Response({"detail": "Primary table not found."}, status=status.HTTP_404_NOT_FOUND)

        if str(primary_table_id) in [str(i) for i in merged_table_ids]:
            return Response({"detail": "primary_table cannot be in merged_table_ids."}, status=status.HTTP_400_BAD_REQUEST)

        valid_count = DiningTable.objects.filter(
            id__in=merged_table_ids, branch=primary_table.branch
        ).count()
        if valid_count != len(merged_table_ids):
            return Response({"detail": "One or more merged tables not found in this branch."}, status=status.HTTP_400_BAD_REQUEST)

        merge_session = TableMergeSession.objects.create(
            branch=primary_table.branch,
            primary_table=primary_table,
            merged_table_ids=merged_table_ids,
            started_by=request.user,
        )
        log_activity(
            actor_user=request.user,
            action="table_merge_started",
            entity_type="table_merge_session",
            entity_id=str(merge_session.id),
            tenant=request.user.tenant,
            branch=primary_table.branch,
        )
        return Response(TableMergeSessionSerializer(merge_session).data, status=status.HTTP_201_CREATED)


class TableSplitView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def post(self, request, pk):
        try:
            merge_session = TableMergeSession.objects.select_related("branch", "primary_table").get(
                pk=pk, branch__tenant=request.user.tenant
            )
        except TableMergeSession.DoesNotExist:
            return Response({"detail": "Merge session not found."}, status=status.HTTP_404_NOT_FOUND)

        if merge_session.ended_at is not None:
            return Response({"detail": "Merge session is already ended."}, status=status.HTTP_400_BAD_REQUEST)

        merge_session.ended_at = timezone.now()
        merge_session.save(update_fields=["ended_at"])

        log_activity(
            actor_user=request.user,
            action="table_merge_ended",
            entity_type="table_merge_session",
            entity_id=str(merge_session.id),
            tenant=request.user.tenant,
            branch=merge_session.branch,
        )
        return Response(TableMergeSessionSerializer(merge_session).data, status=status.HTTP_200_OK)


class TableSessionListView(generics.ListAPIView):
    serializer_class = TableSessionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = (
            TableSession.objects.filter(branch__tenant=self.request.user.tenant)
            .select_related("branch", "table", "opened_by")
            .order_by("-opened_at")
        )
        params = self.request.query_params
        branch = params.get("branch")
        if branch:
            queryset = queryset.filter(branch_id=branch)
        table = params.get("table")
        if table:
            queryset = queryset.filter(table_id=table)
        is_open = params.get("is_open")
        if is_open is not None:
            if is_open.lower() in {"1", "true", "yes"}:
                queryset = queryset.filter(closed_at__isnull=True)
            else:
                queryset = queryset.filter(closed_at__isnull=False)
        return queryset


class TableLiveStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def get(self, request):
        params = request.query_params
        queryset = (
            DiningTable.objects.filter(branch__tenant=request.user.tenant)
            .select_related("branch", "floor_plan")
            .order_by("id")
        )
        branch = params.get("branch")
        if branch:
            queryset = queryset.filter(branch_id=branch)

        floor_plan = params.get("floor_plan")
        if floor_plan:
            queryset = queryset.filter(floor_plan_id=floor_plan)

        open_sessions = {
            s.table_id: s
            for s in TableSession.objects.filter(
                table__in=queryset, closed_at__isnull=True
            ).select_related("opened_by")
        }
        active_merges = {
            m.primary_table_id: m
            for m in TableMergeSession.objects.filter(
                primary_table__in=queryset, ended_at__isnull=True
            )
        }

        result = []
        for table in queryset:
            session = open_sessions.get(table.id)
            merge = active_merges.get(table.id)
            entry = {
                "id": table.id,
                "code": table.code,
                "seats": table.seats,
                "state": table.state,
                "floor_plan": table.floor_plan_id,
                "x": table.x,
                "y": table.y,
                "open_session": TableSessionSerializer(session).data if session else None,
                "active_merge": TableMergeSessionSerializer(merge).data if merge else None,
            }
            result.append(entry)

        return Response(result, status=status.HTTP_200_OK)
