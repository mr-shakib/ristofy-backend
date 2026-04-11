from django.contrib import admin

from .models import Device, OutboxEvent, SyncPushRecord


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ["name", "device_type", "device_uuid", "branch", "is_active", "last_seen_at"]
    list_filter = ["device_type", "is_active", "branch__tenant"]
    search_fields = ["name", "device_uuid"]
    ordering = ["-registered_at"]


@admin.register(OutboxEvent)
class OutboxEventAdmin(admin.ModelAdmin):
    list_display = ["id", "entity_type", "entity_id", "event_type", "branch", "created_at"]
    list_filter = ["entity_type", "event_type", "branch__tenant"]
    ordering = ["-id"]


@admin.register(SyncPushRecord)
class SyncPushRecordAdmin(admin.ModelAdmin):
    list_display = ["idempotency_key", "entity_type", "entity_id", "status", "device", "created_at"]
    list_filter = ["status", "entity_type"]
    ordering = ["-created_at"]
