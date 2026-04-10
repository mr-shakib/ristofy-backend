from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from tenants.models import Branch, Tenant

from .models import Ingredient, StockMovement

User = get_user_model()


class InventoryApiTests(APITestCase):
	def setUp(self):
		self.tenant = Tenant.objects.create(name="Tenant Inventory")
		self.branch = Branch.objects.create(tenant=self.tenant, name="Main")
		self.owner = User.objects.create_user(
			username="owner_inventory",
			password="StrongPass123",
			role=User.Role.OWNER,
			tenant=self.tenant,
			branch=self.branch,
		)
		self.manager = User.objects.create_user(
			username="manager_inventory",
			password="StrongPass123",
			role=User.Role.MANAGER,
			tenant=self.tenant,
			branch=self.branch,
		)
		self.waiter = User.objects.create_user(
			username="waiter_inventory",
			password="StrongPass123",
			role=User.Role.WAITER,
			tenant=self.tenant,
			branch=self.branch,
		)

		self.other_tenant = Tenant.objects.create(name="Other Tenant Inventory")
		self.other_branch = Branch.objects.create(tenant=self.other_tenant, name="Other")
		self.other_owner = User.objects.create_user(
			username="owner_inventory_other",
			password="StrongPass123",
			role=User.Role.OWNER,
			tenant=self.other_tenant,
			branch=self.other_branch,
		)

	def _auth(self, user=None):
		user = user or self.owner
		access = str(RefreshToken.for_user(user).access_token)
		self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

	def test_create_ingredient(self):
		self._auth(self.owner)
		res = self.client.post(
			"/api/v1/inventory/ingredients",
			{
				"branch": self.branch.id,
				"name": "Flour",
				"sku": "FLR-001",
				"unit": "KG",
				"current_stock": "10.000",
				"min_stock_level": "3.000",
			},
			format="json",
		)

		self.assertEqual(res.status_code, status.HTTP_201_CREATED)
		self.assertEqual(res.data["name"], "Flour")
		self.assertEqual(res.data["tenant"], self.tenant.id)

	def test_create_ingredient_rejects_other_tenant_branch(self):
		self._auth(self.owner)
		res = self.client.post(
			"/api/v1/inventory/ingredients",
			{
				"branch": self.other_branch.id,
				"name": "Sugar",
				"unit": "KG",
				"current_stock": "2.000",
				"min_stock_level": "1.000",
			},
			format="json",
		)
		self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

	def test_waiter_forbidden_on_inventory_write(self):
		self._auth(self.waiter)
		res = self.client.post(
			"/api/v1/inventory/ingredients",
			{
				"branch": self.branch.id,
				"name": "Butter",
				"unit": "KG",
				"current_stock": "1.000",
				"min_stock_level": "0.500",
			},
			format="json",
		)
		self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

	def test_tenant_isolation_on_ingredient_detail(self):
		ingredient = Ingredient.objects.create(
			tenant=self.tenant,
			branch=self.branch,
			name="Tomato",
			unit=Ingredient.Unit.KG,
			current_stock="12.000",
			min_stock_level="2.000",
		)
		self._auth(self.other_owner)
		res = self.client.get(f"/api/v1/inventory/ingredients/{ingredient.id}")
		self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

	def test_record_stock_in_movement(self):
		ingredient = Ingredient.objects.create(
			tenant=self.tenant,
			branch=self.branch,
			name="Olive Oil",
			unit=Ingredient.Unit.L,
			current_stock="5.000",
			min_stock_level="2.000",
		)
		self._auth(self.manager)

		res = self.client.post(
			"/api/v1/inventory/movements",
			{
				"ingredient": ingredient.id,
				"movement_type": "STOCK_IN",
				"quantity": "3.000",
				"reason": "Supplier delivery",
			},
			format="json",
		)

		self.assertEqual(res.status_code, status.HTTP_201_CREATED)
		ingredient.refresh_from_db()
		self.assertEqual(ingredient.current_stock, Decimal("8.000"))
		self.assertEqual(res.data["stock_before"], "5.000")
		self.assertEqual(res.data["stock_after"], "8.000")

	def test_record_stock_out_cannot_go_negative(self):
		ingredient = Ingredient.objects.create(
			tenant=self.tenant,
			branch=self.branch,
			name="Cheese",
			unit=Ingredient.Unit.KG,
			current_stock="1.000",
			min_stock_level="0.500",
		)
		self._auth(self.owner)

		res = self.client.post(
			"/api/v1/inventory/movements",
			{
				"ingredient": ingredient.id,
				"movement_type": "STOCK_OUT",
				"quantity": "2.000",
				"reason": "Kitchen usage",
			},
			format="json",
		)

		self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
		ingredient.refresh_from_db()
		self.assertEqual(ingredient.current_stock, Decimal("1.000"))
		self.assertEqual(StockMovement.objects.count(), 0)

	def test_movement_tenant_isolation(self):
		ingredient = Ingredient.objects.create(
			tenant=self.tenant,
			branch=self.branch,
			name="Basil",
			unit=Ingredient.Unit.PCS,
			current_stock="20.000",
			min_stock_level="5.000",
		)
		self._auth(self.other_owner)

		res = self.client.post(
			"/api/v1/inventory/movements",
			{
				"ingredient": ingredient.id,
				"movement_type": "STOCK_OUT",
				"quantity": "1.000",
			},
			format="json",
		)
		self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

	def test_low_stock_report(self):
		Ingredient.objects.create(
			tenant=self.tenant,
			branch=self.branch,
			name="Salt",
			unit=Ingredient.Unit.KG,
			current_stock="1.000",
			min_stock_level="1.500",
		)
		Ingredient.objects.create(
			tenant=self.tenant,
			branch=self.branch,
			name="Pepper",
			unit=Ingredient.Unit.KG,
			current_stock="3.000",
			min_stock_level="1.500",
		)
		Ingredient.objects.create(
			tenant=self.other_tenant,
			branch=self.other_branch,
			name="Other Ingredient",
			unit=Ingredient.Unit.KG,
			current_stock="0.200",
			min_stock_level="1.000",
		)

		self._auth(self.owner)
		res = self.client.get("/api/v1/inventory/reports/low-stock")

		self.assertEqual(res.status_code, status.HTTP_200_OK)
		self.assertEqual(res.data["count"], 1)
		self.assertEqual(res.data["results"][0]["name"], "Salt")
