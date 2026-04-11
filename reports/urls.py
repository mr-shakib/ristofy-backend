from django.urls import path

from .views import (
    BuffetBranchComparisonView,
    DailyReportSnapshotListView,
    DailyReportSnapshotRefreshView,
    ReportCacheInvalidateView,
    SalesByCategoryView,
    SalesByTableView,
    SalesByVatView,
    SalesByWaiterView,
)


urlpatterns = [
    path("reports/snapshots", DailyReportSnapshotListView.as_view(), name="report-snapshot-list"),
    path("reports/snapshots/refresh", DailyReportSnapshotRefreshView.as_view(), name="report-snapshot-refresh"),
    path("reports/sales/by-category", SalesByCategoryView.as_view(), name="report-sales-by-category"),
    path("reports/sales/by-table", SalesByTableView.as_view(), name="report-sales-by-table"),
    path("reports/sales/by-waiter", SalesByWaiterView.as_view(), name="report-sales-by-waiter"),
    path("reports/sales/by-vat", SalesByVatView.as_view(), name="report-sales-by-vat"),
    path("reports/buffet/branch-comparison", BuffetBranchComparisonView.as_view(), name="report-buffet-branch-comparison"),
    path("reports/cache/invalidate", ReportCacheInvalidateView.as_view(), name="report-cache-invalidate"),
]
