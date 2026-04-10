from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from menu.models import MenuCategory, MenuItem
from orders.models import Order
from tenants.models import Branch, Tenant

from .models import Ingredient, RecipeComponent, StockMovement

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


class InventoryPhase7ExtensionTests(APITestCase):
	def setUp(self):
		self.tenant = Tenant.objects.create(name="Tenant Inventory Ext")
		self.branch = Branch.objects.create(tenant=self.tenant, name="Main")
		self.owner = User.objects.create_user(
			username="owner_inventory_ext",
			password="StrongPass123",
			role=User.Role.OWNER,
			tenant=self.tenant,
			branch=self.branch,
		)
		self.other_tenant = Tenant.objects.create(name="Other Tenant Inventory Ext")
		self.other_branch = Branch.objects.create(tenant=self.other_tenant, name="Other")
		self.other_owner = User.objects.create_user(
			username="owner_inventory_ext_other",
			password="StrongPass123",
			role=User.Role.OWNER,
			tenant=self.other_tenant,
			branch=self.other_branch,
		)

		self.category = MenuCategory.objects.create(
			tenant=self.tenant,
			branch=self.branch,
			name="Pizza",
			sort_order=1,
		)
		self.menu_item = MenuItem.objects.create(
			tenant=self.tenant,
			branch=self.branch,
			category=self.category,
			name="Margherita",
			base_price="8.00",
			vat_rate="10.00",
		)
		self.ingredient = Ingredient.objects.create(
			tenant=self.tenant,
			branch=self.branch,
			name="Flour",
			unit=Ingredient.Unit.KG,
			current_stock="20.000",
			min_stock_level="5.000",
		)

	def _auth(self, user=None):
		user = user or self.owner
		access = str(RefreshToken.for_user(user).access_token)
		self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

	def test_create_recipe_component(self):
		self._auth()
		res = self.client.post(
			"/api/v1/inventory/recipes",
			{
				"branch": self.branch.id,
				"menu_item": self.menu_item.id,
				"ingredient": self.ingredient.id,
				"quantity": "0.250",
			},
			format="json",
		)
		self.assertEqual(res.status_code, status.HTTP_201_CREATED)
		self.assertEqual(res.data["quantity"], "0.250")

	def test_recipe_component_tenant_isolation(self):
		other_category = MenuCategory.objects.create(
			tenant=self.other_tenant,
			branch=self.other_branch,
			name="Other",
			sort_order=1,
		)
		other_item = MenuItem.objects.create(
			tenant=self.other_tenant,
			branch=self.other_branch,
			category=other_category,
			name="Other Item",
			base_price="4.00",
			vat_rate="10.00",
		)
		self._auth()
		res = self.client.post(
			"/api/v1/inventory/recipes",
			{
				"branch": self.branch.id,
				"menu_item": other_item.id,
				"ingredient": self.ingredient.id,
				"quantity": "0.500",
			},
			format="json",
		)
		self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

	def test_receive_stock_endpoint(self):
		self._auth()
		res = self.client.post(
			"/api/v1/inventory/receivings",
			{
				"ingredient": self.ingredient.id,
				"quantity": "4.000",
				"supplier_name": "Main Supplier",
				"document_no": "RCV-1001",
				"notes": "Weekly delivery",
			},
			format="json",
		)
		self.assertEqual(res.status_code, status.HTTP_201_CREATED)
		self.assertEqual(res.data["movement_type"], StockMovement.MovementType.RECEIVING)
		self.ingredient.refresh_from_db()
		self.assertEqual(self.ingredient.current_stock, Decimal("24.000"))

	def test_usage_report(self):
		StockMovement.record_movement(
			ingredient=self.ingredient,
			movement_type=StockMovement.MovementType.RECEIVING,
			quantity=Decimal("2.000"),
			created_by=self.owner,
		)
		StockMovement.record_movement(
			ingredient=self.ingredient,
			movement_type=StockMovement.MovementType.STOCK_OUT,
			quantity=Decimal("1.250"),
			created_by=self.owner,
		)

		self._auth()
		res = self.client.get("/api/v1/inventory/reports/usage")
		self.assertEqual(res.status_code, status.HTTP_200_OK)
		self.assertEqual(res.data["count"], 1)
		row = res.data["results"][0]
		self.assertEqual(row["ingredient_name"], "Flour")
		self.assertEqual(row["consumed_quantity"], "1.250")
		self.assertEqual(row["received_quantity"], "2.000")

	def test_usage_report_filters_by_ingredient(self):
		ingredient_b = Ingredient.objects.create(
			tenant=self.tenant,
			branch=self.branch,
			name="Cheese",
			unit=Ingredient.Unit.KG,
			current_stock="5.000",
			min_stock_level="1.000",
		)
		StockMovement.record_movement(
			ingredient=self.ingredient,
			movement_type=StockMovement.MovementType.STOCK_OUT,
			quantity=Decimal("0.500"),
			created_by=self.owner,
		)
		StockMovement.record_movement(
			ingredient=ingredient_b,
			movement_type=StockMovement.MovementType.STOCK_OUT,
			quantity=Decimal("0.700"),
			created_by=self.owner,
		)

		self._auth()
		res = self.client.get(f"/api/v1/inventory/reports/usage?ingredient={ingredient_b.id}")
		self.assertEqual(res.status_code, status.HTTP_200_OK)
		self.assertEqual(res.data["count"], 1)
		self.assertEqual(res.data["results"][0]["ingredient_name"], "Cheese")

	def test_recipe_auto_deduction_on_fire(self):
		RecipeComponent.objects.create(
			tenant=self.tenant,
			branch=self.branch,
			menu_item=self.menu_item,
			ingredient=self.ingredient,
			quantity="2.000",
		)

		self._auth()
		order_create = self.client.post(
			"/api/v1/orders",
			{
				"branch": self.branch.id,
				"channel": "DINE_IN",
				"items": [{"menu_item": self.menu_item.id, "quantity": 3}],
			},
			format="json",
		)
		self.assertEqual(order_create.status_code, status.HTTP_201_CREATED)
		order_id = order_create.data["id"]

		fire = self.client.post(f"/api/v1/orders/{order_id}/fire")
		self.assertEqual(fire.status_code, status.HTTP_200_OK)

		self.ingredient.refresh_from_db()
		self.assertEqual(self.ingredient.current_stock, Decimal("14.000"))
		movement = StockMovement.objects.filter(
			ingredient=self.ingredient,
			movement_type=StockMovement.MovementType.STOCK_OUT,
			reference=f"ORDER:{order_id}",
		).first()
		self.assertIsNotNone(movement)

	def test_fire_rejected_when_stock_insufficient(self):
		RecipeComponent.objects.create(
			tenant=self.tenant,
			branch=self.branch,
			menu_item=self.menu_item,
			ingredient=self.ingredient,
			quantity="4.000",
		)
		self.ingredient.current_stock = Decimal("5.000")
		self.ingredient.save(update_fields=["current_stock", "updated_at"])

		self._auth()
		order_create = self.client.post(
			"/api/v1/orders",
			{
				"branch": self.branch.id,
				"channel": "DINE_IN",
				"items": [{"menu_item": self.menu_item.id, "quantity": 2}],
			},
			format="json",
		)
		order_id = order_create.data["id"]

		fire = self.client.post(f"/api/v1/orders/{order_id}/fire")
		self.assertEqual(fire.status_code, status.HTTP_400_BAD_REQUEST)

		self.ingredient.refresh_from_db()
		self.assertEqual(self.ingredient.current_stock, Decimal("5.000"))
		self.assertEqual(StockMovement.objects.filter(reference=f"ORDER:{order_id}").count(), 0)

		order = Order.objects.get(pk=order_id)
		self.assertEqual(order.status, Order.Status.OPEN)
		self.assertEqual(order.items.filter(status="PENDING").count(), 1)
