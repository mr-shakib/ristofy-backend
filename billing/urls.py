from django.urls import path

from .views import BillCreateFromOrderView, BillDetailView


urlpatterns = [
    path("bills/create-from-order", BillCreateFromOrderView.as_view(), name="bill-create-from-order"),
    path("bills/<int:pk>", BillDetailView.as_view(), name="bill-detail"),
]