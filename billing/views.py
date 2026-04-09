from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from users.audit import log_activity
from users.permissions import IsOwnerOrManager

from .models import Bill, FiscalTransaction, Receipt
from .serializers import (
    BillApplyCopertoSerializer,
    BillApplyDiscountSerializer,
    BillCreateFromOrderSerializer,
    BillPaySerializer,
    BillSerializer,
    FiscalAckSerializer,
    FiscalTransactionSerializer,
    FiscalZReportSyncSerializer,
    ReceiptRefundCreateSerializer,
    ReceiptSerializer,
)


class BillCreateFromOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def post(self, request):
        serializer = BillCreateFromOrderSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        order = serializer.validated_data["order"]

        try:
            bill = Bill.create_from_order(order)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        log_activity(
            actor_user=request.user,
            action="bill_created",
            entity_type="bill",
            entity_id=str(bill.id),
            tenant=request.user.tenant,
            branch=bill.branch,
            metadata={"order_id": bill.order_id, "bill_no": bill.bill_no},
        )

        return Response(BillSerializer(bill, context={"request": request}).data, status=status.HTTP_201_CREATED)


class BillDetailView(generics.RetrieveAPIView):
    serializer_class = BillSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def get_queryset(self):
        return (
            Bill.objects.filter(tenant=self.request.user.tenant)
            .select_related("tenant", "branch", "order")
            .prefetch_related("lines", "payments")
        )


class _BillActionBaseView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def get_bill(self, request, pk):
        try:
            return (
                Bill.objects.filter(tenant=request.user.tenant)
                .select_related("tenant", "branch", "order")
                .get(pk=pk)
            )
        except Bill.DoesNotExist:
            return None


