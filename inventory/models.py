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


class StockMovement(models.Model):
	class MovementType(models.TextChoices):
		STOCK_IN = "STOCK_IN", "Stock In"
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
			delta = quantity if movement_type == cls.MovementType.STOCK_IN else -quantity
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
