from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import StandardResultsSetPagination
from users.audit import log_activity
from users.permissions import IsOwnerOrManager, IsWaiterOrAbove

from .events import (
    ORDER_CANCELED,
    ORDER_COMPLETED,
    ORDER_FIRED,
    ORDER_HELD,
    ORDER_UPDATED,
    TICKET_PRINT_REQUESTED,
    publish_order_event,
)
from .models import KitchenTicket, Order, OrderItem
from .serializers import (
    KitchenTicketSerializer,
    OrderCreateSerializer,
    OrderItemAddSerializer,
    OrderItemSerializer,
    OrderItemUpdateSerializer,
    OrderSerializer,
)
from .services import fire_order_items


# ─── Order list/create ────────────────────────────────────────────────────────

class OrderListCreateView(generics.ListCreateAPIView):
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


# ─── Order detail/update ──────────────────────────────────────────────────────

class OrderDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = OrderSerializer
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
        publish_order_event(ORDER_UPDATED, order, status=order.status)


# ─── Order status actions ─────────────────────────────────────────────────────

class OrderHoldView(APIView):
    """Hold a taken order before sending to kitchen."""
    permission_classes = [permissions.IsAuthenticated, IsWaiterOrAbove]

    def post(self, request, pk):
        try:
            order = Order.objects.select_related("branch", "tenant").get(pk=pk, tenant=request.user.tenant)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        if order.is_terminal:
            return Response(
                {"detail": "Cannot hold a completed or canceled order."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if order.status not in {Order.Status.OPEN}:
            return Response(
                {"detail": f"Cannot hold an order with status '{order.status}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.status = Order.Status.HELD
        order.save(update_fields=["status", "updated_at"])

        log_activity(
            actor_user=request.user,
            action="order_held",
            entity_type="order",
            entity_id=str(order.id),
            tenant=request.user.tenant,
            branch=order.branch,
        )
        publish_order_event(ORDER_HELD, order)

        return Response(OrderSerializer(order, context={"request": request}).data, status=status.HTTP_200_OK)


class OrderFireView(APIView):
    """Fire all pending items in the order to the kitchen (one ticket per course)."""
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

        if order.is_terminal:
            return Response(
                {"detail": "Cannot fire a completed or canceled order."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tickets = fire_order_items(order)

        if not tickets:
            return Response(
                {"detail": "No pending items to fire."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.status = Order.Status.SENT_TO_KITCHEN
        order.save(update_fields=["status", "updated_at"])

        log_activity(
            actor_user=request.user,
            action="order_fired",
            entity_type="order",
            entity_id=str(order.id),
            tenant=request.user.tenant,
            branch=order.branch,
        )
        publish_order_event(ORDER_FIRED, order, tickets=[t.id for t in tickets])

        order.refresh_from_db()
        return Response(OrderSerializer(order, context={"request": request}).data, status=status.HTTP_200_OK)


class OrderCourseFireView(APIView):
    """Fire all pending items for a specific course."""
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

        if order.is_terminal:
            return Response(
                {"detail": "Cannot fire a completed or canceled order."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        course = request.data.get("course")
        valid_courses = {c.value for c in OrderItem.Course}
        if not course or course not in valid_courses:
            return Response(
                {"detail": f"'course' is required. Valid values: {sorted(valid_courses)}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tickets = fire_order_items(order, course=course)

        if not tickets:
            return Response(
                {"detail": f"No pending items found for course '{course}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Move to SENT_TO_KITCHEN if still OPEN/HELD
        if order.status in {Order.Status.OPEN, Order.Status.HELD}:
            order.status = Order.Status.SENT_TO_KITCHEN
            order.save(update_fields=["status", "updated_at"])

        log_activity(
            actor_user=request.user,
            action="order_course_fired",
            entity_type="order",
            entity_id=str(order.id),
            tenant=request.user.tenant,
            branch=order.branch,
        )
        publish_order_event(ORDER_FIRED, order, course=course, tickets=[t.id for t in tickets])

        order.refresh_from_db()
        return Response(OrderSerializer(order, context={"request": request}).data, status=status.HTTP_200_OK)


class OrderSendToKitchenView(APIView):
    """Legacy alias for fire — kept for backward compatibility."""
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

        fire_order_items(order)

        order.status = Order.Status.SENT_TO_KITCHEN
        order.save(update_fields=["status", "updated_at"])

        log_activity(
            actor_user=request.user,
            action="order_sent_to_kitchen",
            entity_type="order",
            entity_id=str(order.id),
            tenant=request.user.tenant,
            branch=order.branch,
        )
        publish_order_event(ORDER_FIRED, order)

        order.refresh_from_db()
        return Response(OrderSerializer(order, context={"request": request}).data, status=status.HTTP_200_OK)


class OrderCancelView(APIView):
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
        publish_order_event(ORDER_CANCELED, order)

        return Response(OrderSerializer(order, context={"request": request}).data, status=status.HTTP_200_OK)


class OrderCompleteView(APIView):
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
        publish_order_event(ORDER_COMPLETED, order)

        return Response(OrderSerializer(order, context={"request": request}).data, status=status.HTTP_200_OK)


class OrderCallWaiterView(APIView):
    """Signal that a waiter is needed at the table. Logs the event; no order state change."""
    permission_classes = [permissions.IsAuthenticated, IsWaiterOrAbove]

    def post(self, request, pk):
        try:
            order = Order.objects.select_related("branch").get(pk=pk, tenant=request.user.tenant)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        if order.is_terminal:
            return Response(
                {"detail": "Cannot call waiter for a completed or canceled order."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        log_activity(
            actor_user=request.user,
            action="call_waiter",
            entity_type="order",
            entity_id=str(order.id),
            tenant=request.user.tenant,
            branch=order.branch,
        )
        publish_order_event("order.call_waiter", order)

        return Response({"detail": "Waiter call registered."}, status=status.HTTP_200_OK)


class OrderRequestBillView(APIView):
    """Signal that the customer wants the bill. Sets table state to WAITING_BILL if table assigned."""
    permission_classes = [permissions.IsAuthenticated, IsWaiterOrAbove]

    def post(self, request, pk):
        try:
            order = Order.objects.select_related("branch", "table").get(pk=pk, tenant=request.user.tenant)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        if order.is_terminal:
            return Response(
                {"detail": "Cannot request bill for a completed or canceled order."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Sync table state to WAITING_BILL if a table is assigned
        if order.table:
            from tables.models import DiningTable
            order.table.state = DiningTable.State.WAITING_BILL
            order.table.save(update_fields=["state", "updated_at"])

        log_activity(
            actor_user=request.user,
            action="request_bill",
            entity_type="order",
            entity_id=str(order.id),
            tenant=request.user.tenant,
            branch=order.branch,
        )
        publish_order_event("order.bill_requested", order)

        return Response({"detail": "Bill request registered."}, status=status.HTTP_200_OK)


# ─── Order items ──────────────────────────────────────────────────────────────

class OrderItemAddView(APIView):
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


# ─── Kitchen tickets ──────────────────────────────────────────────────────────

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

        course = params.get("course")
        if course:
            queryset = queryset.filter(course=course)

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
        publish_order_event(TICKET_PRINT_REQUESTED, ticket.order, ticket_id=ticket.id)

        return Response(KitchenTicketSerializer(ticket).data, status=status.HTTP_200_OK)