class BillApplyCopertoView(_BillActionBaseView):
    def post(self, request, pk):
        bill = self.get_bill(request, pk)
        if bill is None:
            return Response({"detail": "Bill not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = BillApplyCopertoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            line = bill.apply_coperto(
                amount=serializer.validated_data["amount"],
                covers=serializer.validated_data["covers"],
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        log_activity(
            actor_user=request.user,
            action="bill_coperto_applied",
            entity_type="bill",
            entity_id=str(bill.id),
            tenant=request.user.tenant,
            branch=bill.branch,
            metadata={
                "line_id": line.id,
                "amount": str(serializer.validated_data["amount"]),
                "covers": serializer.validated_data["covers"],
            },
        )

        bill.refresh_from_db()
        return Response(BillSerializer(bill, context={"request": request}).data, status=status.HTTP_200_OK)


class BillApplyDiscountView(_BillActionBaseView):
    def post(self, request, pk):
        bill = self.get_bill(request, pk)
        if bill is None:
            return Response({"detail": "Bill not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = BillApplyDiscountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            line = bill.apply_discount(
                discount_type=serializer.validated_data["type"],
                value=serializer.validated_data["value"],
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        log_activity(
            actor_user=request.user,
            action="bill_discount_applied",
            entity_type="bill",
            entity_id=str(bill.id),
            tenant=request.user.tenant,
            branch=bill.branch,
            metadata={
                "line_id": line.id,
                "discount_type": serializer.validated_data["type"],
                "value": str(serializer.validated_data["value"]),
            },
        )

        bill.refresh_from_db()
        return Response(BillSerializer(bill, context={"request": request}).data, status=status.HTTP_200_OK)


class BillFinalizeView(_BillActionBaseView):
    def post(self, request, pk):
        bill = self.get_bill(request, pk)
        if bill is None:
            return Response({"detail": "Bill not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            bill.finalize()
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        log_activity(
            actor_user=request.user,
            action="bill_finalized",
            entity_type="bill",
            entity_id=str(bill.id),
            tenant=request.user.tenant,
            branch=bill.branch,
        )

        bill.refresh_from_db()
        return Response(BillSerializer(bill, context={"request": request}).data, status=status.HTTP_200_OK)


class BillPayView(_BillActionBaseView):
    def post(self, request, pk):
        bill = self.get_bill(request, pk)
        if bill is None:
            return Response({"detail": "Bill not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = BillPaySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            payment = bill.record_payment(
                method=serializer.validated_data["method"],
                amount=serializer.validated_data["amount"],
                reference=serializer.validated_data.get("reference", ""),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        log_activity(
            actor_user=request.user,
            action="bill_payment_recorded",
            entity_type="bill",
            entity_id=str(bill.id),
            tenant=request.user.tenant,
            branch=bill.branch,
            metadata={
                "payment_id": payment.id,
                "method": payment.method,
                "amount": str(payment.amount),
            },
        )

        bill.refresh_from_db()
        return Response(BillSerializer(bill, context={"request": request}).data, status=status.HTTP_200_OK)


class BillSendToFiscalView(_BillActionBaseView):
    def post(self, request, pk):
        bill = self.get_bill(request, pk)
        if bill is None:
            return Response({"detail": "Bill not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            receipt, fiscal_tx = bill.send_to_fiscal()
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        log_activity(
            actor_user=request.user,
            action="bill_sent_to_fiscal",
            entity_type="bill",
            entity_id=str(bill.id),
            tenant=request.user.tenant,
            branch=bill.branch,
            metadata={
                "receipt_id": receipt.id,
                "fiscal_transaction_id": fiscal_tx.id,
                "fiscal_receipt_no": receipt.fiscal_receipt_no,
            },
        )

        return Response(
            {
                "receipt": ReceiptSerializer(receipt, context={"request": request}).data,
                "fiscal_transaction": FiscalTransactionSerializer(fiscal_tx, context={"request": request}).data,
            },
            status=status.HTTP_200_OK,
        )


class ReceiptDetailView(generics.RetrieveAPIView):
    serializer_class = ReceiptSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def get_queryset(self):
        return (
            Receipt.objects.filter(bill__tenant=self.request.user.tenant)
            .select_related("bill", "bill__tenant", "bill__branch")
            .prefetch_related("refunds")
        )


class _ReceiptActionBaseView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def get_receipt(self, request, pk):
        try:
            return Receipt.objects.select_related("bill", "bill__tenant", "bill__branch").get(
                pk=pk,
                bill__tenant=request.user.tenant,
            )
        except Receipt.DoesNotExist:
            return None


class ReceiptReprintView(_ReceiptActionBaseView):
    def post(self, request, pk):
        receipt = self.get_receipt(request, pk)
        if receipt is None:
            return Response({"detail": "Receipt not found."}, status=status.HTTP_404_NOT_FOUND)

        fiscal_tx = receipt.register_reprint()
        log_activity(
            actor_user=request.user,
            action="receipt_reprinted",
            entity_type="receipt",
            entity_id=str(receipt.id),
            tenant=request.user.tenant,
            branch=receipt.bill.branch,
            metadata={"fiscal_transaction_id": fiscal_tx.id, "reprint_count": receipt.reprint_count},
        )

        receipt.refresh_from_db()
        return Response(ReceiptSerializer(receipt, context={"request": request}).data, status=status.HTTP_200_OK)


class ReceiptRefundView(_ReceiptActionBaseView):
    def post(self, request, pk):
        receipt = self.get_receipt(request, pk)
        if receipt is None:
            return Response({"detail": "Receipt not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ReceiptRefundCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            refund, fiscal_tx = receipt.create_refund(
                amount=serializer.validated_data["amount"],
                reason=serializer.validated_data.get("reason", ""),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        log_activity(
            actor_user=request.user,
            action="receipt_refunded",
            entity_type="receipt",
            entity_id=str(receipt.id),
            tenant=request.user.tenant,
            branch=receipt.bill.branch,
            metadata={
                "refund_id": refund.id,
                "amount": str(refund.amount),
                "fiscal_transaction_id": fiscal_tx.id,
            },
        )

        receipt.refresh_from_db()
        return Response(ReceiptSerializer(receipt, context={"request": request}).data, status=status.HTTP_200_OK)


class FiscalZReportSyncView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def post(self, request):
        serializer = FiscalZReportSyncSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        branch = serializer.validated_data["branch"]
        business_date = serializer.validated_data.get("business_date")
        z_report_no = serializer.validated_data.get("z_report_no", "")

        fiscal_tx = FiscalTransaction.objects.create(
            tenant=request.user.tenant,
            branch=branch,
            transaction_type=FiscalTransaction.TransactionType.Z_REPORT_SYNC,
            status=FiscalTransaction.Status.COMPLETED,
            external_id=f"zsync-{timezone.now().strftime('%Y%m%d%H%M%S%f')}",
            request_json={
                "branch_id": branch.id,
                "business_date": str(business_date) if business_date else None,
                "z_report_no": z_report_no,
            },
            response_json={"synced": True},
        )

        if z_report_no:
            Receipt.objects.filter(bill__branch=branch, bill__tenant=request.user.tenant).update(z_report_no=z_report_no)

        log_activity(
            actor_user=request.user,
            action="fiscal_z_report_synced",
            entity_type="fiscal_transaction",
            entity_id=str(fiscal_tx.id),
            tenant=request.user.tenant,
            branch=branch,
        )

        return Response(FiscalTransactionSerializer(fiscal_tx, context={"request": request}).data, status=status.HTTP_201_CREATED)


class FiscalZReportStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def get(self, request):
        qs = FiscalTransaction.objects.filter(
            tenant=request.user.tenant,
            transaction_type=FiscalTransaction.TransactionType.Z_REPORT_SYNC,
        ).select_related("branch")

        branch_id = request.query_params.get("branch")
        if branch_id:
            qs = qs.filter(branch_id=branch_id)

        last_sync = qs.order_by("-created_at").first()
        total_syncs = qs.count()

        return Response(
            {
                "last_sync": FiscalTransactionSerializer(last_sync, context={"request": request}).data if last_sync else None,
                "total_syncs": total_syncs,
            },
            status=status.HTTP_200_OK,
        )


class BridgeFiscalAckView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def post(self, request):
        serializer = FiscalAckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        external_id = serializer.validated_data["external_id"]
        try:
            tx = FiscalTransaction.objects.get(external_id=external_id, tenant=request.user.tenant)
        except FiscalTransaction.DoesNotExist:
            return Response({"detail": "Fiscal transaction not found."}, status=status.HTTP_404_NOT_FOUND)

        tx.status = serializer.validated_data["status"]
        if "response_json" in serializer.validated_data:
            tx.response_json = serializer.validated_data["response_json"]
        tx.error_code = serializer.validated_data.get("error_code", "")
        tx.save(update_fields=["status", "response_json", "error_code", "updated_at"])

        log_activity(
            actor_user=request.user,
            action="fiscal_bridge_ack_received",
            entity_type="fiscal_transaction",
            entity_id=str(tx.id),
            tenant=request.user.tenant,
            branch=tx.branch,
        )

        return Response(FiscalTransactionSerializer(tx, context={"request": request}).data, status=status.HTTP_200_OK)
