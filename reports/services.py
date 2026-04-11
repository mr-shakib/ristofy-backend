from decimal import Decimal

from django.db.models import F, Sum

from billing.models import Bill
from orders.models import BuffetSession, Order, WasteLog

from .models import DailyReportSnapshot


def _money(value):
    return (value or Decimal("0.00")).quantize(Decimal("0.01"))


def compute_daily_snapshot(*, tenant, branch, business_date):
    order_qs = Order.objects.filter(tenant=tenant, branch=branch, created_at__date=business_date)

    total_orders = order_qs.count()
    completed_orders = order_qs.filter(status=Order.Status.COMPLETED).count()
    canceled_orders = order_qs.filter(status=Order.Status.CANCELED).count()
    dine_in_orders = order_qs.filter(channel=Order.Channel.DINE_IN).count()
    takeaway_orders = order_qs.filter(channel=Order.Channel.TAKEAWAY).count()

    bill_qs = Bill.objects.filter(
        tenant=tenant,
        branch=branch,
        created_at__date=business_date,
    ).exclude(status=Bill.Status.DRAFT)

    gross_parts = bill_qs.aggregate(
        subtotal=Sum("subtotal"),
        vat=Sum("vat_total"),
        coperto=Sum("coperto_total"),
        service=Sum("service_charge_total"),
        waste=Sum("waste_total"),
    )
    gross_sales = _money(
        (gross_parts["subtotal"] or Decimal("0.00"))
        + (gross_parts["vat"] or Decimal("0.00"))
        + (gross_parts["coperto"] or Decimal("0.00"))
        + (gross_parts["service"] or Decimal("0.00"))
        + (gross_parts["waste"] or Decimal("0.00"))
    )
    net_sales = _money(bill_qs.aggregate(total=Sum("grand_total"))["total"])
    vat_total = _money(bill_qs.aggregate(total=Sum("vat_total"))["total"])
    discount_total = _money(bill_qs.aggregate(total=Sum("discount_total"))["total"])

    billed_orders = bill_qs.count()
    average_order_value = _money(net_sales / billed_orders) if billed_orders > 0 else Decimal("0.00")

    buffet_qs = BuffetSession.objects.filter(
        tenant=tenant,
        branch=branch,
        started_at__date=business_date,
    )
    buffet_sessions = buffet_qs.count()
    buffet_guests = buffet_qs.aggregate(total=Sum(F("adults_count") + F("kids_count")))["total"] or 0

    waste_penalty_total = _money(
        WasteLog.objects.filter(
            tenant=tenant,
            branch=branch,
            created_at__date=business_date,
        ).aggregate(total=Sum("penalty_applied"))["total"]
    )

    snapshot, _ = DailyReportSnapshot.objects.update_or_create(
        tenant=tenant,
        branch=branch,
        business_date=business_date,
        defaults={
            "total_orders": total_orders,
            "completed_orders": completed_orders,
            "canceled_orders": canceled_orders,
            "dine_in_orders": dine_in_orders,
            "takeaway_orders": takeaway_orders,
            "gross_sales": gross_sales,
            "net_sales": net_sales,
            "vat_total": vat_total,
            "discount_total": discount_total,
            "average_order_value": average_order_value,
            "buffet_sessions": buffet_sessions,
            "buffet_guests": buffet_guests,
            "waste_penalty_total": waste_penalty_total,
        },
    )
    return snapshot
