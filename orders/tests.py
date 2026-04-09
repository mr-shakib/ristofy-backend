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


class OrderStatusActionTests(APITestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tenant Status")
        self.branch = Branch.objects.create(tenant=self.tenant, name="Main")
        self.owner = User.objects.create_user(
            username="owner_status",
            password="StrongPass123",
            role=User.Role.OWNER,
            tenant=self.tenant,
            branch=self.branch,
        )
        self.waiter = User.objects.create_user(
            username="waiter_status",
            password="StrongPass123",
            role=User.Role.WAITER,
            tenant=self.tenant,
            branch=self.branch,
        )
        self.category = MenuCategory.objects.create(
            tenant=self.tenant, branch=self.branch, name="Drinks", sort_order=1
        )
        self.menu_item = MenuItem.objects.create(
            tenant=self.tenant,
            branch=self.branch,
            category=self.category,
            name="Water",
            base_price="2.00",
            vat_rate="10.00",
        )

    def _auth(self, user):
        access = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    def _create_order(self):
        self._auth(self.owner)
        res = self.client.post(
            "/api/v1/orders",
            {"branch": self.branch.id, "channel": "DINE_IN", "items": [{"menu_item": self.menu_item.id, "quantity": 1}]},
            format="json",
        )
        return res.data["id"]

    def test_order_no_assigned_on_create(self):
        self._auth(self.owner)
        res = self.client.post(
            "/api/v1/orders",
            {"branch": self.branch.id, "channel": "DINE_IN", "items": [{"menu_item": self.menu_item.id, "quantity": 1}]},
            format="json",
        )
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["order_no"], 1)

        res2 = self.client.post(
            "/api/v1/orders",
            {"branch": self.branch.id, "channel": "DINE_IN", "items": [{"menu_item": self.menu_item.id, "quantity": 1}]},
            format="json",
        )
        self.assertEqual(res2.data["order_no"], 2)

    def test_cancel_order(self):
        order_id = self._create_order()
        res = self.client.post(f"/api/v1/orders/{order_id}/cancel")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["status"], "CANCELED")

    def test_cancel_already_canceled_rejected(self):
        order_id = self._create_order()
        self.client.post(f"/api/v1/orders/{order_id}/cancel")
        res = self.client.post(f"/api/v1/orders/{order_id}/cancel")
        self.assertEqual(res.status_code, 400)

    def test_cancel_completed_order_rejected(self):
        order_id = self._create_order()
        self.client.post(f"/api/v1/orders/{order_id}/complete")
        res = self.client.post(f"/api/v1/orders/{order_id}/cancel")
        self.assertEqual(res.status_code, 400)

    def test_complete_order(self):
        order_id = self._create_order()
        res = self.client.post(f"/api/v1/orders/{order_id}/complete")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["status"], "COMPLETED")

    def test_complete_already_completed_rejected(self):
        order_id = self._create_order()
        self.client.post(f"/api/v1/orders/{order_id}/complete")
        res = self.client.post(f"/api/v1/orders/{order_id}/complete")
        self.assertEqual(res.status_code, 400)

    def test_complete_canceled_order_rejected(self):
        order_id = self._create_order()
        self.client.post(f"/api/v1/orders/{order_id}/cancel")
        res = self.client.post(f"/api/v1/orders/{order_id}/complete")
        self.assertEqual(res.status_code, 400)

    def test_waiter_can_create_order(self):
        self._auth(self.waiter)
        res = self.client.post(
            "/api/v1/orders",
            {"branch": self.branch.id, "channel": "DINE_IN", "items": [{"menu_item": self.menu_item.id, "quantity": 1}]},
            format="json",
        )
        self.assertEqual(res.status_code, 201)

    def test_waiter_cannot_cancel_order(self):
        order_id = self._create_order()
        self._auth(self.waiter)
        res = self.client.post(f"/api/v1/orders/{order_id}/cancel")
        self.assertEqual(res.status_code, 403)

    def test_waiter_cannot_complete_order(self):
        order_id = self._create_order()
        self._auth(self.waiter)
        res = self.client.post(f"/api/v1/orders/{order_id}/complete")
        self.assertEqual(res.status_code, 403)


