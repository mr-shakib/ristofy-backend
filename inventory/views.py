from decimal import Decimal

from django.db.models import Count, F, Q, Sum
from django.db.models.functions import Coalesce
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import StandardResultsSetPagination
from users.audit import log_activity
from users.permissions import IsOwnerOrManager

from .models import Ingredient, PurchaseOrder, PurchaseOrderItem, RecipeComponent, StockMovement, Supplier
from .serializers import (
	IngredientSerializer,
	InventoryUsageQuerySerializer,
	LowStockIngredientSerializer,
	PurchaseOrderReceiveSerializer,
	PurchaseOrderSerializer,
	ReceiveStockSerializer,
	RecipeComponentSerializer,
	StockMovementSerializer,
	SupplierSerializer,
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


class SupplierListCreateView(generics.ListCreateAPIView):
	serializer_class = SupplierSerializer
	permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]
	pagination_class = StandardResultsSetPagination

	def get_queryset(self):
		queryset = Supplier.objects.filter(tenant=self.request.user.tenant).select_related("branch").order_by("name")
		params = self.request.query_params
		branch = params.get("branch")
		if branch:
			queryset = queryset.filter(branch_id=branch)
		q = params.get("q")
		if q:
			queryset = queryset.filter(name__icontains=q)
		is_active = params.get("is_active")
		if is_active is not None:
			queryset = queryset.filter(is_active=is_active.lower() in {"1", "true", "yes"})
		return queryset

	def perform_create(self, serializer):
		supplier = serializer.save(tenant=self.request.user.tenant)
		log_activity(
			actor_user=self.request.user,
			action="supplier_created",
			entity_type="supplier",
			entity_id=str(supplier.id),
			tenant=self.request.user.tenant,
			branch=supplier.branch,
		)


class SupplierDetailView(generics.RetrieveUpdateDestroyAPIView):
	serializer_class = SupplierSerializer
	permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

	def get_queryset(self):
		return Supplier.objects.filter(tenant=self.request.user.tenant).select_related("branch")

	def perform_update(self, serializer):
		supplier = serializer.save()
		log_activity(
			actor_user=self.request.user,
			action="supplier_updated",
			entity_type="supplier",
			entity_id=str(supplier.id),
			tenant=self.request.user.tenant,
			branch=supplier.branch,
		)

	def perform_destroy(self, instance):
		log_activity(
			actor_user=self.request.user,
			action="supplier_deleted",
			entity_type="supplier",
			entity_id=str(instance.id),
			tenant=self.request.user.tenant,
			branch=instance.branch,
		)
		instance.delete()


class PurchaseOrderListCreateView(generics.ListCreateAPIView):
	serializer_class = PurchaseOrderSerializer
	permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]
	pagination_class = StandardResultsSetPagination

	def get_queryset(self):
		queryset = (
			PurchaseOrder.objects.filter(tenant=self.request.user.tenant)
			.select_related("branch", "supplier", "created_by")
			.prefetch_related("items__ingredient")
			.order_by("-created_at")
		)
		params = self.request.query_params
		branch = params.get("branch")
		if branch:
			queryset = queryset.filter(branch_id=branch)
		supplier = params.get("supplier")
		if supplier:
			queryset = queryset.filter(supplier_id=supplier)
		po_status = params.get("status")
		if po_status:
			queryset = queryset.filter(status=po_status)
		return queryset

	def perform_create(self, serializer):
		po = serializer.save(tenant=self.request.user.tenant, created_by=self.request.user)
		log_activity(
			actor_user=self.request.user,
			action="purchase_order_created",
			entity_type="purchase_order",
			entity_id=str(po.id),
			tenant=self.request.user.tenant,
			branch=po.branch,
		)


class PurchaseOrderDetailView(generics.RetrieveUpdateDestroyAPIView):
	serializer_class = PurchaseOrderSerializer
	permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

	def get_queryset(self):
		return (
			PurchaseOrder.objects.filter(tenant=self.request.user.tenant)
			.select_related("branch", "supplier", "created_by")
			.prefetch_related("items__ingredient")
		)

	def perform_update(self, serializer):
		po = serializer.save()
		log_activity(
			actor_user=self.request.user,
			action="purchase_order_updated",
			entity_type="purchase_order",
			entity_id=str(po.id),
			tenant=self.request.user.tenant,
			branch=po.branch,
		)

	def perform_destroy(self, instance):
		if instance.status not in {PurchaseOrder.Status.DRAFT, PurchaseOrder.Status.CANCELED}:
			from rest_framework.exceptions import ValidationError
			raise ValidationError("Only draft or canceled purchase orders can be deleted.")
		log_activity(
			actor_user=self.request.user,
			action="purchase_order_deleted",
			entity_type="purchase_order",
			entity_id=str(instance.id),
			tenant=self.request.user.tenant,
			branch=instance.branch,
		)
		instance.delete()


class PurchaseOrderReceiveView(APIView):
	permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

	def post(self, request, pk):
		try:
			po = (
				PurchaseOrder.objects.select_related("branch", "tenant")
				.prefetch_related("items__ingredient")
				.get(pk=pk, tenant=request.user.tenant)
			)
		except PurchaseOrder.DoesNotExist:
			return Response({"detail": "Purchase order not found."}, status=status.HTTP_404_NOT_FOUND)

		if po.status == PurchaseOrder.Status.CANCELED:
			return Response({"detail": "Canceled purchase orders cannot be received."}, status=status.HTTP_400_BAD_REQUEST)
		if po.status == PurchaseOrder.Status.RECEIVED:
			return Response({"detail": "Purchase order is already fully received."}, status=status.HTTP_400_BAD_REQUEST)

		serializer = PurchaseOrderReceiveSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		item_map = {item.id: item for item in po.items.all()}
		errors = []
		movements = []

		for entry in serializer.validated_data["items"]:
			item_id = entry["id"]
			qty_received = Decimal(str(entry["quantity_received"]))
			item = item_map.get(item_id)
			if not item:
				errors.append(f"Item {item_id} not found in this purchase order.")
				continue
			try:
				movement = StockMovement.record_movement(
					ingredient=item.ingredient,
					movement_type=StockMovement.MovementType.RECEIVING,
					quantity=qty_received,
					created_by=request.user,
					reason=f"PO #{po.po_number or po.id} receiving",
					reference=str(po.id),
				)
				item.quantity_received = F("quantity_received") + qty_received
				item.save(update_fields=["quantity_received", "updated_at"])
				movements.append(movement.id)
			except ValueError as exc:
				errors.append(str(exc))

		if errors:
			return Response({"detail": errors}, status=status.HTTP_400_BAD_REQUEST)

		po.refresh_from_db()
		all_received = all(
			item.quantity_received >= item.quantity_ordered
			for item in po.items.all()
		)
		po.status = PurchaseOrder.Status.RECEIVED if all_received else PurchaseOrder.Status.PARTIALLY_RECEIVED
		po.save(update_fields=["status", "updated_at"])

		log_activity(
			actor_user=request.user,
			action="purchase_order_received",
			entity_type="purchase_order",
			entity_id=str(po.id),
			tenant=request.user.tenant,
			branch=po.branch,
		)

		po.refresh_from_db()
		return Response(PurchaseOrderSerializer(po, context={"request": request}).data, status=status.HTTP_200_OK)
