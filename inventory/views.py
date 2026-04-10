from decimal import Decimal

from django.db.models import Count, F, Q, Sum
from django.db.models.functions import Coalesce
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import StandardResultsSetPagination
from users.audit import log_activity
from users.permissions import IsOwnerOrManager

from .models import Ingredient, RecipeComponent, StockMovement
from .serializers import (
	IngredientSerializer,
	InventoryUsageQuerySerializer,
	LowStockIngredientSerializer,
	ReceiveStockSerializer,
	RecipeComponentSerializer,
	StockMovementSerializer,
)


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


class RecipeComponentListCreateView(generics.ListCreateAPIView):
	serializer_class = RecipeComponentSerializer
	permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]
	pagination_class = StandardResultsSetPagination

	def get_queryset(self):
		queryset = (
			RecipeComponent.objects.filter(tenant=self.request.user.tenant)
			.select_related("branch", "menu_item", "ingredient")
			.order_by("id")
		)
		params = self.request.query_params

		branch = params.get("branch")
		if branch:
			queryset = queryset.filter(branch_id=branch)

		menu_item = params.get("menu_item")
		if menu_item:
			queryset = queryset.filter(menu_item_id=menu_item)

		ingredient = params.get("ingredient")
		if ingredient:
			queryset = queryset.filter(ingredient_id=ingredient)

		is_active = params.get("is_active")
		if is_active is not None:
			is_active_value = is_active.lower() in {"1", "true", "yes", "on"}
			queryset = queryset.filter(is_active=is_active_value)

		return queryset

	def perform_create(self, serializer):
		recipe = serializer.save(tenant=self.request.user.tenant)
		log_activity(
			actor_user=self.request.user,
			action="recipe_component_created",
			entity_type="recipe_component",
			entity_id=str(recipe.id),
			tenant=self.request.user.tenant,
			branch=recipe.branch,
		)


class RecipeComponentDetailView(generics.RetrieveUpdateDestroyAPIView):
	serializer_class = RecipeComponentSerializer
	permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

	def get_queryset(self):
		return RecipeComponent.objects.filter(tenant=self.request.user.tenant).select_related(
			"branch", "menu_item", "ingredient"
		)

	def perform_update(self, serializer):
		recipe = serializer.save()
		log_activity(
			actor_user=self.request.user,
			action="recipe_component_updated",
			entity_type="recipe_component",
			entity_id=str(recipe.id),
			tenant=self.request.user.tenant,
			branch=recipe.branch,
		)

	def perform_destroy(self, instance):
		log_activity(
			actor_user=self.request.user,
			action="recipe_component_deleted",
			entity_type="recipe_component",
			entity_id=str(instance.id),
			tenant=self.request.user.tenant,
			branch=instance.branch,
		)
		instance.delete()


class ReceiveStockView(APIView):
	permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

	def post(self, request):
		serializer = ReceiveStockSerializer(data=request.data, context={"request": request})
		serializer.is_valid(raise_exception=True)
		movement = serializer.save()

		log_activity(
			actor_user=request.user,
			action="stock_received",
			entity_type="stock_movement",
			entity_id=str(movement.id),
			tenant=request.user.tenant,
			branch=movement.branch,
			metadata={
				"ingredient_id": movement.ingredient_id,
				"quantity": str(movement.quantity),
				"reference": movement.reference,
			},
		)

		return Response(StockMovementSerializer(movement, context={"request": request}).data, status=status.HTTP_201_CREATED)


class InventoryUsageReportView(APIView):
	permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

	def get(self, request):
		query = InventoryUsageQuerySerializer(data=request.query_params)
		query.is_valid(raise_exception=True)
		data = query.validated_data

		movements = StockMovement.objects.filter(tenant=request.user.tenant)

		branch = data.get("branch")
		if branch:
			movements = movements.filter(branch_id=branch)

		ingredient = data.get("ingredient")
		if ingredient:
			movements = movements.filter(ingredient_id=ingredient)

		date_from = data.get("date_from")
		if date_from:
			movements = movements.filter(created_at__date__gte=date_from)

		date_to = data.get("date_to")
		if date_to:
			movements = movements.filter(created_at__date__lte=date_to)

		rows = list(
			movements.values("ingredient_id", "ingredient__name", "ingredient__unit")
			.annotate(
				movement_count=Count("id"),
				consumed_quantity=Coalesce(
					Sum("quantity", filter=Q(movement_type=StockMovement.MovementType.STOCK_OUT)),
					Decimal("0.000"),
				),
				received_quantity=Coalesce(
					Sum(
						"quantity",
						filter=Q(
							movement_type__in=[
								StockMovement.MovementType.STOCK_IN,
								StockMovement.MovementType.RECEIVING,
							]
						),
					),
					Decimal("0.000"),
				),
			)
			.order_by("-consumed_quantity", "ingredient_id")
		)

		for row in rows:
			row["net_quantity"] = row["received_quantity"] - row["consumed_quantity"]

		total_consumed = sum((row["consumed_quantity"] for row in rows), Decimal("0.000"))
		total_received = sum((row["received_quantity"] for row in rows), Decimal("0.000"))

		return Response(
			{
				"count": len(rows),
				"total_consumed": f"{total_consumed:.3f}",
				"total_received": f"{total_received:.3f}",
				"results": [
					{
						"ingredient": row["ingredient_id"],
						"ingredient_name": row["ingredient__name"],
						"unit": row["ingredient__unit"],
						"movement_count": row["movement_count"],
						"consumed_quantity": f"{row['consumed_quantity']:.3f}",
						"received_quantity": f"{row['received_quantity']:.3f}",
						"net_quantity": f"{row['net_quantity']:.3f}",
					}
					for row in rows
				],
			}
		)
