from django.db import models


class Printer(models.Model):
    class Type(models.TextChoices):
        KITCHEN = "KITCHEN", "Kitchen"
        RECEIPT = "RECEIPT", "Receipt"

    class ConnectionMode(models.TextChoices):
        NETWORK = "NETWORK", "Network (TCP/IP)"
        USB = "USB", "USB"

    branch = models.ForeignKey("tenants.Branch", on_delete=models.CASCADE, related_name="printers")
    name = models.CharField(max_length=120)
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.KITCHEN)
    connection_mode = models.CharField(max_length=20, choices=ConnectionMode.choices, default=ConnectionMode.NETWORK)
    ip = models.GenericIPAddressField(null=True, blank=True)
    port = models.PositiveIntegerField(default=9100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("branch", "name")

    def __str__(self):
        return f"{self.name} ({self.branch.name})"


class PrinterRouteRule(models.Model):
    """Routes a category, item, or course to a specific printer at a branch."""

    branch = models.ForeignKey("tenants.Branch", on_delete=models.CASCADE, related_name="printer_route_rules")
    printer = models.ForeignKey(Printer, on_delete=models.CASCADE, related_name="route_rules")
    category = models.ForeignKey(
        "menu.MenuCategory", on_delete=models.CASCADE, null=True, blank=True, related_name="printer_route_rules"
    )
    menu_item = models.ForeignKey(
        "menu.MenuItem", on_delete=models.CASCADE, null=True, blank=True, related_name="printer_route_rules"
    )
    course = models.CharField(max_length=20, blank=True)
    priority = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-priority", "id"]

    def __str__(self):
        return f"Route → {self.printer.name} (priority {self.priority})"


class PrintJob(models.Model):
    class Status(models.TextChoices):
        QUEUED = "QUEUED", "Queued"
        SENT = "SENT", "Sent"
        ACKED = "ACKED", "Acknowledged"
        FAILED = "FAILED", "Failed"

    class JobType(models.TextChoices):
        KITCHEN_TICKET = "KITCHEN_TICKET", "Kitchen Ticket"
        RECEIPT = "RECEIPT", "Receipt"

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="print_jobs")
    branch = models.ForeignKey("tenants.Branch", on_delete=models.CASCADE, related_name="print_jobs")
    printer = models.ForeignKey(
        Printer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="print_jobs",
    )
    kitchen_ticket = models.ForeignKey(
        "orders.KitchenTicket",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="print_jobs",
    )
    job_type = models.CharField(max_length=30, choices=JobType.choices)
    payload_json = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    attempts = models.PositiveSmallIntegerField(default=0)
    queued_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    acked_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)

    class Meta:
        ordering = ["queued_at"]

    def __str__(self):
        return f"PrintJob #{self.pk} [{self.job_type}] [{self.status}]"
