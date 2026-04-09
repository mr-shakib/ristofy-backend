from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from menu.models import MenuCategory, MenuItem
from orders.models import Order, OrderItem
from tenants.models import Branch, Tenant

from .models import Bill, FiscalTransaction, Receipt

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

    def _create_bill(self):
        self._auth(self.owner)
        order = self._create_order()
        res = self.client.post("/api/v1/bills/create-from-order", {"order": order.id}, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        return res.data["id"]

    def test_apply_coperto(self):
        bill_id = self._create_bill()

        res = self.client.post(
            f"/api/v1/bills/{bill_id}/apply-coperto",
            {"amount": "2.00", "covers": 4},
            format="json",
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(str(res.data["coperto_total"]), "8.00")
        self.assertEqual(str(res.data["grand_total"]), "46.60")
        self.assertEqual(len(res.data["lines"]), 3)

    def test_apply_discount_percent(self):
        bill_id = self._create_bill()

        res = self.client.post(
            f"/api/v1/bills/{bill_id}/apply-discount",
            {"type": "PERCENT", "value": "10.00"},
            format="json",
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(str(res.data["discount_total"]), "3.86")
        self.assertEqual(str(res.data["grand_total"]), "34.74")

    def test_finalize_bill(self):
        bill_id = self._create_bill()

        res = self.client.post(f"/api/v1/bills/{bill_id}/finalize")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], "FINALIZED")

    def test_cannot_modify_after_finalize(self):
        bill_id = self._create_bill()
        self.client.post(f"/api/v1/bills/{bill_id}/finalize")

        coperto_res = self.client.post(
            f"/api/v1/bills/{bill_id}/apply-coperto",
            {"amount": "2.00", "covers": 4},
            format="json",
        )
        discount_res = self.client.post(
            f"/api/v1/bills/{bill_id}/apply-discount",
            {"type": "FIXED", "value": "5.00"},
            format="json",
        )

        self.assertEqual(coperto_res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(discount_res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pay_requires_finalize(self):
        bill_id = self._create_bill()

        res = self.client.post(
            f"/api/v1/bills/{bill_id}/pay",
            {"method": "CASH", "amount": "10.00"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pay_marks_bill_paid_when_fully_covered(self):
        bill_id = self._create_bill()
        self.client.post(f"/api/v1/bills/{bill_id}/finalize")

        part = self.client.post(
            f"/api/v1/bills/{bill_id}/pay",
            {"method": "CARD", "amount": "20.00", "reference": "POS-1"},
            format="json",
        )
        self.assertEqual(part.status_code, status.HTTP_200_OK)
        self.assertEqual(part.data["status"], "FINALIZED")
        self.assertEqual(str(part.data["amount_paid"]), "20.00")

        final = self.client.post(
            f"/api/v1/bills/{bill_id}/pay",
            {"method": "CASH", "amount": "18.60"},
            format="json",
        )
        self.assertEqual(final.status_code, status.HTTP_200_OK)
        self.assertEqual(final.data["status"], "PAID")
        self.assertEqual(str(final.data["amount_paid"]), "38.60")
        self.assertEqual(len(final.data["payments"]), 2)

    def test_pay_on_paid_bill_rejected(self):
        bill_id = self._create_bill()
        self.client.post(f"/api/v1/bills/{bill_id}/finalize")
        self.client.post(
            f"/api/v1/bills/{bill_id}/pay",
            {"method": "CASH", "amount": "38.60"},
            format="json",
        )

        res = self.client.post(
            f"/api/v1/bills/{bill_id}/pay",
            {"method": "CASH", "amount": "1.00"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_waiter_forbidden_on_actions(self):
        bill_id = self._create_bill()

        self._auth(self.waiter)
        res = self.client.post(
            f"/api/v1/bills/{bill_id}/finalize",
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def _create_finalized_bill(self):
        bill_id = self._create_bill()
        finalize = self.client.post(f"/api/v1/bills/{bill_id}/finalize")
        self.assertEqual(finalize.status_code, status.HTTP_200_OK)
        return bill_id

    def _issue_receipt(self):
        bill_id = self._create_finalized_bill()
        res = self.client.post(f"/api/v1/bills/{bill_id}/send-to-fiscal")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        return bill_id, res.data["receipt"]["id"]

    def test_send_to_fiscal_requires_finalized_bill(self):
        bill_id = self._create_bill()
        res = self.client.post(f"/api/v1/bills/{bill_id}/send-to-fiscal")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_send_to_fiscal_success(self):
        bill_id = self._create_finalized_bill()
        res = self.client.post(f"/api/v1/bills/{bill_id}/send-to-fiscal")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("receipt", res.data)
        self.assertIn("fiscal_transaction", res.data)
        self.assertTrue(res.data["receipt"]["fiscal_receipt_no"].startswith("FR-"))
        self.assertEqual(res.data["fiscal_transaction"]["transaction_type"], "ISSUE_RECEIPT")

    def test_send_to_fiscal_duplicate_rejected(self):
        bill_id = self._create_finalized_bill()
        self.client.post(f"/api/v1/bills/{bill_id}/send-to-fiscal")
        res = self.client.post(f"/api/v1/bills/{bill_id}/send-to-fiscal")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_receipt_detail(self):
        _, receipt_id = self._issue_receipt()
        res = self.client.get(f"/api/v1/receipts/{receipt_id}")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["id"], receipt_id)

    def test_receipt_tenant_isolation(self):
        _, receipt_id = self._issue_receipt()
        self._auth(self.other_owner)
        res = self.client.get(f"/api/v1/receipts/{receipt_id}")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_receipt_reprint(self):
        _, receipt_id = self._issue_receipt()
        reprint = self.client.post(f"/api/v1/receipts/{receipt_id}/reprint")
        self.assertEqual(reprint.status_code, status.HTTP_200_OK)
        self.assertEqual(reprint.data["reprint_count"], 1)

    def test_receipt_refund(self):
        _, receipt_id = self._issue_receipt()
        refund = self.client.post(
            f"/api/v1/receipts/{receipt_id}/refund",
            {"amount": "5.00", "reason": "Customer complaint"},
            format="json",
        )
        self.assertEqual(refund.status_code, status.HTTP_200_OK)
        self.assertEqual(str(refund.data["refunded_total"]), "5.00")
        self.assertEqual(len(refund.data["refunds"]), 1)

    def test_receipt_refund_over_limit_rejected(self):
        _, receipt_id = self._issue_receipt()
        res = self.client.post(
            f"/api/v1/receipts/{receipt_id}/refund",
            {"amount": "1000.00", "reason": "Invalid"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_z_report_sync_and_status(self):
        self._auth(self.manager)
        sync = self.client.post(
            "/api/v1/fiscal/z-report/sync",
            {
                "branch": self.branch.id,
                "business_date": "2026-04-10",
                "z_report_no": "Z-2026-04-10-001",
            },
            format="json",
        )
        self.assertEqual(sync.status_code, status.HTTP_201_CREATED)
        self.assertEqual(sync.data["transaction_type"], "Z_REPORT_SYNC")

        status_res = self.client.get(f"/api/v1/fiscal/z-report/status?branch={self.branch.id}")
        self.assertEqual(status_res.status_code, status.HTTP_200_OK)
        self.assertEqual(status_res.data["total_syncs"], 1)
        self.assertIsNotNone(status_res.data["last_sync"])

    def test_bridge_fiscal_ack(self):
        bill_id = self._create_finalized_bill()
        bill = Bill.objects.get(pk=bill_id)
        tx = FiscalTransaction.objects.create(
            tenant=self.tenant,
            branch=self.branch,
            bill=bill,
            transaction_type=FiscalTransaction.TransactionType.ISSUE_RECEIPT,
            status=FiscalTransaction.Status.SENT,
            external_id="ack-ext-1",
        )

        res = self.client.post(
            "/api/v1/integrations/bridge/fiscal-ack",
            {
                "external_id": "ack-ext-1",
                "status": "ACKED",
                "response_json": {"bridge": "ok"},
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["id"], tx.id)
        self.assertEqual(res.data["status"], "ACKED")

    def test_waiter_forbidden_on_fiscal_endpoints(self):
        bill_id = self._create_finalized_bill()
        self._auth(self.waiter)

        send = self.client.post(f"/api/v1/bills/{bill_id}/send-to-fiscal")
        sync = self.client.post(
            "/api/v1/fiscal/z-report/sync",
            {"branch": self.branch.id},
            format="json",
        )
        self.assertEqual(send.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(sync.status_code, status.HTTP_403_FORBIDDEN)
