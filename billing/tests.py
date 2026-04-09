from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from menu.models import MenuCategory, MenuItem
from orders.models import Order, OrderItem
from tenants.models import Branch, Tenant

from .models import Bill

User = get_user_model()


class BillingApiTests(APITestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tenant Billing")
        self.branch = Branch.objects.create(tenant=self.tenant, name="Main")
        self.owner = User.objects.create_user(
            username="owner_billing",
            password="StrongPass123",
            role=User.Role.OWNER,
            tenant=self.tenant,
            branch=self.branch,
        )
        self.manager = User.objects.create_user(
            username="manager_billing",
            password="StrongPass123",
            role=User.Role.MANAGER,
            tenant=self.tenant,
            branch=self.branch,
        )
        self.waiter = User.objects.create_user(
            username="waiter_billing",
            password="StrongPass123",
            role=User.Role.WAITER,
            tenant=self.tenant,
            branch=self.branch,
        )

        self.category = MenuCategory.objects.create(
            tenant=self.tenant,
            branch=self.branch,
            name="Pasta",
            sort_order=1,
        )
        self.item_a = MenuItem.objects.create(
            tenant=self.tenant,
            branch=self.branch,
            category=self.category,
            name="Carbonara",
            base_price="12.00",
            vat_rate="10.00",
        )
        self.item_b = MenuItem.objects.create(
            tenant=self.tenant,
            branch=self.branch,
            category=self.category,
            name="Amatriciana",
            base_price="10.00",
            vat_rate="22.00",
        )

        self.other_tenant = Tenant.objects.create(name="Other Tenant Billing")
        self.other_branch = Branch.objects.create(tenant=self.other_tenant, name="Other")
        self.other_owner = User.objects.create_user(
            username="owner_other_billing",
            password="StrongPass123",
            role=User.Role.OWNER,
            tenant=self.other_tenant,
            branch=self.other_branch,
        )

    def _auth(self, user=None):
        user = user or self.owner
        access = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    def _create_order(self, *, branch=None):
        branch = branch or self.branch
        order = Order.objects.create(
            tenant=branch.tenant,
            branch=branch,
            order_no=Order.next_order_no(branch),
            channel=Order.Channel.DINE_IN,
        )
        OrderItem.objects.create(
            order=order,
            menu_item=self.item_a if branch == self.branch else None,
            item_name="Carbonara",
            unit_price="12.00",
            vat_rate="10.00",
            quantity=2,
        )
        OrderItem.objects.create(
            order=order,
            menu_item=self.item_b if branch == self.branch else None,
            item_name="Amatriciana",
            unit_price="10.00",
            vat_rate="22.00",
            quantity=1,
        )
        return order

    def test_create_bill_from_order(self):
        self._auth(self.owner)
        order = self._create_order()

        res = self.client.post("/api/v1/bills/create-from-order", {"order": order.id}, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["status"], "DRAFT")
        self.assertEqual(res.data["bill_no"], 1)
        self.assertEqual(str(res.data["subtotal"]), "34.00")
        self.assertEqual(str(res.data["vat_total"]), "4.60")
        self.assertEqual(str(res.data["grand_total"]), "38.60")
        self.assertEqual(len(res.data["lines"]), 2)

    def test_bill_no_is_sequential_per_branch(self):
        self._auth(self.owner)
        order_1 = self._create_order()
        order_2 = self._create_order()

        res_1 = self.client.post("/api/v1/bills/create-from-order", {"order": order_1.id}, format="json")
        res_2 = self.client.post("/api/v1/bills/create-from-order", {"order": order_2.id}, format="json")

        self.assertEqual(res_1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_1.data["bill_no"], 1)
        self.assertEqual(res_2.data["bill_no"], 2)

    def test_create_bill_for_same_order_twice_rejected(self):
        self._auth(self.owner)
        order = self._create_order()

        self.client.post("/api/v1/bills/create-from-order", {"order": order.id}, format="json")
        res = self.client.post("/api/v1/bills/create-from-order", {"order": order.id}, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_bill_with_other_tenant_order_rejected(self):
        self._auth(self.owner)
        other_order = Order.objects.create(
            tenant=self.other_tenant,
            branch=self.other_branch,
            order_no=Order.next_order_no(self.other_branch),
            channel=Order.Channel.DINE_IN,
        )

        res = self.client.post("/api/v1/bills/create-from-order", {"order": other_order.id}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_bill_detail(self):
        self._auth(self.manager)
        order = self._create_order()
        create_res = self.client.post("/api/v1/bills/create-from-order", {"order": order.id}, format="json")
        bill_id = create_res.data["id"]

        detail = self.client.get(f"/api/v1/bills/{bill_id}")
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(detail.data["id"], bill_id)
        self.assertEqual(len(detail.data["lines"]), 2)

    def test_tenant_isolation_on_bill_detail(self):
        self._auth(self.owner)
        order = self._create_order()
        bill = Bill.create_from_order(order)

        self._auth(self.other_owner)
        res = self.client.get(f"/api/v1/bills/{bill.id}")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_waiter_forbidden_for_billing_endpoints(self):
        self._auth(self.waiter)
        order = self._create_order()

        create_res = self.client.post("/api/v1/bills/create-from-order", {"order": order.id}, format="json")
        self.assertEqual(create_res.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_rejected(self):
        order = self._create_order()
        self.client.credentials()

        create_res = self.client.post("/api/v1/bills/create-from-order", {"order": order.id}, format="json")
        self.assertEqual(create_res.status_code, status.HTTP_401_UNAUTHORIZED)
