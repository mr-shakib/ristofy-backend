from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from users.audit import log_activity
from users.permissions import IsOwnerOrManager

from .models import Bill
from .serializers import (
    BillApplyCopertoSerializer,
    BillApplyDiscountSerializer,
    BillCreateFromOrderSerializer,
    BillPaySerializer,
    BillSerializer,
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
