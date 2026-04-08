from django.urls import path

from .views import (
    AllergenDetailView,
    AllergenListCreateView,
    MenuCategoryDetailView,
    MenuCategoryListCreateView,
    MenuItemDetailView,
    MenuItemListCreateView,
    MenuScheduleDetailView,
    MenuScheduleListCreateView,
)

urlpatterns = [
    path("menu/allergens", AllergenListCreateView.as_view(), name="menu-allergens-list-create"),
    path("menu/allergens/<int:pk>", AllergenDetailView.as_view(), name="menu-allergens-detail"),
    path("menu/categories", MenuCategoryListCreateView.as_view(), name="menu-categories-list-create"),
    path("menu/categories/<int:pk>", MenuCategoryDetailView.as_view(), name="menu-categories-detail"),
    path("menu/items", MenuItemListCreateView.as_view(), name="menu-items-list-create"),
    path("menu/items/<int:pk>", MenuItemDetailView.as_view(), name="menu-items-detail"),
    path("menu/schedules", MenuScheduleListCreateView.as_view(), name="menu-schedules-list-create"),
    path("menu/schedules/<int:pk>", MenuScheduleDetailView.as_view(), name="menu-schedules-detail"),
]
