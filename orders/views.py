from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import StandardResultsSetPagination
from users.audit import log_activity
from users.permissions import IsOwnerOrManager, IsWaiterOrAbove

from .models import KitchenTicket, Order, OrderItem
from .serializers import (
    KitchenTicketSerializer,
    OrderCreateSerializer,
    OrderItemAddSerializer,
    OrderItemSerializer,
    OrderItemUpdateSerializer,
    OrderSerializer,
)


class OrderListCreateView(generics.ListCreateAPIView):
    # Waiters and above can list and create orders
    permission_classes = [permissions.IsAuthenticated, IsWaiterOrAbove]
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
        output = OrderSerializer(serializer.instance, context={"request": request})
        return Response(output.data, status=status.HTTP_201_CREATED)


class OrderDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = OrderSerializer
    # Waiters and above can view/update order fields
    permission_classes = [permissions.IsAuthenticated, IsWaiterOrAbove]

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
    # Waiters and above can fire orders to kitchen
    permission_classes = [permissions.IsAuthenticated, IsWaiterOrAbove]

    def post(self, request, pk):
        try:
            order = (
                Order.objects.select_related("branch", "tenant")
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
        order.items.filter(status="PENDING").update(status="SENT")

        KitchenTicket.objects.create(
            tenant=order.tenant,
            branch=order.branch,
            order=order,
        )

        log_activity(
            actor_user=request.user,
            action="order_sent_to_kitchen",
            entity_type="order",
            entity_id=str(order.id),
            tenant=request.user.tenant,
            branch=order.branch,
        )

        order.refresh_from_db()
        return Response(
            OrderSerializer(order, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )


class OrderCancelView(APIView):
    # Only managers/owners can cancel orders
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def post(self, request, pk):
        try:
            order = Order.objects.select_related("branch").get(pk=pk, tenant=request.user.tenant)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        if order.status == Order.Status.CANCELED:
            return Response({"detail": "Order is already canceled."}, status=status.HTTP_400_BAD_REQUEST)

        if order.status == Order.Status.COMPLETED:
            return Response({"detail": "Completed orders cannot be canceled."}, status=status.HTTP_400_BAD_REQUEST)

        order.status = Order.Status.CANCELED
        order.save(update_fields=["status", "updated_at"])

        log_activity(
            actor_user=request.user,
            action="order_canceled",
            entity_type="order",
            entity_id=str(order.id),
            tenant=request.user.tenant,
            branch=order.branch,
        )

        return Response(
            OrderSerializer(order, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )


class OrderCompleteView(APIView):
    # Only managers/owners can mark orders complete
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def post(self, request, pk):
        try:
            order = Order.objects.select_related("branch").get(pk=pk, tenant=request.user.tenant)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        if order.status == Order.Status.CANCELED:
            return Response({"detail": "Canceled orders cannot be completed."}, status=status.HTTP_400_BAD_REQUEST)

        if order.status == Order.Status.COMPLETED:
            return Response({"detail": "Order is already completed."}, status=status.HTTP_400_BAD_REQUEST)

        order.status = Order.Status.COMPLETED
        order.save(update_fields=["status", "updated_at"])

        log_activity(
            actor_user=request.user,
            action="order_completed",
            entity_type="order",
            entity_id=str(order.id),
            tenant=request.user.tenant,
            branch=order.branch,
        )

        return Response(
            OrderSerializer(order, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )


class OrderItemAddView(APIView):
    # Waiters and above can add items
    permission_classes = [permissions.IsAuthenticated, IsWaiterOrAbove]

    def post(self, request, pk):
        try:
            order = Order.objects.select_related("branch").get(pk=pk, tenant=request.user.tenant)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        if order.status == Order.Status.CANCELED:
            return Response(
                {"detail": "Cannot add items to a canceled order."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = OrderItemAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = serializer.save(order=order)

        log_activity(
            actor_user=request.user,
            action="order_item_added",
            entity_type="order_item",
            entity_id=str(item.id),
            tenant=request.user.tenant,
            branch=order.branch,
        )

        return Response(OrderItemSerializer(item).data, status=status.HTTP_201_CREATED)


class OrderItemDetailView(APIView):
    # Waiters and above can update/delete items
    permission_classes = [permissions.IsAuthenticated, IsWaiterOrAbove]

    def _get_item(self, request, order_pk, item_pk):
        try:
            return OrderItem.objects.select_related("order__branch").get(
                pk=item_pk,
                order_id=order_pk,
                order__tenant=request.user.tenant,
            )
        except OrderItem.DoesNotExist:
            return None

    def patch(self, request, pk, item_pk):
        item = self._get_item(request, pk, item_pk)
        if item is None:
            return Response({"detail": "Order item not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = OrderItemUpdateSerializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        log_activity(
            actor_user=request.user,
            action="order_item_updated",
            entity_type="order_item",
            entity_id=str(item.id),
            tenant=request.user.tenant,
            branch=item.order.branch,
        )

        return Response(OrderItemSerializer(item).data, status=status.HTTP_200_OK)

    def delete(self, request, pk, item_pk):
        item = self._get_item(request, pk, item_pk)
        if item is None:
            return Response({"detail": "Order item not found."}, status=status.HTTP_404_NOT_FOUND)

        order_branch = item.order.branch
        item_id = str(item.id)
        item.delete()

        log_activity(
            actor_user=request.user,
            action="order_item_deleted",
            entity_type="order_item",
            entity_id=item_id,
            tenant=request.user.tenant,
            branch=order_branch,
        )

        return Response(status=status.HTTP_204_NO_CONTENT)


class KitchenTicketListView(generics.ListAPIView):
    serializer_class = KitchenTicketSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = (
            KitchenTicket.objects.filter(tenant=self.request.user.tenant)
            .select_related("branch", "order")
            .order_by("created_at")
        )
        params = self.request.query_params

        branch = params.get("branch")
        if branch:
            queryset = queryset.filter(branch_id=branch)

        ticket_status = params.get("status")
        if ticket_status:
            queryset = queryset.filter(status=ticket_status)

        return queryset


class KitchenTicketPreparedView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def post(self, request, pk):
        try:
            ticket = KitchenTicket.objects.select_related("branch", "order").get(
                pk=pk, tenant=request.user.tenant
            )
        except KitchenTicket.DoesNotExist:
            return Response({"detail": "Kitchen ticket not found."}, status=status.HTTP_404_NOT_FOUND)

        if ticket.status == KitchenTicket.Status.PREPARED:
            return Response({"detail": "Ticket is already marked as prepared."}, status=status.HTTP_400_BAD_REQUEST)

        ticket.status = KitchenTicket.Status.PREPARED
        ticket.save(update_fields=["status", "updated_at"])

        log_activity(
            actor_user=request.user,
            action="kitchen_ticket_prepared",
            entity_type="kitchen_ticket",
            entity_id=str(ticket.id),
            tenant=request.user.tenant,
            branch=ticket.branch,
        )

        return Response(KitchenTicketSerializer(ticket).data, status=status.HTTP_200_OK)
