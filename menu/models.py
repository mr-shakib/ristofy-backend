from django.db import models


class Allergen(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name_it = models.CharField(max_length=120)
    name_en = models.CharField(max_length=120)
    name_de = models.CharField(max_length=120, blank=True)
    name_fr = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name_en}"


class MenuCategory(models.Model):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="menu_categories")
    branch = models.ForeignKey(
        "tenants.Branch",
        on_delete=models.CASCADE,
        related_name="menu_categories",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=120)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("tenant", "branch", "name")
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="menu_items")
    branch = models.ForeignKey(
        "tenants.Branch",
        on_delete=models.CASCADE,
        related_name="menu_items",
        null=True,
        blank=True,
    )
    category = models.ForeignKey(MenuCategory, on_delete=models.PROTECT, related_name="items")
    allergens = models.ManyToManyField(Allergen, through="MenuItemAllergen", related_name="menu_items", blank=True)
    name = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=22.00)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("tenant", "branch", "category", "name")
        ordering = ["name"]

    def __str__(self):
        return self.name


class MenuItemAllergen(models.Model):
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name="menu_item_allergens")
    allergen = models.ForeignKey(Allergen, on_delete=models.CASCADE, related_name="menu_item_allergens")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("menu_item", "allergen")

    def __str__(self):
        return f"{self.menu_item.name} - {self.allergen.code}"


class MenuVariant(models.Model):
    """Size / option variant for a menu item (e.g. small, medium, large)."""

    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name="variants")
    name = models.CharField(max_length=120)
    price_delta = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("menu_item", "name")
        ordering = ["menu_item_id", "name"]

    def __str__(self):
        return f"{self.menu_item.name} — {self.name}"


class AddonGroup(models.Model):
    """Group of optional add-ons for a menu item (e.g. Toppings, Sauces)."""

    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name="addon_groups")
    name = models.CharField(max_length=120)
    min_select = models.PositiveSmallIntegerField(default=0)
    max_select = models.PositiveSmallIntegerField(default=1)
    required = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("menu_item", "name")
        ordering = ["menu_item_id", "name"]

    def __str__(self):
        return f"{self.menu_item.name} — {self.name}"


class AddonItem(models.Model):
    """A single selectable option within an AddonGroup."""

    addon_group = models.ForeignKey(AddonGroup, on_delete=models.CASCADE, related_name="items")
    name = models.CharField(max_length=120)
    price_delta = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("addon_group", "name")
        ordering = ["addon_group_id", "name"]

    def __str__(self):
        return f"{self.addon_group.name} — {self.name}"


class MenuSchedule(models.Model):
    class Weekday(models.IntegerChoices):
        MONDAY = 1, "Monday"
        TUESDAY = 2, "Tuesday"
        WEDNESDAY = 3, "Wednesday"
        THURSDAY = 4, "Thursday"
        FRIDAY = 5, "Friday"
        SATURDAY = 6, "Saturday"
        SUNDAY = 7, "Sunday"

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="menu_schedules")
    branch = models.ForeignKey(
        "tenants.Branch",
        on_delete=models.CASCADE,
        related_name="menu_schedules",
        null=True,
        blank=True,
    )
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name="schedules")
    day_of_week = models.PositiveSmallIntegerField(choices=Weekday.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["day_of_week", "start_time", "id"]
        unique_together = ("tenant", "branch", "menu_item", "day_of_week", "start_time", "end_time")

    def __str__(self):
        return f"{self.menu_item.name} - {self.day_of_week} {self.start_time}-{self.end_time}"

