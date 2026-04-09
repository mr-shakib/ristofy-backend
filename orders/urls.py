from django.urls import path

from .views import (
    KitchenTicketListView,
    KitchenTicketPreparedView,
    OrderCancelView,
    OrderCompleteView,
    OrderDetailView,
    OrderItemAddView,
    OrderItemDetailView,
    OrderListCreateView,
    OrderSendToKitchenView,
)

urlpatterns = [
    path("orders", OrderListCreateView.as_view(), name="order-list-create"),
    path("orders/<int:pk>", OrderDetailView.as_view(), name="order-detail"),
    path("orders/<int:pk>/send-to-kitchen", OrderSendToKitchenView.as_view(), name="order-send-to-kitchen"),
    path("orders/<int:pk>/cancel", OrderCancelView.as_view(), name="order-cancel"),
    path("orders/<int:pk>/complete", OrderCompleteView.as_view(), name="order-complete"),
    path("orders/<int:pk>/items", OrderItemAddView.as_view(), name="order-item-add"),
    path("orders/<int:pk>/items/<int:item_pk>", OrderItemDetailView.as_view(), name="order-item-detail"),
    path("kitchen/tickets", KitchenTicketListView.as_view(), name="kitchen-ticket-list"),
    path("kitchen/tickets/<int:pk>/prepared", KitchenTicketPreparedView.as_view(), name="kitchen-ticket-prepared"),
]
