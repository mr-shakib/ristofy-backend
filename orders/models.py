from django.db import models, transaction
from django.db.models import Max, Q


class Order(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        HELD = "HELD", "Held"
        SENT_TO_KITCHEN = "SENT_TO_KITCHEN", "Sent to Kitchen"
        PARTIALLY_SERVED = "PARTIALLY_SERVED", "Partially Served"
        COMPLETED = "COMPLETED", "Completed"
        CANCELED = "CANCELED", "Canceled"

    class Channel(models.TextChoices):
        DINE_IN = "DINE_IN", "Dine In"
        TAKEAWAY = "TAKEAWAY", "Takeaway"

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="orders")
    branch = models.ForeignKey("tenants.Branch", on_delete=models.CASCADE, related_name="orders")
    order_no = models.PositiveIntegerField(null=True, blank=True)
    table = models.ForeignKey(
        "tables.DiningTable",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    waiter_user = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.OPEN)
    channel = models.CharField(max_length=20, choices=Channel.choices, default=Channel.DINE_IN)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["branch", "order_no"],
                condition=Q(order_no__isnull=False),
                name="uniq_order_no_per_branch",
            )
        ]

    def __str__(self):
        return f"Order #{self.order_no or self.pk} [{self.status}] — {self.branch.name}"

    @classmethod
    def next_order_no(cls, branch):
        """Return the next sequential order_no for the given branch (safe under concurrent writes)."""
        with transaction.atomic():
            result = cls.objects.select_for_update().filter(branch=branch).aggregate(Max("order_no"))
            current_max = result["order_no__max"] or 0
            return current_max + 1

    @property
    def is_terminal(self):
        return self.status in {self.Status.COMPLETED, self.Status.CANCELED}

    @property
    def can_be_fired(self):
        return self.status in {self.Status.OPEN, self.Status.HELD, self.Status.SENT_TO_KITCHEN}


class OrderItem(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SENT = "SENT", "Sent"
        SERVED = "SERVED", "Served"
        CANCELED = "CANCELED", "Canceled"

    class Course(models.TextChoices):
        STARTER = "STARTER", "Starter"
        MAIN = "MAIN", "Main"
        DESSERT = "DESSERT", "Dessert"
        DRINK = "DRINK", "Drink"
        OTHER = "OTHER", "Other"

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    menu_item = models.ForeignKey(
        "menu.MenuItem",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
    )
    # Snapshot fields — captured at order time so price changes don't affect existing orders
    item_name = models.CharField(max_length=200)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2)
    quantity = models.PositiveSmallIntegerField(default=1)
    course = models.CharField(max_length=20, choices=Course.choices, default=Course.MAIN)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["course", "id"]

    def __str__(self):
        return f"{self.item_name} x{self.quantity} [{self.course}] (Order #{self.order_id})"


class KitchenTicket(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PREPARED = "PREPARED", "Prepared"

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="kitchen_tickets")
    branch = models.ForeignKey("tenants.Branch", on_delete=models.CASCADE, related_name="kitchen_tickets")
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="kitchen_tickets")
    # Nullable: None means whole-order ticket; set means course-specific ticket
    course = models.CharField(max_length=20, choices=OrderItem.Course.choices, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        course_label = f" [{self.course}]" if self.course else ""
        return f"Ticket #{self.pk} Order #{self.order_id}{course_label} [{self.status}]"
