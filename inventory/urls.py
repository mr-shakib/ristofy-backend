from django.urls import path

from .views import (
    IngredientDetailView,
    IngredientListCreateView,
    InventoryUsageReportView,
    LowStockReportView,
    ReceiveStockView,
    RecipeComponentDetailView,
    RecipeComponentListCreateView,
    StockMovementListCreateView,
)

urlpatterns = [
    path("inventory/ingredients", IngredientListCreateView.as_view(), name="inventory-ingredients-list-create"),
    path("inventory/ingredients/<int:pk>", IngredientDetailView.as_view(), name="inventory-ingredients-detail"),
    path("inventory/recipes", RecipeComponentListCreateView.as_view(), name="inventory-recipe-list-create"),
    path("inventory/recipes/<int:pk>", RecipeComponentDetailView.as_view(), name="inventory-recipe-detail"),
    path("inventory/movements", StockMovementListCreateView.as_view(), name="inventory-movements-list-create"),
    path("inventory/receivings", ReceiveStockView.as_view(), name="inventory-receiving-create"),
    path("inventory/reports/low-stock", LowStockReportView.as_view(), name="inventory-low-stock-report"),
    path("inventory/reports/usage", InventoryUsageReportView.as_view(), name="inventory-usage-report"),
]
