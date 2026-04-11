from django.urls import path

from .views import (
    BillApplyCopertoView,
    BillApplyDiscountView,
    BillCreateFromOrderView,
    BillDetailView,
    BillFinalizeView,
    BillPayView,
    BillSendToFiscalView,
    BillSplitView,
    BridgeFiscalAckView,
    FiscalZReportStatusView,
    FiscalZReportSyncView,
    ReceiptDetailView,
    ReceiptRefundView,
    ReceiptReprintView,
)


urlpatterns = [
    path("bills/create-from-order", BillCreateFromOrderView.as_view(), name="bill-create-from-order"),
    path("bills/<int:pk>", BillDetailView.as_view(), name="bill-detail"),
    path("bills/<int:pk>/apply-coperto", BillApplyCopertoView.as_view(), name="bill-apply-coperto"),
    path("bills/<int:pk>/apply-discount", BillApplyDiscountView.as_view(), name="bill-apply-discount"),
    path("bills/<int:pk>/finalize", BillFinalizeView.as_view(), name="bill-finalize"),
    path("bills/<int:pk>/pay", BillPayView.as_view(), name="bill-pay"),
    path("bills/<int:pk>/send-to-fiscal", BillSendToFiscalView.as_view(), name="bill-send-to-fiscal"),
    path("bills/<int:pk>/split", BillSplitView.as_view(), name="bill-split"),
    path("receipts/<int:pk>", ReceiptDetailView.as_view(), name="receipt-detail"),
    path("receipts/<int:pk>/reprint", ReceiptReprintView.as_view(), name="receipt-reprint"),
    path("receipts/<int:pk>/refund", ReceiptRefundView.as_view(), name="receipt-refund"),
    path("fiscal/z-report/status", FiscalZReportStatusView.as_view(), name="fiscal-z-report-status"),
    path("fiscal/z-report/sync", FiscalZReportSyncView.as_view(), name="fiscal-z-report-sync"),
    path("integrations/bridge/fiscal-ack", BridgeFiscalAckView.as_view(), name="bridge-fiscal-ack"),
]