from django.db.models import Q
from rest_framework import generics, permissions

from core.pagination import StandardResultsSetPagination
from users.audit import log_activity
from users.permissions import IsOwnerOrManager

from .models import Allergen, MenuCategory, MenuItem, MenuSchedule
from .serializers import AllergenSerializer, MenuCategorySerializer, MenuItemSerializer, MenuScheduleSerializer


class AllergenListCreateView(generics.ListCreateAPIView):
    serializer_class = AllergenSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = Allergen.objects.all().order_by("id")
        q = self.request.query_params.get("q")
        if q:
            queryset = queryset.filter(Q(name_en__icontains=q) | Q(name_it__icontains=q) | Q(code__icontains=q))
        return queryset


class AllergenDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AllergenSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]
    queryset = Allergen.objects.all().order_by("id")


class MenuCategoryListCreateView(generics.ListCreateAPIView):
    serializer_class = MenuCategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = MenuCategory.objects.filter(tenant=self.request.user.tenant).select_related("branch").order_by("id")
        params = self.request.query_params

        branch = params.get("branch")
        if branch:
            queryset = queryset.filter(branch_id=branch)

        is_active = params.get("is_active")
        if is_active is not None:
            is_active_value = is_active.lower() in {"1", "true", "yes", "on"}
            queryset = queryset.filter(is_active=is_active_value)

        q = params.get("q")
        if q:
            queryset = queryset.filter(name__icontains=q)

        return queryset

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


class MenuCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MenuCategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def get_queryset(self):
        return MenuCategory.objects.filter(tenant=self.request.user.tenant).select_related("branch")

    def perform_update(self, serializer):
        category = serializer.save()
        log_activity(
            actor_user=self.request.user,
            action="menu_category_updated",
            entity_type="menu_category",
            entity_id=str(category.id),
            tenant=self.request.user.tenant,
            branch=category.branch,
        )

    def perform_destroy(self, instance):
        log_activity(
            actor_user=self.request.user,
            action="menu_category_deleted",
            entity_type="menu_category",
            entity_id=str(instance.id),
            tenant=self.request.user.tenant,
            branch=instance.branch,
        )
        instance.delete()


class MenuItemListCreateView(generics.ListCreateAPIView):
    serializer_class = MenuItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = (
            MenuItem.objects.filter(tenant=self.request.user.tenant)
            .select_related("branch", "category")
            .prefetch_related("allergens")
            .order_by("id")
        )
        params = self.request.query_params

        branch = params.get("branch")
        if branch:
            queryset = queryset.filter(branch_id=branch)

        category = params.get("category")
        if category:
            queryset = queryset.filter(category_id=category)

        is_active = params.get("is_active")
        if is_active is not None:
            is_active_value = is_active.lower() in {"1", "true", "yes", "on"}
            queryset = queryset.filter(is_active=is_active_value)

        min_price = params.get("min_price")
        if min_price:
            queryset = queryset.filter(base_price__gte=min_price)

        max_price = params.get("max_price")
        if max_price:
            queryset = queryset.filter(base_price__lte=max_price)

        q = params.get("q")
        if q:
            queryset = queryset.filter(name__icontains=q)

        return queryset

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


class MenuItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MenuItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def get_queryset(self):
        return (
            MenuItem.objects.filter(tenant=self.request.user.tenant)
            .select_related("branch", "category")
            .prefetch_related("allergens")
        )

    def perform_update(self, serializer):
        item = serializer.save()
        log_activity(
            actor_user=self.request.user,
            action="menu_item_updated",
            entity_type="menu_item",
            entity_id=str(item.id),
            tenant=self.request.user.tenant,
            branch=item.branch,
        )

    def perform_destroy(self, instance):
        log_activity(
            actor_user=self.request.user,
            action="menu_item_deleted",
            entity_type="menu_item",
            entity_id=str(instance.id),
            tenant=self.request.user.tenant,
            branch=instance.branch,
        )
        instance.delete()


class MenuScheduleListCreateView(generics.ListCreateAPIView):
    serializer_class = MenuScheduleSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = (
            MenuSchedule.objects.filter(tenant=self.request.user.tenant)
            .select_related("branch", "menu_item")
            .order_by("id")
        )
        params = self.request.query_params

        branch = params.get("branch")
        if branch:
            queryset = queryset.filter(branch_id=branch)

        menu_item = params.get("menu_item")
        if menu_item:
            queryset = queryset.filter(menu_item_id=menu_item)

        day_of_week = params.get("day_of_week")
        if day_of_week:
            queryset = queryset.filter(day_of_week=day_of_week)

        is_active = params.get("is_active")
        if is_active is not None:
            is_active_value = is_active.lower() in {"1", "true", "yes", "on"}
            queryset = queryset.filter(is_active=is_active_value)

        return queryset

    def perform_create(self, serializer):
        schedule = serializer.save(tenant=self.request.user.tenant)
        log_activity(
            actor_user=self.request.user,
            action="menu_schedule_created",
            entity_type="menu_schedule",
            entity_id=str(schedule.id),
            tenant=self.request.user.tenant,
            branch=schedule.branch,
        )


class MenuScheduleDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MenuScheduleSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def get_queryset(self):
        return MenuSchedule.objects.filter(tenant=self.request.user.tenant).select_related("branch", "menu_item")

    def perform_update(self, serializer):
        schedule = serializer.save()
        log_activity(
            actor_user=self.request.user,
            action="menu_schedule_updated",
            entity_type="menu_schedule",
            entity_id=str(schedule.id),
            tenant=self.request.user.tenant,
            branch=schedule.branch,
        )

    def perform_destroy(self, instance):
        log_activity(
            actor_user=self.request.user,
            action="menu_schedule_deleted",
            entity_type="menu_schedule",
            entity_id=str(instance.id),
            tenant=self.request.user.tenant,
            branch=instance.branch,
        )
        instance.delete()
