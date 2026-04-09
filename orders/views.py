from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import StandardResultsSetPagination
from users.audit import log_activity
from users.permissions import IsOwnerOrManager

from .models import Order
from .serializers import OrderCreateSerializer, OrderSerializer


class OrderListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        if self.request.method == "POST":
            return OrderCreateSerializer
        return OrderSerializer

    def get_queryset(self):
        queryset = (
            Order.objects.filter(tenant=self.request.user.tenant)
            .select_related("branch", "table", "waiter_user")
            .prefetch_related("items")
            .order_by("-created_at")
        )
        params = self.request.query_params

        branch = params.get("branch")
        if branch:
            queryset = queryset.filter(branch_id=branch)

        order_status = params.get("status")
        if order_status:
            queryset = queryset.filter(status=order_status)

        channel = params.get("channel")
        if channel:
            queryset = queryset.filter(channel=channel)

        return queryset

    def perform_create(self, serializer):
        order = serializer.save()
        log_activity(
            actor_user=self.request.user,
            action="order_created",
            entity_type="order",
            entity_id=str(order.id),
            tenant=self.request.user.tenant,
            branch=order.branch,
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # Return full representation with items
        output = OrderSerializer(serializer.instance, context={"request": request})
        return Response(output.data, status=status.HTTP_201_CREATED)


class OrderDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def get_queryset(self):
        return (
            Order.objects.filter(tenant=self.request.user.tenant)
            .select_related("branch", "table", "waiter_user")
            .prefetch_related("items")
        )

    def perform_update(self, serializer):
        order = serializer.save()
        log_activity(
            actor_user=self.request.user,
            action="order_updated",
            entity_type="order",
            entity_id=str(order.id),
            tenant=self.request.user.tenant,
            branch=order.branch,
        )


class OrderSendToKitchenView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def post(self, request, pk):
        try:
            order = (
                Order.objects.select_related("branch")
                .prefetch_related("items")
                .get(pk=pk, tenant=request.user.tenant)
            )
        except Order.DoesNotExist:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        if order.status == Order.Status.CANCELED:
            return Response(
                {"detail": "Canceled orders cannot be sent to kitchen."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if order.status == Order.Status.COMPLETED:
            return Response(
                {"detail": "Completed orders cannot be sent to kitchen again."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.status = Order.Status.SENT_TO_KITCHEN
        order.save(update_fields=["status", "updated_at"])

        # Mark pending items as sent
        order.items.filter(status="PENDING").update(status="SENT")

        log_activity(
            actor_user=request.user,
            action="order_sent_to_kitchen",
            entity_type="order",
            entity_id=str(order.id),
            tenant=request.user.tenant,
            branch=order.branch,
        )

        # Re-fetch to get updated item statuses
        order.refresh_from_db()
        return Response(
            OrderSerializer(order, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )
