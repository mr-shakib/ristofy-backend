from django.db import models
from django.db.models import Q


class FloorPlan(models.Model):
    branch = models.ForeignKey("tenants.Branch", on_delete=models.CASCADE, related_name="floor_plans")
    name = models.CharField(max_length=120)
    layout_json = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("branch", "name")

    def __str__(self):
        return f"{self.branch.name} - {self.name}"


class DiningTable(models.Model):
    class State(models.TextChoices):
        FREE = "FREE", "Free"
        OCCUPIED = "OCCUPIED", "Occupied"
        WAITING_BILL = "WAITING_BILL", "Waiting Bill"
        RESERVED = "RESERVED", "Reserved"

    branch = models.ForeignKey("tenants.Branch", on_delete=models.CASCADE, related_name="tables")
    floor_plan = models.ForeignKey(
        FloorPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tables",
    )
    code = models.CharField(max_length=60)
    seats = models.PositiveSmallIntegerField(default=2)
    state = models.CharField(max_length=20, choices=State.choices, default=State.FREE)
    x = models.IntegerField(default=0)
    y = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("branch", "code")

    def __str__(self):
        return f"{self.branch.name} - {self.code}"


class TableSession(models.Model):
    """Tracks a live service session at a table (open → closed)."""

    branch = models.ForeignKey("tenants.Branch", on_delete=models.CASCADE, related_name="table_sessions")
    table = models.ForeignKey(DiningTable, on_delete=models.CASCADE, related_name="sessions")
    opened_by = models.ForeignKey(
        "users.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="opened_sessions"
    )
    covers = models.PositiveSmallIntegerField(default=1)
    seat_map_json = models.JSONField(default=dict, blank=True)
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-opened_at"]

    def __str__(self):
        return f"Session {self.id} — {self.table.code} ({'open' if not self.closed_at else 'closed'})"

    @property
    def is_open(self):
        return self.closed_at is None


class TableMergeSession(models.Model):
    """Tracks a merge of multiple tables into one service session."""

    branch = models.ForeignKey("tenants.Branch", on_delete=models.CASCADE, related_name="table_merge_sessions")
    primary_table = models.ForeignKey(
        DiningTable, on_delete=models.CASCADE, related_name="merge_sessions_as_primary"
    )
    merged_table_ids = models.JSONField(default=list)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    started_by = models.ForeignKey(
        "users.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="started_merges"
    )

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"Merge {self.id} — primary table {self.primary_table.code}"

    @property
    def is_active(self):
        return self.ended_at is None


class Reservation(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        ARRIVED = "ARRIVED", "Arrived"
        CANCELED = "CANCELED", "Canceled"

    branch = models.ForeignKey("tenants.Branch", on_delete=models.CASCADE, related_name="reservations")
    table = models.ForeignKey(
        DiningTable,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reservations",
    )
    customer_name = models.CharField(max_length=160)
    customer_phone = models.CharField(max_length=40, blank=True)
    party_size = models.PositiveSmallIntegerField(default=2)
    reserved_for = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["reserved_for"]
        constraints = [
            models.UniqueConstraint(
                fields=["table", "reserved_for"],
                condition=Q(table__isnull=False) & ~Q(status="CANCELED"),
                name="uniq_active_reservation_per_table_time",
            )
        ]

    def __str__(self):
        return f"{self.customer_name} - {self.reserved_for}"


class WaitlistEntry(models.Model):
    class Status(models.TextChoices):
        WAITING = "WAITING", "Waiting"
        CALLED = "CALLED", "Called"
        SEATED = "SEATED", "Seated"
        CANCELED = "CANCELED", "Canceled"

    branch = models.ForeignKey("tenants.Branch", on_delete=models.CASCADE, related_name="waitlist_entries")
    table = models.ForeignKey(
        DiningTable,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="waitlist_entries",
    )
    customer_name = models.CharField(max_length=160)
    customer_phone = models.CharField(max_length=40, blank=True)
    party_size = models.PositiveSmallIntegerField(default=2)
    quoted_wait_minutes = models.PositiveSmallIntegerField(default=15)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.WAITING)
    notes = models.TextField(blank=True)
    seated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"{self.customer_name} ({self.status})"

