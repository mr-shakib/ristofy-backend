"""
Order domain event publishing.

Stub implementation — publishes structured events to stdout/logs.
Wire to Redis Streams or Pub/Sub when the realtime dispatcher is integrated.

Event envelope matches docs/backend-roadmap.md §9.2:
  event_type, tenant_id, branch_id, aggregate_id, occurred_at, payload
"""

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Events emitted by the orders domain
ORDER_CREATED = "order.created"
ORDER_UPDATED = "order.updated"
ORDER_FIRED = "order.fired"
ORDER_HELD = "order.held"
ORDER_CANCELED = "order.canceled"
ORDER_COMPLETED = "order.completed"
TICKET_PRINT_REQUESTED = "ticket.print.requested"


def publish_order_event(event_type: str, order, **payload) -> None:
    """
    Publish an order domain event.

    Currently logs the event. Replace the body of this function with
    a Redis XADD / PUBLISH call when the realtime dispatcher is ready.
    """
    envelope = {
        "event_type": event_type,
        "tenant_id": order.tenant_id,
        "branch_id": order.branch_id,
        "aggregate_id": order.id,
        "occurred_at": datetime.now(tz=timezone.utc).isoformat(),
        "payload": payload,
    }
    logger.info("order_event published: %s", envelope)
    # TODO: redis_client.xadd(f"orders:{order.tenant_id}", envelope)
