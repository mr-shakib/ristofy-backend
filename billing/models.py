from decimal import Decimal, ROUND_HALF_UP

from django.db import models, transaction
from django.db.models import Max, Sum
from django.utils import timezone


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
        """Recompute totals from bill lines, grouped by source type."""
        subtotal = Decimal("0.00")
        coperto_total = Decimal("0.00")
        service_charge_total = Decimal("0.00")
        waste_total = Decimal("0.00")
        discount_total = Decimal("0.00")
        vat_total = Decimal("0.00")

        for line in self.lines.all():
            line_total = quantize_money(Decimal(line.line_total))
            if line.source_type == BillLine.SourceType.ORDER_ITEM:
                subtotal += line_total
            elif line.source_type == BillLine.SourceType.COPERTO:
                coperto_total += line_total
            elif line.source_type == BillLine.SourceType.SERVICE:
                service_charge_total += line_total
            elif line.source_type == BillLine.SourceType.WASTE:
                waste_total += line_total
            elif line.source_type == BillLine.SourceType.DISCOUNT:
                discount_total += line_total

            vat_total += quantize_money((line_total * line.vat_rate) / HUNDRED)

        subtotal = quantize_money(subtotal)
        coperto_total = quantize_money(coperto_total)
        service_charge_total = quantize_money(service_charge_total)
        waste_total = quantize_money(waste_total)
        discount_total = quantize_money(discount_total)
        vat_total = quantize_money(vat_total)
        raw_grand_total = quantize_money(
            subtotal
            + vat_total
            + coperto_total
            + service_charge_total
            + waste_total
            - discount_total
        )
        grand_total = max(Decimal("0.00"), raw_grand_total)

        self.subtotal = subtotal
        self.coperto_total = coperto_total
        self.service_charge_total = service_charge_total
        self.waste_total = waste_total
        self.discount_total = discount_total
        self.vat_total = vat_total
        self.grand_total = grand_total

    @property
    def amount_paid(self):
        result = self.payments.aggregate(total=Sum("amount"))
        return quantize_money(result["total"] or Decimal("0.00"))

    @property
    def is_editable(self):
        return self.status == self.Status.DRAFT

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
            bill.save(
                update_fields=[
                    "subtotal",
                    "vat_total",
                    "coperto_total",
                    "service_charge_total",
                    "waste_total",
                    "discount_total",
                    "grand_total",
                    "updated_at",
                ]
            )

            return bill

    def apply_coperto(self, *, amount: Decimal, covers: int):
        """Add a coperto adjustment line while bill is DRAFT."""
        if not self.is_editable:
            raise ValueError("Only draft bills can be modified.")

        if covers < 1:
            raise ValueError("Covers must be at least 1.")

        amount = quantize_money(Decimal(amount))
        if amount <= Decimal("0.00"):
            raise ValueError("Coperto amount must be greater than zero.")

        covers_decimal = Decimal(covers)
        line = BillLine.objects.create(
            bill=self,
            source_type=BillLine.SourceType.COPERTO,
            description=f"Coperto x{covers}",
            quantity=covers_decimal,
            unit_price=amount,
            vat_rate=Decimal("0.00"),
            line_total=quantize_money(amount * covers_decimal),
        )

        self.recalculate_totals()
        self.save(
            update_fields=[
                "subtotal",
                "vat_total",
                "coperto_total",
                "service_charge_total",
                "waste_total",
                "discount_total",
                "grand_total",
                "updated_at",
            ]
        )
        return line

    def apply_discount(self, *, discount_type: str, value: Decimal):
        """Add a discount line while bill is DRAFT."""
        if not self.is_editable:
            raise ValueError("Only draft bills can be modified.")

        discount_type = str(discount_type).upper()
        if discount_type not in {"PERCENT", "FIXED"}:
            raise ValueError("Discount type must be PERCENT or FIXED.")

        value = quantize_money(Decimal(value))
        if value <= Decimal("0.00"):
            raise ValueError("Discount value must be greater than zero.")

        self.recalculate_totals()
        gross_total = quantize_money(
            self.subtotal
            + self.vat_total
            + self.coperto_total
            + self.service_charge_total
            + self.waste_total
        )
        current_payable = quantize_money(gross_total - self.discount_total)
        if current_payable <= Decimal("0.00"):
            raise ValueError("Bill already has no payable amount.")

        if discount_type == "PERCENT":
            discount_amount = quantize_money((current_payable * value) / HUNDRED)
            description = f"Discount {value}%"
        else:
            discount_amount = value
            description = "Discount fixed"

        discount_amount = min(discount_amount, current_payable)
        if discount_amount <= Decimal("0.00"):
            raise ValueError("Discount amount must be greater than zero.")

        line = BillLine.objects.create(
            bill=self,
            source_type=BillLine.SourceType.DISCOUNT,
            description=description,
            quantity=Decimal("1.00"),
            unit_price=discount_amount,
            vat_rate=Decimal("0.00"),
            line_total=discount_amount,
        )

        self.recalculate_totals()
        self.save(
            update_fields=[
                "subtotal",
                "vat_total",
                "coperto_total",
                "service_charge_total",
                "waste_total",
                "discount_total",
                "grand_total",
                "updated_at",
            ]
        )
        return line

    def finalize(self):
        if self.status != self.Status.DRAFT:
            raise ValueError("Only draft bills can be finalized.")
        self.status = self.Status.FINALIZED
        self.save(update_fields=["status", "updated_at"])

    def record_payment(self, *, method: str, amount: Decimal, reference: str = ""):
        if self.status == self.Status.DRAFT:
            raise ValueError("Bill must be finalized before recording payment.")
        if self.status == self.Status.PAID:
            raise ValueError("Bill is already fully paid.")

        amount = quantize_money(Decimal(amount))
        if amount <= Decimal("0.00"):
            raise ValueError("Payment amount must be greater than zero.")

        payment = Payment.objects.create(
            bill=self,
            method=method,
            amount=amount,
            reference=reference,
        )

        if self.amount_paid >= self.grand_total:
            self.status = self.Status.PAID
            self.save(update_fields=["status", "updated_at"])

        return payment


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


class Payment(models.Model):
    class Method(models.TextChoices):
        CASH = "CASH", "Cash"
        CARD = "CARD", "Card"
        OTHER = "OTHER", "Other"

    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name="payments")
    method = models.CharField(max_length=20, choices=Method.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reference = models.CharField(max_length=255, blank=True)
    paid_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["paid_at", "id"]

    def __str__(self):
        return f"Payment {self.method} {self.amount} (Bill #{self.bill_id})"
