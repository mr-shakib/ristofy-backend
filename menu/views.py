from rest_framework import generics, permissions

from users.audit import log_activity
from users.permissions import IsOwnerOrManager

from .models import MenuCategory, MenuItem
from .serializers import MenuCategorySerializer, MenuItemSerializer


class MenuCategoryListCreateView(generics.ListCreateAPIView):
    serializer_class = MenuCategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def get_queryset(self):
        return MenuCategory.objects.filter(tenant=self.request.user.tenant).select_related("branch")

    def perform_create(self, serializer):
        category = serializer.save(tenant=self.request.user.tenant)
        log_activity(
            actor_user=self.request.user,
            action="menu_category_created",
            entity_type="menu_category",
            entity_id=str(category.id),
            tenant=self.request.user.tenant,
            branch=category.branch,
        )


class MenuItemListCreateView(generics.ListCreateAPIView):
    serializer_class = MenuItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def get_queryset(self):
        return MenuItem.objects.filter(tenant=self.request.user.tenant).select_related("branch", "category")

    def perform_create(self, serializer):
        item = serializer.save(tenant=self.request.user.tenant)
        log_activity(
            actor_user=self.request.user,
            action="menu_item_created",
            entity_type="menu_item",
            entity_id=str(item.id),
            tenant=self.request.user.tenant,
            branch=item.branch,
        )
