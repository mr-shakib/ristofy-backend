from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from billing.models import Bill
from menu.models import MenuCategory, MenuItem
from orders.models import BuffetPlan, BuffetSession, Order, OrderItem, WasteLog
from tables.models import DiningTable, FloorPlan
from tenants.models import Branch, Tenant

from .models import DailyReportSnapshot

User = get_user_model()


class ReportsPhase9Tests(APITestCase):
	def setUp(self):
		self.tenant = Tenant.objects.create(name="Tenant Reports")
		self.branch = Branch.objects.create(tenant=self.tenant, name="Main")

		self.owner = User.objects.create_user(
			username="owner_reports",
			password="StrongPass123",
			role=User.Role.OWNER,
			tenant=self.tenant,
			branch=self.branch,
		)
		self.waiter = User.objects.create_user(
			username="waiter_reports",
			password="StrongPass123",
			role=User.Role.WAITER,
			tenant=self.tenant,
			branch=self.branch,
		)

		self.other_tenant = Tenant.objects.create(name="Other Reports")
		self.other_branch = Branch.objects.create(tenant=self.other_tenant, name="Other")
		self.other_owner = User.objects.create_user(
			username="owner_reports_other",
			password="StrongPass123",
			role=User.Role.OWNER,
			tenant=self.other_tenant,
			branch=self.other_branch,
		)

		floor = FloorPlan.objects.create(branch=self.branch, name="Main Floor")
		self.table = DiningTable.objects.create(branch=self.branch, floor_plan=floor, code="T1", seats=4)

		category = MenuCategory.objects.create(tenant=self.tenant, branch=self.branch, name="Pasta")
		self.item = MenuItem.objects.create(
			tenant=self.tenant,
			branch=self.branch,
			category=category,
			name="Spaghetti",
			base_price="12.00",
			vat_rate="10.00",
		)

		self.order = Order.objects.create(
			tenant=self.tenant,
			branch=self.branch,
			order_no=1,
			table=self.table,
			waiter_user=self.waiter,
			status=Order.Status.COMPLETED,
		)
		OrderItem.objects.create(
			order=self.order,
			menu_item=self.item,
			item_name=self.item.name,
			unit_price=Decimal("12.00"),
			vat_rate=Decimal("10.00"),
			quantity=2,
			course=OrderItem.Course.MAIN,
			status=OrderItem.Status.SERVED,
		)

		self.bill = Bill.create_from_order(self.order)
		self.bill.finalize()

		plan = BuffetPlan.objects.create(
			branch=self.branch,
			name="Lunch Buffet",
			base_price="20.00",
			kids_price="10.00",
			waste_penalty_amount="2.00",
		)
		self.session = BuffetSession.objects.create(
			tenant=self.tenant,
			branch=self.branch,
			order=self.order,
			buffet_plan=plan,
			adults_count=2,
			kids_count=1,
			started_at=timezone.now(),
			ends_at=timezone.now() + timedelta(minutes=90),
			status=BuffetSession.Status.ACTIVE,
		)
		WasteLog.objects.create(
			tenant=self.tenant,
			branch=self.branch,
			order_item=self.order.items.first(),
			quantity_wasted=1,
			penalty_applied=Decimal("2.00"),
			marked_by=self.owner,
		)

	def _auth(self, user):
		access = str(RefreshToken.for_user(user).access_token)
		self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

	def test_waiter_cannot_access_reports(self):
		self._auth(self.waiter)
		res = self.client.get("/api/v1/reports/sales/by-category")
		self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

	def test_snapshot_refresh_and_list(self):
		self._auth(self.owner)
		refresh = self.client.post("/api/v1/reports/snapshots/refresh", {"business_date": str(timezone.localdate())}, format="json")
		self.assertEqual(refresh.status_code, status.HTTP_200_OK)
		self.assertEqual(len(refresh.data["snapshots"]), 1)

		listed = self.client.get("/api/v1/reports/snapshots")
		self.assertEqual(listed.status_code, status.HTTP_200_OK)
		self.assertEqual(listed.data["count"], 1)

	def test_snapshot_tenant_isolation(self):
		DailyReportSnapshot.objects.create(
			tenant=self.tenant,
			branch=self.branch,
			business_date=timezone.localdate(),
			total_orders=1,
		)

		self._auth(self.other_owner)
		listed = self.client.get("/api/v1/reports/snapshots")
		self.assertEqual(listed.status_code, status.HTTP_200_OK)
		self.assertEqual(listed.data["count"], 0)

	def test_sales_breakdowns_and_cache(self):
		self._auth(self.owner)

		by_category = self.client.get("/api/v1/reports/sales/by-category")
		self.assertEqual(by_category.status_code, status.HTTP_200_OK)
		self.assertFalse(by_category.data["cached"])
		self.assertEqual(by_category.data["data"][0]["category_name"], "Pasta")

		by_category_cached = self.client.get("/api/v1/reports/sales/by-category")
		self.assertEqual(by_category_cached.status_code, status.HTTP_200_OK)
		self.assertTrue(by_category_cached.data["cached"])

		by_table = self.client.get("/api/v1/reports/sales/by-table")
		self.assertEqual(by_table.status_code, status.HTTP_200_OK)
		self.assertEqual(by_table.data["data"][0]["table_code"], "T1")

		by_waiter = self.client.get("/api/v1/reports/sales/by-waiter")
		self.assertEqual(by_waiter.status_code, status.HTTP_200_OK)
		self.assertEqual(by_waiter.data["data"][0]["waiter_username"], "waiter_reports")

		by_vat = self.client.get("/api/v1/reports/sales/by-vat")
		self.assertEqual(by_vat.status_code, status.HTTP_200_OK)
		self.assertEqual(by_vat.data["data"][0]["vat_rate"], "10.00")

	def test_buffet_comparison_and_cache_invalidate(self):
		self._auth(self.owner)
		comparison = self.client.get("/api/v1/reports/buffet/branch-comparison")
		self.assertEqual(comparison.status_code, status.HTTP_200_OK)
		self.assertEqual(comparison.data["data"][0]["branch_name"], "Main")

		invalidate = self.client.post("/api/v1/reports/cache/invalidate", {}, format="json")
		self.assertEqual(invalidate.status_code, status.HTTP_200_OK)
		self.assertGreaterEqual(invalidate.data["cache_keys_invalidated"], 1)
