from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from menu.models import MenuCategory, MenuItem
from tenants.models import Branch, Tenant

User = get_user_model()


class OrderApiTests(APITestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tenant Orders")
        self.branch = Branch.objects.create(tenant=self.tenant, name="Main")
        self.owner = User.objects.create_user(
            username="owner_orders",
            password="StrongPass123",
            role=User.Role.OWNER,
            tenant=self.tenant,
            branch=self.branch,
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
            base_price="10.00",
            vat_rate="10.00",
        )

        # Second tenant for isolation tests
        self.other_tenant = Tenant.objects.create(name="Other Tenant")
        self.other_branch = Branch.objects.create(tenant=self.other_tenant, name="Other Branch")
        self.other_user = User.objects.create_user(
            username="owner_other",
            password="StrongPass123",
            role=User.Role.OWNER,
            tenant=self.other_tenant,
            branch=self.other_branch,
        )

    def _auth(self, user=None):
        user = user or self.owner
        access = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    def _create_order(self, extra=None):
        payload = {
            "branch": self.branch.id,
            "channel": "DINE_IN",
            "notes": "Test order",
            "items": [
                {
                    "menu_item": self.menu_item.id,
                    "quantity": 2,
                }
            ],
        }
        if extra:
            payload.update(extra)
        return self.client.post("/api/v1/orders", payload, format="json")

    def test_create_order_with_items(self):
        self._auth()
        res = self._create_order()
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["status"], "OPEN")
        self.assertEqual(len(res.data["items"]), 1)
        item = res.data["items"][0]
        self.assertEqual(item["item_name"], "Margherita")
        self.assertEqual(item["quantity"], 2)
        self.assertEqual(str(item["unit_price"]), "10.00")
        self.assertEqual(str(item["vat_rate"]), "10.00")

    def test_list_orders_scoped_to_tenant(self):
        self._auth()
        self._create_order()
        res = self.client.get("/api/v1/orders")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 1)

    def test_list_filter_by_branch(self):
        self._auth()
        self._create_order()
        res = self.client.get(f"/api/v1/orders?branch={self.branch.id}")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 1)

    def test_list_filter_by_status(self):
        self._auth()
        self._create_order()
        res = self.client.get("/api/v1/orders?status=OPEN")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 1)

        res = self.client.get("/api/v1/orders?status=COMPLETED")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 0)

    def test_order_detail(self):
        self._auth()
        create_res = self._create_order()
        order_id = create_res.data["id"]

        res = self.client.get(f"/api/v1/orders/{order_id}")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["id"], order_id)
        self.assertEqual(len(res.data["items"]), 1)

    def test_send_to_kitchen(self):
        self._auth()
        create_res = self._create_order()
        order_id = create_res.data["id"]

        res = self.client.post(f"/api/v1/orders/{order_id}/send-to-kitchen")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], "SENT_TO_KITCHEN")
        # Items should be moved to SENT
        for item in res.data["items"]:
            self.assertEqual(item["status"], "SENT")

    def test_send_to_kitchen_canceled_order_rejected(self):
        self._auth()
        create_res = self._create_order()
        order_id = create_res.data["id"]

        # Cancel via PATCH
        self.client.patch(f"/api/v1/orders/{order_id}", {"status": "CANCELED"}, format="json")
        res = self.client.post(f"/api/v1/orders/{order_id}/send-to-kitchen")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_tenant_isolation(self):
        # Create order as owner of tenant 1
        self._auth(self.owner)
        create_res = self._create_order()
        order_id = create_res.data["id"]

        # Other tenant cannot see it
        self._auth(self.other_user)
        res = self.client.get(f"/api/v1/orders/{order_id}")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_rejected(self):
        self.client.credentials()
        res = self.client.get("/api/v1/orders")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_branch_from_other_tenant_rejected(self):
        self._auth()
        res = self.client.post(
            "/api/v1/orders",
            {
                "branch": self.other_branch.id,
                "channel": "DINE_IN",
                "items": [{"menu_item": self.menu_item.id, "quantity": 1}],
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
