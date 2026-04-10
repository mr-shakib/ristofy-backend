from django.contrib import admin

from .models import Ingredient, RecipeComponent, StockMovement


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
	list_display = ("id", "name", "tenant", "branch", "unit", "current_stock", "min_stock_level", "is_active")
	list_filter = ("tenant", "branch", "unit", "is_active")
	search_fields = ("name", "sku")


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
	list_display = (
		"id",
		"ingredient",
		"movement_type",
		"quantity",
		"stock_before",
		"stock_after",
		"tenant",
		"branch",
		"created_at",
	)
	list_filter = ("tenant", "branch", "movement_type")
	search_fields = ("ingredient__name", "reference", "reason")


@admin.register(RecipeComponent)
class RecipeComponentAdmin(admin.ModelAdmin):
	list_display = ("id", "menu_item", "ingredient", "quantity", "tenant", "branch", "is_active")
	list_filter = ("tenant", "branch", "is_active")
	search_fields = ("menu_item__name", "ingredient__name")
