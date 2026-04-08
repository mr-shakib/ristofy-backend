from .models import DiningTable, Reservation


def recalculate_table_state(table):
    active = Reservation.objects.filter(table=table).exclude(status=Reservation.Status.CANCELED)

    if active.filter(status=Reservation.Status.ARRIVED).exists():
        next_state = DiningTable.State.OCCUPIED
    elif active.filter(status=Reservation.Status.CONFIRMED).exists():
        next_state = DiningTable.State.RESERVED
    else:
        next_state = DiningTable.State.FREE

    if table.state != next_state:
        table.state = next_state
        table.save(update_fields=["state", "updated_at"])


def sync_table_state_for_reservation(reservation):
    if reservation.table_id:
        recalculate_table_state(reservation.table)


def sync_table_state_for_table(table):
    if table:
        recalculate_table_state(table)
