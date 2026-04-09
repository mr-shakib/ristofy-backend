from decimal import Decimal, ROUND_HALF_UP

from django.db import models, transaction
from django.db.models import Max


MONEY_QUANT = Decimal("0.01")
HUNDRED = Decimal("100")


def quantize_money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


class Bill(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        FINALIZED = "FINALIZED", "Finalized"
        PAID = "PAID", "Paid"

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="bills")
    branch = models.ForeignKey("tenants.Branch", on_delete=models.CASCADE, related_name="bills")
    order = models.OneToOneField("orders.Order", on_delete=models.PROTECT, related_name="bill")
    bill_no = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    vat_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    coperto_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    service_charge_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    waste_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    discount_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("branch", "bill_no")

    def __str__(self):
        return f"Bill #{self.bill_no} [{self.status}] — {self.branch.name}"

    @classmethod
    def next_bill_no(cls, branch):
        """Return the next sequential bill number for a branch."""
        with transaction.atomic():
            result = cls.objects.select_for_update().filter(branch=branch).aggregate(Max("bill_no"))
            current_max = result["bill_no__max"] or 0
            return current_max + 1

    def recalculate_totals(self):
        """Recompute totals from current lines and adjustment fields."""
        subtotal = Decimal("0.00")
        vat_total = Decimal("0.00")

        for line in self.lines.all():
            subtotal += line.line_total
            vat_total += quantize_money((line.line_total * line.vat_rate) / HUNDRED)

        subtotal = quantize_money(subtotal)
        vat_total = quantize_money(vat_total)
        grand_total = quantize_money(
            subtotal
            + vat_total
            + self.coperto_total
            + self.service_charge_total
            + self.waste_total
            - self.discount_total
        )

        self.subtotal = subtotal
        self.vat_total = vat_total
        self.grand_total = grand_total

    @classmethod
    def create_from_order(cls, order):
        """Create a bill and ORDER_ITEM lines from a given order."""
        from orders.models import Order, OrderItem

        with transaction.atomic():
            locked_order = (
                Order.objects.select_for_update()
                .select_related("tenant", "branch")
                .prefetch_related("items")
                .get(pk=order.pk)
            )

            if hasattr(locked_order, "bill"):
                raise ValueError("A bill already exists for this order.")

            bill = cls.objects.create(
                tenant=locked_order.tenant,
                branch=locked_order.branch,
                order=locked_order,
                bill_no=cls.next_bill_no(locked_order.branch),
                status=cls.Status.DRAFT,
            )

            lines = []
            for item in locked_order.items.exclude(status=OrderItem.Status.CANCELED):
                line_total = quantize_money(item.unit_price * Decimal(item.quantity))
                lines.append(
                    BillLine(
                        bill=bill,
                        source_type=BillLine.SourceType.ORDER_ITEM,
                        source_id=str(item.id),
                        description=item.item_name,
                        quantity=Decimal(item.quantity),
                        unit_price=item.unit_price,
                        vat_rate=item.vat_rate,
                        line_total=line_total,
                    )
                )

            if lines:
                BillLine.objects.bulk_create(lines)

            bill.recalculate_totals()
            bill.save(update_fields=["subtotal", "vat_total", "grand_total", "updated_at"])

            return bill


class BillLine(models.Model):
    class SourceType(models.TextChoices):
        ORDER_ITEM = "ORDER_ITEM", "Order Item"
        COPERTO = "COPERTO", "Coperto"
        SERVICE = "SERVICE", "Service"
        DISCOUNT = "DISCOUNT", "Discount"
        WASTE = "WASTE", "Waste"

    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name="lines")
    source_type = models.CharField(max_length=20, choices=SourceType.choices)
    source_id = models.CharField(max_length=64, null=True, blank=True)
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    line_total = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.source_type}: {self.description} ({self.line_total})"
