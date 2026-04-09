"""
Order domain services — printer routing and kitchen ticket creation.
"""

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

    if not items_qs.exists():
        return []

    # Capture distinct courses BEFORE updating so the queryset is still valid
    courses_to_fire = list(items_qs.values_list("course", flat=True).distinct()) if not course else [course]
    items_qs.update(status="SENT")

    tickets = [create_kitchen_ticket_and_print_job(order, course=c) for c in courses_to_fire]
    return tickets
