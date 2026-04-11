from decimal import Decimal

from django.db import models


class DailyReportSnapshot(models.Model):
	tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="daily_report_snapshots")
	branch = models.ForeignKey("tenants.Branch", on_delete=models.CASCADE, related_name="daily_report_snapshots")
	business_date = models.DateField()

	total_orders = models.PositiveIntegerField(default=0)
	completed_orders = models.PositiveIntegerField(default=0)
	canceled_orders = models.PositiveIntegerField(default=0)
	dine_in_orders = models.PositiveIntegerField(default=0)
	takeaway_orders = models.PositiveIntegerField(default=0)

	gross_sales = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
	net_sales = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
	vat_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
	discount_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
	average_order_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

	buffet_sessions = models.PositiveIntegerField(default=0)
	buffet_guests = models.PositiveIntegerField(default=0)
	waste_penalty_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

	generated_at = models.DateTimeField(auto_now=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-business_date", "branch__name"]
		unique_together = ("tenant", "branch", "business_date")

	def __str__(self):
		return f"Snapshot {self.business_date} - {self.branch.name}"
