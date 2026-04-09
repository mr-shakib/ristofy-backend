from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from menu.models import MenuCategory, MenuItem
from tenants.models import Branch, Tenant

from .models import BuffetPlan, BuffetSession, Order

User = get_user_model()


class BuffetTestBase(APITestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tenant Buffet")
        self.branch = Branch.objects.create(tenant=self.tenant, name="Main")
        self.owner = User.objects.create_user(
            username="owner_buffet",
            password="StrongPass123",
            role=User.Role.OWNER,
            tenant=self.tenant,
            branch=self.branch,
        )
        self.waiter = User.objects.create_user(
            username="waiter_buffet",
            password="StrongPass123",
            role=User.Role.WAITER,
            tenant=self.tenant,
            branch=self.branch,
        )
        self.plan = BuffetPlan.objects.create(
            branch=self.branch,
            name="Sunday Buffet",
            base_price="25.00",
            kids_price="12.00",
            time_limit_minutes=90,
            waste_penalty_amount="5.00",
            round_limit_per_person=3,
            round_delay_seconds=0,
        )
        # Second tenant for isolation
        self.other_tenant = Tenant.objects.create(name="Other Buffet Tenant")
        self.other_branch = Branch.objects.create(tenant=self.other_tenant, name="Other")
        self.other_user = User.objects.create_user(
            username="owner_buffet_other",
            password="StrongPass123",
            role=User.Role.OWNER,
            tenant=self.other_tenant,
            branch=self.other_branch,
        )

    def _auth(self, user=None):
        user = user or self.owner
        access = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    def _start_session(self, adults=2, kids=1, extra=None):
        payload = {
            "branch": self.branch.id,
            "buffet_plan": self.plan.id,
            "adults_count": adults,
            "kids_count": kids,
        }
        if extra:
            payload.update(extra)
        return self.client.post("/api/v1/buffet/sessions/start", payload, format="json")


class BuffetPlanTests(BuffetTestBase):

    def test_create_buffet_plan(self):
        self._auth()
        res = self.client.post("/api/v1/buffet/plans", {
            "branch": self.branch.id,
            "name": "Weekday Lunch",
            "base_price": "18.00",
            "kids_price": "9.00",
            "time_limit_minutes": 60,
            "waste_penalty_amount": "3.00",
            "round_limit_per_person": 2,
            "round_delay_seconds": 300,
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["name"], "Weekday Lunch")

    def test_list_buffet_plans(self):
        self._auth()
        res = self.client.get("/api/v1/buffet/plans")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 1)

    def test_filter_plans_by_branch(self):
        self._auth()
        res = self.client.get(f"/api/v1/buffet/plans?branch={self.branch.id}")
        self.assertEqual(res.data["count"], 1)

    def test_update_buffet_plan(self):
        self._auth()
        res = self.client.patch(f"/api/v1/buffet/plans/{self.plan.id}", {"name": "Updated Buffet"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["name"], "Updated Buffet")

    def test_plan_from_other_tenant_branch_rejected(self):
        self._auth()
        res = self.client.post("/api/v1/buffet/plans", {
            "branch": self.other_branch.id,
            "name": "Hack",
            "base_price": "10.00",
            "kids_price": "5.00",
            "time_limit_minutes": 60,
            "waste_penalty_amount": "0.00",
            "round_limit_per_person": 0,
            "round_delay_seconds": 0,
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_active_to_before_active_from_rejected(self):
        self._auth()
        res = self.client.post("/api/v1/buffet/plans", {
            "branch": self.branch.id,
            "name": "Bad Dates",
            "base_price": "10.00",
            "kids_price": "5.00",
            "time_limit_minutes": 60,
            "waste_penalty_amount": "0.00",
            "round_limit_per_person": 0,
            "round_delay_seconds": 0,
            "active_from": "2026-06-01",
            "active_to": "2026-05-01",
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_rejected(self):
        self.client.credentials()
        res = self.client.get("/api/v1/buffet/plans")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class BuffetSessionTests(BuffetTestBase):

    def test_start_session(self):
        self._auth()
        res = self._start_session()
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["status"], "ACTIVE")
        self.assertEqual(res.data["adults_count"], 2)
        self.assertEqual(res.data["kids_count"], 1)
        self.assertIsNotNone(res.data["ends_at"])

    def test_ends_at_computed_from_plan(self):
        self._auth()
        res = self._start_session()
        # ends_at should be ~90 minutes after started_at
        from django.utils.dateparse import parse_datetime
        started = parse_datetime(res.data["started_at"])
        ended = parse_datetime(res.data["ends_at"])
        diff_minutes = (ended - started).total_seconds() / 60
        self.assertAlmostEqual(diff_minutes, 90, delta=1)

    def test_get_session_detail(self):
        self._auth()
        res = self._start_session()
        session_id = res.data["id"]
        detail = self.client.get(f"/api/v1/buffet/sessions/{session_id}")
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(detail.data["id"], session_id)

    def test_end_session(self):
        self._auth()
        res = self._start_session()
        session_id = res.data["id"]
        end_res = self.client.post(f"/api/v1/buffet/sessions/{session_id}/end")
        self.assertEqual(end_res.status_code, status.HTTP_200_OK)
        self.assertEqual(end_res.data["status"], "ENDED")

    def test_end_already_ended_session_rejected(self):
        self._auth()
        res = self._start_session()
        session_id = res.data["id"]
        self.client.post(f"/api/v1/buffet/sessions/{session_id}/end")
        res2 = self.client.post(f"/api/v1/buffet/sessions/{session_id}/end")
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_waiter_can_start_session(self):
        self._auth(self.waiter)
        res = self._start_session()
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_waiter_cannot_end_session(self):
        self._auth()
        res = self._start_session()
        session_id = res.data["id"]
        self._auth(self.waiter)
        res2 = self.client.post(f"/api/v1/buffet/sessions/{session_id}/end")
        self.assertEqual(res2.status_code, status.HTTP_403_FORBIDDEN)

    def test_session_plan_must_belong_to_branch(self):
        self._auth()
        other_plan = BuffetPlan.objects.create(
            branch=self.other_branch, name="Other Plan",
            base_price="20.00", kids_price="10.00",
            time_limit_minutes=60, waste_penalty_amount="0.00",
        )
        res = self._start_session(extra={"buffet_plan": other_plan.id})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_tenant_isolation_session_detail(self):
        self._auth()
        res = self._start_session()
        session_id = res.data["id"]
        self._auth(self.other_user)
        detail = self.client.get(f"/api/v1/buffet/sessions/{session_id}")
        self.assertEqual(detail.status_code, status.HTTP_404_NOT_FOUND)


class BuffetRoundTests(BuffetTestBase):

    def setUp(self):
        super().setUp()
        self._auth()
        res = self._start_session()
        self.session_id = res.data["id"]

    def test_open_new_round(self):
        res = self.client.post(f"/api/v1/buffet/sessions/{self.session_id}/new-round")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["round_number"], 1)
        self.assertIsNone(res.data["closed_at"])
        self.assertTrue(res.data["is_open"])

    def test_cannot_open_round_while_one_is_open(self):
        self.client.post(f"/api/v1/buffet/sessions/{self.session_id}/new-round")
        res = self.client.post(f"/api/v1/buffet/sessions/{self.session_id}/new-round")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_close_round(self):
        self.client.post(f"/api/v1/buffet/sessions/{self.session_id}/new-round")
        res = self.client.post(f"/api/v1/buffet/sessions/{self.session_id}/close-round")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(res.data["closed_at"])
        self.assertFalse(res.data["is_open"])

    def test_close_round_with_no_open_round_rejected(self):
        res = self.client.post(f"/api/v1/buffet/sessions/{self.session_id}/close-round")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_round_numbers_increment(self):
        self.client.post(f"/api/v1/buffet/sessions/{self.session_id}/new-round")
        self.client.post(f"/api/v1/buffet/sessions/{self.session_id}/close-round")
        res = self.client.post(f"/api/v1/buffet/sessions/{self.session_id}/new-round")
        self.assertEqual(res.data["round_number"], 2)

    def test_round_limit_enforced(self):
        # plan has round_limit_per_person=3; open+close 3 rounds then reject 4th
        for _ in range(3):
            self.client.post(f"/api/v1/buffet/sessions/{self.session_id}/new-round")
            self.client.post(f"/api/v1/buffet/sessions/{self.session_id}/close-round")
        res = self.client.post(f"/api/v1/buffet/sessions/{self.session_id}/new-round")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("limit", res.data["detail"].lower())

    def test_round_delay_enforced(self):
        # Create a plan with a 60-second delay
        delay_plan = BuffetPlan.objects.create(
            branch=self.branch, name="Delay Plan",
            base_price="20.00", kids_price="10.00",
            time_limit_minutes=90, waste_penalty_amount="0.00",
            round_limit_per_person=0, round_delay_seconds=60,
        )
        session_res = self.client.post("/api/v1/buffet/sessions/start", {
            "branch": self.branch.id,
            "buffet_plan": delay_plan.id,
            "adults_count": 2,
            "kids_count": 0,
        }, format="json")
        sid = session_res.data["id"]
        self.client.post(f"/api/v1/buffet/sessions/{sid}/new-round")
        self.client.post(f"/api/v1/buffet/sessions/{sid}/close-round")
        # Immediately try another round — delay not elapsed
        res = self.client.post(f"/api/v1/buffet/sessions/{sid}/new-round")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("wait", res.data["detail"].lower())

    def test_cannot_open_round_on_ended_session(self):
        self.client.post(f"/api/v1/buffet/sessions/{self.session_id}/end")
        res = self.client.post(f"/api/v1/buffet/sessions/{self.session_id}/new-round")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_end_session_auto_closes_open_round(self):
        self.client.post(f"/api/v1/buffet/sessions/{self.session_id}/new-round")
        end_res = self.client.post(f"/api/v1/buffet/sessions/{self.session_id}/end")
        self.assertEqual(end_res.status_code, status.HTTP_200_OK)
        # Round should now be closed
        detail = self.client.get(f"/api/v1/buffet/sessions/{self.session_id}")
        rounds = detail.data["rounds"]
        self.assertEqual(len(rounds), 1)
        self.assertFalse(rounds[0]["is_open"])


class WasteLogTests(BuffetTestBase):

    def setUp(self):
        super().setUp()
        self._auth()
        self.category = MenuCategory.objects.create(
            tenant=self.tenant, branch=self.branch, name="Mains", sort_order=1
        )
        self.menu_item = MenuItem.objects.create(
            tenant=self.tenant, branch=self.branch, category=self.category,
            name="Pizza", base_price="12.00", vat_rate="10.00",
        )
        # Create an order and a buffet session linked to it
        order_res = self.client.post("/api/v1/orders", {
            "branch": self.branch.id,
            "channel": "DINE_IN",
            "items": [{"menu_item": self.menu_item.id, "quantity": 3}],
        }, format="json")
        self.order_id = order_res.data["id"]
        self.order_item_id = order_res.data["items"][0]["id"]
        session_res = self._start_session(extra={"order": self.order_id})
        self.session_id = session_res.data["id"]

    def test_create_waste_log_with_auto_penalty(self):
        res = self.client.post("/api/v1/waste-logs", {
            "branch": self.branch.id,
            "order_item": self.order_item_id,
            "quantity_wasted": 2,
            "reason": "Left on plate",
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # penalty = waste_penalty_amount * quantity_wasted = 5.00 * 2 = 10.00
        self.assertEqual(str(res.data["penalty_applied"]), "10.00")
        self.assertEqual(res.data["marked_by"], self.owner.id)

    def test_waste_log_without_order_item(self):
        res = self.client.post("/api/v1/waste-logs", {
            "branch": self.branch.id,
            "quantity_wasted": 1,
            "reason": "General waste",
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(str(res.data["penalty_applied"]), "0.00")

    def test_waste_log_other_tenant_order_item_rejected(self):
        # Create order_item in other tenant
        other_category = MenuCategory.objects.create(
            tenant=self.other_tenant, branch=self.other_branch, name="Other Mains", sort_order=1
        )
        other_item = MenuItem.objects.create(
            tenant=self.other_tenant, branch=self.other_branch, category=other_category,
            name="Pasta", base_price="10.00", vat_rate="10.00",
        )
        self._auth(self.other_user)
        other_order_res = self.client.post("/api/v1/orders", {
            "branch": self.other_branch.id,
            "channel": "DINE_IN",
            "items": [{"menu_item": other_item.id, "quantity": 1}],
        }, format="json")
        other_order_item_id = other_order_res.data["items"][0]["id"]

        self._auth(self.owner)
        res = self.client.post("/api/v1/waste-logs", {
            "branch": self.branch.id,
            "order_item": other_order_item_id,
            "quantity_wasted": 1,
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_waiter_cannot_create_waste_log(self):
        self._auth(self.waiter)
        res = self.client.post("/api/v1/waste-logs", {
            "branch": self.branch.id,
            "quantity_wasted": 1,
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class BuffetAnalyticsTests(BuffetTestBase):

    def test_analytics_aggregates(self):
        self._auth()
        self._start_session(adults=2, kids=1)
        self._start_session(adults=4, kids=0)

        res = self.client.get("/api/v1/buffet/analytics")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["total_sessions"], 2)
        self.assertEqual(res.data["total_adults"], 6)
        self.assertEqual(res.data["total_kids"], 1)
        self.assertEqual(res.data["total_waste_logs"], 0)

    def test_analytics_filter_by_branch(self):
        self._auth()
        self._start_session()
        res = self.client.get(f"/api/v1/buffet/analytics?branch={self.branch.id}")
        self.assertEqual(res.data["total_sessions"], 1)

    def test_analytics_tenant_isolation(self):
        self._auth()
        self._start_session()
        self._auth(self.other_user)
        res = self.client.get("/api/v1/buffet/analytics")
        self.assertEqual(res.data["total_sessions"], 0)
