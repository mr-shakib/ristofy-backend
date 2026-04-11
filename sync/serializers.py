from django.utils import timezone
from rest_framework import serializers

from tenants.models import Branch

from .models import Device, OutboxEvent, SyncPushRecord


class DeviceRegisterSerializer(serializers.Serializer):
    device_uuid = serializers.CharField(max_length=64)
    name = serializers.CharField(max_length=120)
    device_type = serializers.ChoiceField(choices=Device.DeviceType.choices, default=Device.DeviceType.POS)
    app_version = serializers.CharField(max_length=32, required=False, allow_blank=True, default="")
    branch_id = serializers.IntegerField()

    def validate(self, attrs):
        request = self.context["request"]
        try:
            branch = Branch.objects.get(pk=attrs["branch_id"], tenant=request.user.tenant)
        except Branch.DoesNotExist:
            raise serializers.ValidationError({"branch_id": "Branch not found or does not belong to your tenant."})
        attrs["branch"] = branch
        return attrs


class DeviceHeartbeatSerializer(serializers.Serializer):
    device_uuid = serializers.CharField(max_length=64)
    app_version = serializers.CharField(max_length=32, required=False, allow_blank=True, default="")

    def validate_device_uuid(self, value):
        request = self.context["request"]
        try:
            device = Device.objects.get(device_uuid=value, tenant=request.user.tenant, is_active=True)
        except Device.DoesNotExist:
            raise serializers.ValidationError("Device not found or inactive.")
        self._device = device
        return value

    def get_device(self):
        return self._device


class PushItemSerializer(serializers.Serializer):
    idempotency_key = serializers.CharField(max_length=128)
    entity_type = serializers.CharField(max_length=64)
    entity_id = serializers.CharField(max_length=64)
    device_updated_at = serializers.DateTimeField(required=False, allow_null=True, default=None)
    payload = serializers.DictField(child=serializers.JSONField(), required=False, default=dict)


class SyncPushSerializer(serializers.Serializer):
    device_uuid = serializers.CharField(max_length=64)
    items = serializers.ListField(child=PushItemSerializer(), min_length=1, max_length=100)

    def validate_device_uuid(self, value):
        request = self.context["request"]
        try:
            device = Device.objects.get(device_uuid=value, tenant=request.user.tenant, is_active=True)
        except Device.DoesNotExist:
            raise serializers.ValidationError("Device not found or inactive.")
        self._device = device
        return value

    def get_device(self):
        return self._device


class SyncPullSerializer(serializers.Serializer):
    device_uuid = serializers.CharField(max_length=64)
    cursor = serializers.IntegerField(min_value=0, default=0)
    branch_id = serializers.IntegerField()
    limit = serializers.IntegerField(min_value=1, max_value=200, default=100)

    def validate(self, attrs):
        request = self.context["request"]
        try:
            branch = Branch.objects.get(pk=attrs["branch_id"], tenant=request.user.tenant)
        except Branch.DoesNotExist:
            raise serializers.ValidationError({"branch_id": "Branch not found or does not belong to your tenant."})
        attrs["branch"] = branch

        try:
            device = Device.objects.get(
                device_uuid=attrs["device_uuid"],
                tenant=request.user.tenant,
                is_active=True,
            )
        except Device.DoesNotExist:
            raise serializers.ValidationError({"device_uuid": "Device not found or inactive."})
        attrs["device"] = device
        return attrs


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = [
            "id",
            "device_uuid",
            "name",
            "device_type",
            "app_version",
            "is_active",
            "registered_at",
            "last_seen_at",
        ]
        read_only_fields = fields


class OutboxEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = OutboxEvent
        fields = ["id", "entity_type", "entity_id", "event_type", "payload_json", "created_at"]
        read_only_fields = fields
