from django.db import models


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

    def __str__(self):
        return f"{self.customer_name} - {self.reserved_for}"

