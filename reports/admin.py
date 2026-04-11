from django.contrib import admin

from .models import DailyReportSnapshot


@admin.register(DailyReportSnapshot)
class DailyReportSnapshotAdmin(admin.ModelAdmin):
	list_display = (
		"business_date",
		"branch",
		"total_orders",
		"net_sales",
		"vat_total",
		"generated_at",
	)
	list_filter = ("tenant", "branch", "business_date")
	search_fields = ("branch__name",)
