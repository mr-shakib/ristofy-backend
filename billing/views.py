from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from users.audit import log_activity
from users.permissions import IsOwnerOrManager

from .models import Bill
from .serializers import BillCreateFromOrderSerializer, BillSerializer


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
            .prefetch_related("lines")
        )
