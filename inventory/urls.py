from django.urls import path

from .views import (
    IngredientDetailView,
    IngredientListCreateView,
    LowStockReportView,
    StockMovementListCreateView,
)

urlpatterns = [
    path("inventory/ingredients", IngredientListCreateView.as_view(), name="inventory-ingredients-list-create"),
    path("inventory/ingredients/<int:pk>", IngredientDetailView.as_view(), name="inventory-ingredients-detail"),
    path("inventory/movements", StockMovementListCreateView.as_view(), name="inventory-movements-list-create"),
    path("inventory/reports/low-stock", LowStockReportView.as_view(), name="inventory-low-stock-report"),
]
