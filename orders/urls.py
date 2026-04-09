from django.urls import path

from .views import (
    KitchenTicketListView,
    KitchenTicketPreparedView,
    OrderCallWaiterView,
    OrderCancelView,
    OrderCompleteView,
    OrderCourseFireView,
    OrderDetailView,
    OrderFireView,
    OrderHoldView,
    OrderItemAddView,
    OrderItemDetailView,
    OrderListCreateView,
    OrderRequestBillView,
    OrderSendToKitchenView,
)

urlpatterns = [
    # Order CRUD
    path("orders", OrderListCreateView.as_view(), name="order-list-create"),
    path("orders/<int:pk>", OrderDetailView.as_view(), name="order-detail"),
    # Order lifecycle actions
    path("orders/<int:pk>/hold", OrderHoldView.as_view(), name="order-hold"),
    path("orders/<int:pk>/fire", OrderFireView.as_view(), name="order-fire"),
    path("orders/<int:pk>/course/fire", OrderCourseFireView.as_view(), name="order-course-fire"),
    path("orders/<int:pk>/send-to-kitchen", OrderSendToKitchenView.as_view(), name="order-send-to-kitchen"),
    path("orders/<int:pk>/cancel", OrderCancelView.as_view(), name="order-cancel"),
    path("orders/<int:pk>/complete", OrderCompleteView.as_view(), name="order-complete"),
    path("orders/<int:pk>/call-waiter", OrderCallWaiterView.as_view(), name="order-call-waiter"),
    path("orders/<int:pk>/request-bill", OrderRequestBillView.as_view(), name="order-request-bill"),
    # Order items
    path("orders/<int:pk>/items", OrderItemAddView.as_view(), name="order-item-add"),
    path("orders/<int:pk>/items/<int:item_pk>", OrderItemDetailView.as_view(), name="order-item-detail"),
    # Kitchen
    path("kitchen/tickets", KitchenTicketListView.as_view(), name="kitchen-ticket-list"),
    path("kitchen/tickets/<int:pk>/prepared", KitchenTicketPreparedView.as_view(), name="kitchen-ticket-prepared"),
]
