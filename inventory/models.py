from decimal import Decimal

from django.db import models, transaction


class Ingredient(models.Model):
	class Unit(models.TextChoices):
		KG = "KG", "Kilogram"
		G = "G", "Gram"
		L = "L", "Liter"
		ML = "ML", "Milliliter"
		PCS = "PCS", "Pieces"

	tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="ingredients")
	branch = models.ForeignKey("tenants.Branch", on_delete=models.CASCADE, related_name="ingredients")
	name = models.CharField(max_length=160)
	sku = models.CharField(max_length=64, blank=True)
	unit = models.CharField(max_length=8, choices=Unit.choices, default=Unit.PCS)
	current_stock = models.DecimalField(max_digits=12, decimal_places=3, default=0)
	min_stock_level = models.DecimalField(max_digits=12, decimal_places=3, default=0)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["name", "id"]
		constraints = [
			models.UniqueConstraint(fields=["tenant", "branch", "name"], name="uniq_ingredient_name_per_branch"),
		]

	def __str__(self):
		return f"{self.name} ({self.branch.name})"


class RecipeComponent(models.Model):
	tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="recipe_components")
	branch = models.ForeignKey("tenants.Branch", on_delete=models.CASCADE, related_name="recipe_components")
	menu_item = models.ForeignKey("menu.MenuItem", on_delete=models.CASCADE, related_name="recipe_components")
	ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name="recipe_components")
	quantity = models.DecimalField(max_digits=12, decimal_places=3)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["menu_item_id", "ingredient_id"]
		constraints = [
			models.UniqueConstraint(
				fields=["tenant", "branch", "menu_item", "ingredient"],
				name="uniq_recipe_component_per_menu_item_ingredient",
			),
		]

	def __str__(self):
		return f"{self.menu_item.name} -> {self.ingredient.name} ({self.quantity})"


class StockMovement(models.Model):
	class MovementType(models.TextChoices):
		STOCK_IN = "STOCK_IN", "Stock In"
		RECEIVING = "RECEIVING", "Receiving"
		STOCK_OUT = "STOCK_OUT", "Stock Out"

	tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="stock_movements")
	branch = models.ForeignKey("tenants.Branch", on_delete=models.CASCADE, related_name="stock_movements")
	ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name="movements")
	movement_type = models.CharField(max_length=20, choices=MovementType.choices)
	quantity = models.DecimalField(max_digits=12, decimal_places=3)
	stock_before = models.DecimalField(max_digits=12, decimal_places=3)
	stock_after = models.DecimalField(max_digits=12, decimal_places=3)
	reason = models.TextField(blank=True)
	reference = models.CharField(max_length=120, blank=True)
	created_by = models.ForeignKey(
		"users.User",
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="stock_movements",
	)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at", "-id"]

	def __str__(self):
		return f"{self.movement_type} {self.quantity} ({self.ingredient.name})"

	@classmethod
	def record_movement(
		cls,
		*,
		ingredient,
		movement_type,
		quantity,
		created_by=None,
		reason="",
		reference="",
	):
		if quantity <= Decimal("0"):
			raise ValueError("Quantity must be greater than zero.")

		with transaction.atomic():
			ingredient_locked = (
				Ingredient.objects.select_for_update()
				.select_related("tenant", "branch")
				.get(pk=ingredient.pk)
			)

			stock_before = ingredient_locked.current_stock
			is_inbound = movement_type in {cls.MovementType.STOCK_IN, cls.MovementType.RECEIVING}
			delta = quantity if is_inbound else -quantity
			stock_after = stock_before + delta

			if stock_after < Decimal("0"):
				raise ValueError("Stock cannot go below zero.")

			movement = cls.objects.create(
				tenant=ingredient_locked.tenant,
				branch=ingredient_locked.branch,
				ingredient=ingredient_locked,
				movement_type=movement_type,
				quantity=quantity,
				stock_before=stock_before,
				stock_after=stock_after,
				reason=reason,
				reference=reference,
				created_by=created_by,
			)

			ingredient_locked.current_stock = stock_after
			ingredient_locked.save(update_fields=["current_stock", "updated_at"])

			return movement


class Supplier(models.Model):
	tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="suppliers")
	branch = models.ForeignKey("tenants.Branch", on_delete=models.CASCADE, related_name="suppliers")
	name = models.CharField(max_length=160)
	contact_name = models.CharField(max_length=120, blank=True)
	phone = models.CharField(max_length=40, blank=True)
	email = models.EmailField(blank=True)
	address = models.TextField(blank=True)
	notes = models.TextField(blank=True)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["name"]
		unique_together = ("tenant", "branch", "name")

	def __str__(self):
		return f"{self.name} ({self.branch.name})"


class PurchaseOrder(models.Model):
	class Status(models.TextChoices):
		DRAFT = "DRAFT", "Draft"
		SENT = "SENT", "Sent"
		PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED", "Partially Received"
		RECEIVED = "RECEIVED", "Received"
		CANCELED = "CANCELED", "Canceled"

	tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="purchase_orders")
	branch = models.ForeignKey("tenants.Branch", on_delete=models.CASCADE, related_name="purchase_orders")
	supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name="purchase_orders")
	po_number = models.CharField(max_length=60, blank=True)
	status = models.CharField(max_length=25, choices=Status.choices, default=Status.DRAFT)
	expected_at = models.DateField(null=True, blank=True)
	notes = models.TextField(blank=True)
	created_by = models.ForeignKey(
		"users.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="purchase_orders"
	)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self):
		return f"PO #{self.po_number or self.id} [{self.status}] — {self.branch.name}"


class PurchaseOrderItem(models.Model):
	purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="items")
	ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name="purchase_order_items")
	quantity_ordered = models.DecimalField(max_digits=12, decimal_places=3)
	quantity_received = models.DecimalField(max_digits=12, decimal_places=3, default=0)
	unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["id"]

	def __str__(self):
		return f"{self.ingredient.name} x{self.quantity_ordered} (PO #{self.purchase_order_id})"
