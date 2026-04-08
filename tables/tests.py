from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from tenants.models import Branch, Tenant

User = get_user_model()


class TablesApiTests(APITestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tenant Tables")
        self.branch = Branch.objects.create(tenant=self.tenant, name="Main")
        self.owner = User.objects.create_user(
            username="owner_tables",
            password="StrongPass123",
            role=User.Role.OWNER,
            tenant=self.tenant,
            branch=self.branch,
        )

    def _auth(self):
        access = str(RefreshToken.for_user(self.owner).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    def test_create_floor_plan_table_and_reservation(self):
        self._auth()
        floor_res = self.client.post(
            "/api/v1/floor-plans",
            {"branch": self.branch.id, "name": "Main Hall", "layout_json": {"w": 100, "h": 60}},
            format="json",
        )
        self.assertEqual(floor_res.status_code, status.HTTP_201_CREATED)

        table_res = self.client.post(
            "/api/v1/tables",
            {
                "branch": self.branch.id,
                "floor_plan": floor_res.data["id"],
                "code": "T1",
                "seats": 4,
                "state": "FREE",
                "x": 10,
                "y": 20,
            },
            format="json",
        )
        self.assertEqual(table_res.status_code, status.HTTP_201_CREATED)

        reservation_res = self.client.post(
            "/api/v1/reservations",
            {
                "branch": self.branch.id,
                "table": table_res.data["id"],
                "customer_name": "Mario Rossi",
                "customer_phone": "+390000000",
                "party_size": 2,
                "reserved_for": (timezone.now() + timedelta(hours=1)).isoformat(),
                "status": "CONFIRMED",
                "notes": "Window seat",
            },
            format="json",
        )
        self.assertEqual(reservation_res.status_code, status.HTTP_201_CREATED)

    def test_table_detail_update(self):
        self._auth()
        floor_res = self.client.post(
            "/api/v1/floor-plans",
            {"branch": self.branch.id, "name": "Patio", "layout_json": {}},
            format="json",
        )
        table_res = self.client.post(
            "/api/v1/tables",
            {
                "branch": self.branch.id,
                "floor_plan": floor_res.data["id"],
                "code": "T9",
                "seats": 2,
                "state": "FREE",
                "x": 0,
                "y": 0,
            },
            format="json",
        )

        update_res = self.client.patch(
            f"/api/v1/tables/{table_res.data['id']}",
            {"state": "RESERVED", "seats": 6},
            format="json",
        )
        self.assertEqual(update_res.status_code, status.HTTP_200_OK)
        self.assertEqual(update_res.data["state"], "RESERVED")
        self.assertEqual(update_res.data["seats"], 6)

    def test_reservation_overlap_is_rejected(self):
        self._auth()
        floor_res = self.client.post(
            "/api/v1/floor-plans",
            {"branch": self.branch.id, "name": "Main Hall", "layout_json": {}},
            format="json",
        )
        table_res = self.client.post(
            "/api/v1/tables",
            {
                "branch": self.branch.id,
                "floor_plan": floor_res.data["id"],
                "code": "T1",
                "seats": 4,
                "state": "FREE",
                "x": 10,
                "y": 20,
            },
            format="json",
        )
        timeslot = (timezone.now() + timedelta(hours=2)).replace(microsecond=0).isoformat()

        first = self.client.post(
            "/api/v1/reservations",
            {
                "branch": self.branch.id,
                "table": table_res.data["id"],
                "customer_name": "Mario Rossi",
                "customer_phone": "+390000000",
                "party_size": 2,
                "reserved_for": timeslot,
                "status": "CONFIRMED",
                "notes": "Window seat",
            },
            format="json",
        )
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)

        second = self.client.post(
            "/api/v1/reservations",
            {
                "branch": self.branch.id,
                "table": table_res.data["id"],
                "customer_name": "Luigi Verdi",
                "customer_phone": "+390000111",
                "party_size": 3,
                "reserved_for": timeslot,
                "status": "CONFIRMED",
                "notes": "Near entrance",
            },
            format="json",
        )
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("reserved_for", second.data)
