from django.urls import path

from .views import MenuCategoryListCreateView, MenuItemListCreateView

urlpatterns = [
    path("menu/categories", MenuCategoryListCreateView.as_view(), name="menu-categories-list-create"),
    path("menu/items", MenuItemListCreateView.as_view(), name="menu-items-list-create"),
]
