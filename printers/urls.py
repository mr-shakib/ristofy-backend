from django.urls import path

from .views import (
    PrintJobDetailView,
    PrintJobListView,
    PrintJobReprintView,
    PrinterDetailView,
    PrinterListCreateView,
    PrinterRouteRuleDetailView,
    PrinterRouteRuleListCreateView,
)

urlpatterns = [
    path("printers", PrinterListCreateView.as_view(), name="printers-list-create"),
    path("printers/<int:pk>", PrinterDetailView.as_view(), name="printers-detail"),
    path("printer-routes", PrinterRouteRuleListCreateView.as_view(), name="printer-routes-list-create"),
    path("printer-routes/<int:pk>", PrinterRouteRuleDetailView.as_view(), name="printer-routes-detail"),
    path("print-jobs", PrintJobListView.as_view(), name="print-jobs-list"),
    path("print-jobs/<int:pk>", PrintJobDetailView.as_view(), name="print-jobs-detail"),
    path("print-jobs/reprint-ticket", PrintJobReprintView.as_view(), name="print-jobs-reprint"),
]
