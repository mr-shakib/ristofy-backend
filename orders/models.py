from django.db import models


class Order(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        SENT_TO_KITCHEN = "SENT_TO_KITCHEN", "Sent to Kitchen"
        PARTIALLY_SERVED = "PARTIALLY_SERVED", "Partially Served"
        COMPLETED = "COMPLETED", "Completed"
        CANCELED = "CANCELED", "Canceled"

    class Channel(models.TextChoices):
        DINE_IN = "DINE_IN", "Dine In"
        TAKEAWAY = "TAKEAWAY", "Takeaway"

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="orders")
    branch = models.ForeignKey("tenants.Branch", on_delete=models.CASCADE, related_name="orders")
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

    def __str__(self):
        return f"Order #{self.pk} [{self.status}] — {self.branch.name}"


class OrderItem(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SENT = "SENT", "Sent"
        SERVED = "SERVED", "Served"
        CANCELED = "CANCELED", "Canceled"

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
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.item_name} x{self.quantity} (Order #{self.order_id})"


class KitchenTicket(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PREPARED = "PREPARED", "Prepared"

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="kitchen_tickets")
    branch = models.ForeignKey("tenants.Branch", on_delete=models.CASCADE, related_name="kitchen_tickets")
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="kitchen_tickets")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Ticket #{self.pk} Order #{self.order_id} [{self.status}]"
