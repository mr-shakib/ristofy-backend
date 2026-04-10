"""
Order domain services — printer routing and kitchen ticket creation.
"""

from django.db import transaction

from printers.models import PrintJob, Printer


def _kitchen_printer_for_branch(branch):
    """Return the first active kitchen printer for a branch, or None."""
    return Printer.objects.filter(branch=branch, type=Printer.Type.KITCHEN, is_active=True).first()


def create_kitchen_ticket_and_print_job(order, course=None):
    """
    Create a KitchenTicket for `order` (optionally scoped to `course`) and
    queue a PrintJob to the branch's kitchen printer if one is configured.

    Returns the created KitchenTicket.
    """
    from .models import KitchenTicket  # local import to avoid circular

    ticket = KitchenTicket.objects.create(
        tenant=order.tenant,
        branch=order.branch,
        order=order,
        course=course,
    )

    printer = _kitchen_printer_for_branch(order.branch)
    PrintJob.objects.create(
        tenant=order.tenant,
        branch=order.branch,
        printer=printer,  # None if no printer configured — job is still queued
        job_type=PrintJob.JobType.KITCHEN_TICKET,
        payload_json={
            "order_id": order.id,
            "order_no": order.order_no,
            "course": course,
            "ticket_id": ticket.id,
        },
    )

    return ticket


def fire_order_items(order, course=None):
    """
    Mark PENDING items (optionally for a specific course) as SENT and
    create the corresponding KitchenTicket + PrintJob.

    Returns list of created KitchenTickets.
    """
    items_qs = order.items.filter(status="PENDING")
    if course:
        items_qs = items_qs.filter(course=course)

    pending_items = list(items_qs.select_related("menu_item"))
    if not pending_items:
        return []

    # Capture distinct courses BEFORE updating item state.
    courses_to_fire = sorted({item.course for item in pending_items}) if not course else [course]

    with transaction.atomic():
        from inventory.services import consume_stock_for_order_items

        consume_stock_for_order_items(order=order, order_items=pending_items, actor_user=order.waiter_user)
        items_qs.update(status="SENT")
        tickets = [create_kitchen_ticket_and_print_job(order, course=c) for c in courses_to_fire]

    return tickets
