from django.urls import path

from .views import (
    AddonGroupDetailView,
    AddonGroupListCreateView,
    AddonItemDetailView,
    AddonItemListCreateView,
    AllergenDetailView,
    AllergenListCreateView,
    CustomerMenuView,
    MenuCategoryDetailView,
    MenuCategoryListCreateView,
    MenuItemDetailView,
    MenuItemListCreateView,
    MenuScheduleDetailView,
    MenuScheduleListCreateView,
    MenuVariantDetailView,
    MenuVariantListCreateView,
)

urlpatterns = [
    path("menu/allergens", AllergenListCreateView.as_view(), name="menu-allergens-list-create"),
    path("menu/allergens/<int:pk>", AllergenDetailView.as_view(), name="menu-allergens-detail"),
    path("menu/categories", MenuCategoryListCreateView.as_view(), name="menu-categories-list-create"),
    path("menu/categories/<int:pk>", MenuCategoryDetailView.as_view(), name="menu-categories-detail"),
    path("menu/items", MenuItemListCreateView.as_view(), name="menu-items-list-create"),
    path("menu/items/<int:pk>", MenuItemDetailView.as_view(), name="menu-items-detail"),
    path("menu/items/<int:item_pk>/variants", MenuVariantListCreateView.as_view(), name="menu-item-variants"),
    path("menu/variants/<int:pk>", MenuVariantDetailView.as_view(), name="menu-variant-detail"),
    path("menu/items/<int:item_pk>/addon-groups", AddonGroupListCreateView.as_view(), name="menu-item-addon-groups"),
    path("menu/addon-groups/<int:pk>", AddonGroupDetailView.as_view(), name="menu-addon-group-detail"),
    path("menu/addon-groups/<int:group_pk>/items", AddonItemListCreateView.as_view(), name="menu-addon-items"),
    path("menu/addon-items/<int:pk>", AddonItemDetailView.as_view(), name="menu-addon-item-detail"),
    path("menu/schedules", MenuScheduleListCreateView.as_view(), name="menu-schedules-list-create"),
    path("menu/schedules/<int:pk>", MenuScheduleDetailView.as_view(), name="menu-schedules-detail"),
    path("customer/menu", CustomerMenuView.as_view(), name="customer-menu"),
]
