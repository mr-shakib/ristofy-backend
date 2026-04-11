from django.db import models


class Tenant(models.Model):
    name = models.CharField(max_length=255, unique=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    address = models.TextField(blank=True)
    vat_number = models.CharField(max_length=60, blank=True)
    fiscal_code = models.CharField(max_length=60, blank=True)
    logo_url = models.URLField(blank=True)
    timezone = models.CharField(max_length=60, default="Europe/Rome")
    currency = models.CharField(max_length=10, default="EUR")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Branch(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="branches")
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("tenant", "name")

    def __str__(self):
        return f"{self.tenant.name} - {self.name}"


class SubscriptionPlan(models.Model):
    class Tier(models.TextChoices):
        FREE = "FREE", "Free"
        STARTER = "STARTER", "Starter"
        PRO = "PRO", "Pro"
        ENTERPRISE = "ENTERPRISE", "Enterprise"

    name = models.CharField(max_length=100)
    tier = models.CharField(max_length=20, choices=Tier.choices, unique=True)
    max_branches = models.PositiveSmallIntegerField(default=1)
    max_users = models.PositiveSmallIntegerField(default=5)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    annual_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    features_json = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.tier})"


class TenantSubscription(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        TRIALING = "TRIALING", "Trialing"
        PAST_DUE = "PAST_DUE", "Past Due"
        CANCELED = "CANCELED", "Canceled"

    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name="subscription")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name="subscriptions")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TRIALING)
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    external_subscription_id = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.tenant.name} — {self.plan.tier} ({self.status})"


class FeatureFlag(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="feature_flags")
    key = models.CharField(max_length=100)
    enabled = models.BooleanField(default=False)
    value_json = models.JSONField(default=None, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("tenant", "key")

    def __str__(self):
        return f"{self.tenant.name} — {self.key}: {self.enabled}"