class OrderItemSubEndpointTests(APITestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tenant Items")
        self.branch = Branch.objects.create(tenant=self.tenant, name="Main")
        self.owner = User.objects.create_user(
            username="owner_items",
            password="StrongPass123",
            role=User.Role.OWNER,
            tenant=self.tenant,
            branch=self.branch,
        )
        self.category = MenuCategory.objects.create(
            tenant=self.tenant, branch=self.branch, name="Pasta", sort_order=1
        )
        self.menu_item = MenuItem.objects.create(
            tenant=self.tenant,
            branch=self.branch,
            category=self.category,
            name="Carbonara",
            base_price="12.00",
            vat_rate="10.00",
        )
        self.menu_item2 = MenuItem.objects.create(
            tenant=self.tenant,
            branch=self.branch,
            category=self.category,
            name="Amatriciana",
            base_price="11.00",
            vat_rate="10.00",
        )

    def _auth(self):
        access = str(RefreshToken.for_user(self.owner).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    def _create_order(self):
        self._auth()
        res = self.client.post(
            "/api/v1/orders",
            {
                "branch": self.branch.id,
                "channel": "DINE_IN",
                "items": [{"menu_item": self.menu_item.id, "quantity": 1}],
            },
            format="json",
        )
        return res.data["id"]

    def test_add_item_to_order(self):
        order_id = self._create_order()
        res = self.client.post(
            f"/api/v1/orders/{order_id}/items",
            {"menu_item": self.menu_item2.id, "quantity": 3},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["item_name"], "Amatriciana")
        self.assertEqual(res.data["quantity"], 3)
        self.assertEqual(str(res.data["unit_price"]), "11.00")

        # Order should now have 2 items
        detail = self.client.get(f"/api/v1/orders/{order_id}")
        self.assertEqual(len(detail.data["items"]), 2)

    def test_add_item_to_canceled_order_rejected(self):
        order_id = self._create_order()
        self.client.patch(f"/api/v1/orders/{order_id}", {"status": "CANCELED"}, format="json")
        res = self.client.post(
            f"/api/v1/orders/{order_id}/items",
            {"menu_item": self.menu_item2.id, "quantity": 1},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_item_quantity_and_notes(self):
        order_id = self._create_order()
        detail = self.client.get(f"/api/v1/orders/{order_id}")
        item_id = detail.data["items"][0]["id"]

        res = self.client.patch(
            f"/api/v1/orders/{order_id}/items/{item_id}",
            {"quantity": 5, "notes": "Extra sauce"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["quantity"], 5)
        self.assertEqual(res.data["notes"], "Extra sauce")

    def test_delete_item(self):
        order_id = self._create_order()
        detail = self.client.get(f"/api/v1/orders/{order_id}")
        item_id = detail.data["items"][0]["id"]

        res = self.client.delete(f"/api/v1/orders/{order_id}/items/{item_id}")
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        detail = self.client.get(f"/api/v1/orders/{order_id}")
        self.assertEqual(len(detail.data["items"]), 0)

    def test_item_from_other_order_not_accessible(self):
        order_id = self._create_order()
        # Create a second order
        order2_res = self.client.post(
            "/api/v1/orders",
            {"branch": self.branch.id, "channel": "DINE_IN", "items": [{"menu_item": self.menu_item.id, "quantity": 1}]},
            format="json",
        )
        item_from_order2 = order2_res.data["items"][0]["id"]

        # Try to PATCH item from order2 via order1's URL
        res = self.client.patch(
            f"/api/v1/orders/{order_id}/items/{item_from_order2}",
            {"quantity": 99},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)


class KitchenTicketTests(APITestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tenant Kitchen")
        self.branch = Branch.objects.create(tenant=self.tenant, name="Main")
        self.owner = User.objects.create_user(
            username="owner_kitchen",
            password="StrongPass123",
            role=User.Role.OWNER,
            tenant=self.tenant,
            branch=self.branch,
        )
        self.category = MenuCategory.objects.create(
            tenant=self.tenant, branch=self.branch, name="Grill", sort_order=1
        )
        self.menu_item = MenuItem.objects.create(
            tenant=self.tenant,
            branch=self.branch,
            category=self.category,
            name="Bistecca",
            base_price="25.00",
            vat_rate="10.00",
        )

        self.other_tenant = Tenant.objects.create(name="Other Kitchen Tenant")
        self.other_branch = Branch.objects.create(tenant=self.other_tenant, name="Other")
        self.other_user = User.objects.create_user(
            username="owner_kitchen_other",
            password="StrongPass123",
            role=User.Role.OWNER,
            tenant=self.other_tenant,
            branch=self.other_branch,
        )

    def _auth(self, user=None):
        user = user or self.owner
        access = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    def _create_and_send_order(self):
        res = self.client.post(
            "/api/v1/orders",
            {"branch": self.branch.id, "channel": "DINE_IN", "items": [{"menu_item": self.menu_item.id, "quantity": 1}]},
            format="json",
        )
        order_id = res.data["id"]
        self.client.post(f"/api/v1/orders/{order_id}/send-to-kitchen")
        return order_id

    def test_send_to_kitchen_creates_ticket(self):
        self._auth()
        self._create_and_send_order()
        res = self.client.get("/api/v1/kitchen/tickets")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 1)
        self.assertEqual(res.data["results"][0]["status"], "PENDING")

    def test_filter_tickets_by_status(self):
        self._auth()
        self._create_and_send_order()
        res = self.client.get("/api/v1/kitchen/tickets?status=PENDING")
        self.assertEqual(res.data["count"], 1)

        res = self.client.get("/api/v1/kitchen/tickets?status=PREPARED")
        self.assertEqual(res.data["count"], 0)

    def test_mark_ticket_prepared(self):
        self._auth()
        self._create_and_send_order()
        tickets = self.client.get("/api/v1/kitchen/tickets")
        ticket_id = tickets.data["results"][0]["id"]

        res = self.client.post(f"/api/v1/kitchen/tickets/{ticket_id}/prepared")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], "PREPARED")

    def test_mark_prepared_twice_rejected(self):
        self._auth()
        self._create_and_send_order()
        tickets = self.client.get("/api/v1/kitchen/tickets")
        ticket_id = tickets.data["results"][0]["id"]

        self.client.post(f"/api/v1/kitchen/tickets/{ticket_id}/prepared")
        res = self.client.post(f"/api/v1/kitchen/tickets/{ticket_id}/prepared")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_kitchen_tickets_tenant_isolation(self):
        self._auth(self.owner)
        self._create_and_send_order()

        self._auth(self.other_user)
        res = self.client.get("/api/v1/kitchen/tickets")
        self.assertEqual(res.data["count"], 0)
