from django.urls import path

from .views import OrderDetailView, OrderListCreateView, OrderSendToKitchenView

urlpatterns = [
    path("orders", OrderListCreateView.as_view(), name="order-list-create"),
    path("orders/<int:pk>", OrderDetailView.as_view(), name="order-detail"),
    path("orders/<int:pk>/send-to-kitchen", OrderSendToKitchenView.as_view(), name="order-send-to-kitchen"),
]
