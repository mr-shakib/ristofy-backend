from django.urls import path

from .views import MenuCategoryDetailView, MenuCategoryListCreateView, MenuItemDetailView, MenuItemListCreateView

urlpatterns = [
    path("menu/categories", MenuCategoryListCreateView.as_view(), name="menu-categories-list-create"),
    path("menu/categories/<int:pk>", MenuCategoryDetailView.as_view(), name="menu-categories-detail"),
    path("menu/items", MenuItemListCreateView.as_view(), name="menu-items-list-create"),
    path("menu/items/<int:pk>", MenuItemDetailView.as_view(), name="menu-items-detail"),
]
