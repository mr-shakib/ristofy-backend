from django.contrib import admin

from .models import PrintJob, Printer, PrinterRouteRule


@admin.register(Printer)
class PrinterAdmin(admin.ModelAdmin):
    list_display = ["name", "type", "connection_mode", "ip", "port", "branch", "is_active"]
    list_filter = ["type", "is_active", "branch__tenant"]
    ordering = ["branch__name", "name"]


@admin.register(PrinterRouteRule)
class PrinterRouteRuleAdmin(admin.ModelAdmin):
    list_display = ["printer", "category", "menu_item", "course", "priority", "branch"]
    list_filter = ["branch__tenant"]
    ordering = ["-priority", "id"]


@admin.register(PrintJob)
class PrintJobAdmin(admin.ModelAdmin):
    list_display = ["id", "job_type", "status", "printer", "branch", "queued_at"]
    list_filter = ["status", "job_type", "branch__tenant"]
    ordering = ["-queued_at"]
