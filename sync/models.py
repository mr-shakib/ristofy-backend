import uuid

from django.db import models
from django.utils import timezone


class Device(models.Model):
    class DeviceType(models.TextChoices):
        POS = "POS", "Point of Sale"
        KDS = "KDS", "Kitchen Display"
        TABLET = "TABLET", "Tablet"
        MOBILE = "MOBILE", "Mobile"

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="devices")
    branch = models.ForeignKey("tenants.Branch", on_delete=models.CASCADE, related_name="devices")
    device_uuid = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=120)
    device_type = models.CharField(max_length=16, choices=DeviceType.choices, default=DeviceType.POS)
    app_version = models.CharField(max_length=32, blank=True)
    is_active = models.BooleanField(default=True)
    registered_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-registered_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["branch", "name"],
                name="uniq_device_name_per_branch",
            )
        ]

    def __str__(self):
        return f"{self.name} [{self.device_type}] ({self.branch.name})"

    def touch(self):
        self.last_seen_at = timezone.now()
        self.save(update_fields=["last_seen_at"])


class OutboxEvent(models.Model):
    """Append-only server event log. Clients pull events since their last cursor (id)."""

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="outbox_events")
    branch = models.ForeignKey("tenants.Branch", on_delete=models.CASCADE, related_name="outbox_events")
    entity_type = models.CharField(max_length=64)
    entity_id = models.CharField(max_length=64)
    event_type = models.CharField(max_length=32)
    payload_json = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"OutboxEvent #{self.id} {self.entity_type}.{self.event_type} ({self.branch.name})"


class SyncPushRecord(models.Model):
    """Idempotency record and conflict audit for device push operations."""

    class PushStatus(models.TextChoices):
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"
        CONFLICT = "CONFLICT", "Conflict"

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="sync_push_records")
    branch = models.ForeignKey("tenants.Branch", on_delete=models.CASCADE, related_name="sync_push_records")
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="push_records")
    idempotency_key = models.CharField(max_length=128, unique=True)
    entity_type = models.CharField(max_length=64)
    entity_id = models.CharField(max_length=64)
    payload_json = models.JSONField(default=dict)
    status = models.CharField(max_length=16, choices=PushStatus.choices, default=PushStatus.ACCEPTED)
    conflict_detail = models.CharField(max_length=255, blank=True)
    device_updated_at = models.DateTimeField(null=True, blank=True)
    server_entity_updated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"SyncPush {self.idempotency_key} [{self.status}]"
