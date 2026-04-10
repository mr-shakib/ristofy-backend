from django.db.models import F
from rest_framework import generics, permissions

from core.pagination import StandardResultsSetPagination
from users.audit import log_activity
from users.permissions import IsOwnerOrManager

from .models import Ingredient, StockMovement
from .serializers import IngredientSerializer, LowStockIngredientSerializer, StockMovementSerializer


class IngredientListCreateView(generics.ListCreateAPIView):
	serializer_class = IngredientSerializer
	permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]
	pagination_class = StandardResultsSetPagination

	def get_queryset(self):
		queryset = Ingredient.objects.filter(tenant=self.request.user.tenant).select_related("branch").order_by("id")
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
		ingredient = serializer.save(tenant=self.request.user.tenant)
		log_activity(
			actor_user=self.request.user,
			action="ingredient_created",
			entity_type="ingredient",
			entity_id=str(ingredient.id),
			tenant=self.request.user.tenant,
			branch=ingredient.branch,
		)


class IngredientDetailView(generics.RetrieveUpdateDestroyAPIView):
	serializer_class = IngredientSerializer
	permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

	def get_queryset(self):
		return Ingredient.objects.filter(tenant=self.request.user.tenant).select_related("branch")

	def perform_update(self, serializer):
		ingredient = serializer.save()
		log_activity(
			actor_user=self.request.user,
			action="ingredient_updated",
			entity_type="ingredient",
			entity_id=str(ingredient.id),
			tenant=self.request.user.tenant,
			branch=ingredient.branch,
		)

	def perform_destroy(self, instance):
		log_activity(
			actor_user=self.request.user,
			action="ingredient_deleted",
			entity_type="ingredient",
			entity_id=str(instance.id),
			tenant=self.request.user.tenant,
			branch=instance.branch,
		)
		instance.delete()


class StockMovementListCreateView(generics.ListCreateAPIView):
	serializer_class = StockMovementSerializer
	permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]
	pagination_class = StandardResultsSetPagination

	def get_queryset(self):
		queryset = (
			StockMovement.objects.filter(tenant=self.request.user.tenant)
			.select_related("branch", "ingredient", "created_by")
			.order_by("-id")
		)
		params = self.request.query_params

		branch = params.get("branch")
		if branch:
			queryset = queryset.filter(branch_id=branch)

		ingredient = params.get("ingredient")
		if ingredient:
			queryset = queryset.filter(ingredient_id=ingredient)

		movement_type = params.get("movement_type")
		if movement_type:
			queryset = queryset.filter(movement_type=movement_type)

		return queryset

	def perform_create(self, serializer):
		movement = serializer.save()
		log_activity(
			actor_user=self.request.user,
			action="stock_movement_recorded",
			entity_type="stock_movement",
			entity_id=str(movement.id),
			tenant=self.request.user.tenant,
			branch=movement.branch,
			metadata={
				"ingredient_id": movement.ingredient_id,
				"movement_type": movement.movement_type,
				"quantity": str(movement.quantity),
				"stock_before": str(movement.stock_before),
				"stock_after": str(movement.stock_after),
			},
		)


class LowStockReportView(generics.ListAPIView):
	serializer_class = LowStockIngredientSerializer
	permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]
	pagination_class = StandardResultsSetPagination

	def get_queryset(self):
		queryset = (
			Ingredient.objects.filter(
				tenant=self.request.user.tenant,
				is_active=True,
				current_stock__lte=F("min_stock_level"),
			)
			.select_related("branch")
			.order_by("current_stock", "id")
		)
		branch = self.request.query_params.get("branch")
		if branch:
			queryset = queryset.filter(branch_id=branch)
		return queryset
