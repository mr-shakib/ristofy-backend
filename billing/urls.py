from django.urls import path

from .views import (
    BillApplyCopertoView,
    BillApplyDiscountView,
    BillCreateFromOrderView,
    BillDetailView,
    BillFinalizeView,
    BillPayView,
)


urlpatterns = [
    path("bills/create-from-order", BillCreateFromOrderView.as_view(), name="bill-create-from-order"),
    path("bills/<int:pk>", BillDetailView.as_view(), name="bill-detail"),
    path("bills/<int:pk>/apply-coperto", BillApplyCopertoView.as_view(), name="bill-apply-coperto"),
    path("bills/<int:pk>/apply-discount", BillApplyDiscountView.as_view(), name="bill-apply-discount"),
    path("bills/<int:pk>/finalize", BillFinalizeView.as_view(), name="bill-finalize"),
    path("bills/<int:pk>/pay", BillPayView.as_view(), name="bill-pay"),
]