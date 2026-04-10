from rest_framework import serializers

from .models import Ingredient, RecipeComponent, StockMovement


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = [
            "id",
            "tenant",
            "branch",
            "name",
            "sku",
            "unit",
            "current_stock",
            "min_stock_level",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "tenant", "created_at", "updated_at"]

    def validate(self, attrs):
        request = self.context["request"]
        branch = attrs.get("branch", getattr(self.instance, "branch", None))
        if branch and branch.tenant_id != request.user.tenant_id:
            raise serializers.ValidationError({"branch": "Branch must belong to your tenant."})
        return attrs


class StockMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMovement
        fields = [
            "id",
            "tenant",
            "branch",
            "ingredient",
            "movement_type",
            "quantity",
            "stock_before",
            "stock_after",
            "reason",
            "reference",
            "created_by",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "tenant",
            "branch",
            "stock_before",
            "stock_after",
            "created_by",
            "created_at",
        ]

    def validate(self, attrs):
        request = self.context["request"]
        ingredient = attrs.get("ingredient")
        quantity = attrs.get("quantity")

        if ingredient and ingredient.tenant_id != request.user.tenant_id:
            raise serializers.ValidationError({"ingredient": "Ingredient must belong to your tenant."})

        if quantity is not None and quantity <= 0:
            raise serializers.ValidationError({"quantity": "Quantity must be greater than zero."})

        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        try:
            return StockMovement.record_movement(
                ingredient=validated_data["ingredient"],
                movement_type=validated_data["movement_type"],
                quantity=validated_data["quantity"],
                created_by=request.user,
                reason=validated_data.get("reason", ""),
                reference=validated_data.get("reference", ""),
            )
        except ValueError as exc:
            raise serializers.ValidationError({"detail": str(exc)})


class LowStockIngredientSerializer(serializers.ModelSerializer):
    shortage = serializers.SerializerMethodField()

    class Meta:
        model = Ingredient
        fields = [
            "id",
            "tenant",
            "branch",
            "name",
            "sku",
            "unit",
            "current_stock",
            "min_stock_level",
            "shortage",
            "updated_at",
        ]

    def get_shortage(self, obj):
        shortage = obj.min_stock_level - obj.current_stock
        return f"{max(shortage, 0):.3f}"


class RecipeComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeComponent
        fields = [
            "id",
            "tenant",
            "branch",
            "menu_item",
            "ingredient",
            "quantity",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "tenant", "created_at", "updated_at"]

    def validate(self, attrs):
        request = self.context["request"]
        branch = attrs.get("branch", getattr(self.instance, "branch", None))
        menu_item = attrs.get("menu_item", getattr(self.instance, "menu_item", None))
        ingredient = attrs.get("ingredient", getattr(self.instance, "ingredient", None))

        if branch and branch.tenant_id != request.user.tenant_id:
            raise serializers.ValidationError({"branch": "Branch must belong to your tenant."})

        if menu_item and menu_item.tenant_id != request.user.tenant_id:
            raise serializers.ValidationError({"menu_item": "Menu item must belong to your tenant."})

        if ingredient and ingredient.tenant_id != request.user.tenant_id:
            raise serializers.ValidationError({"ingredient": "Ingredient must belong to your tenant."})

        if branch and ingredient and ingredient.branch_id != branch.id:
            raise serializers.ValidationError({"ingredient": "Ingredient branch must match selected branch."})

        if branch and menu_item and menu_item.branch_id and menu_item.branch_id != branch.id:
            raise serializers.ValidationError({"menu_item": "Menu item branch must match selected branch."})

        if attrs.get("quantity") is not None and attrs["quantity"] <= 0:
            raise serializers.ValidationError({"quantity": "Quantity must be greater than zero."})

        return attrs


class ReceiveStockSerializer(serializers.Serializer):
    ingredient = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    quantity = serializers.DecimalField(max_digits=12, decimal_places=3)
    supplier_name = serializers.CharField(max_length=160, required=False, allow_blank=True)
    document_no = serializers.CharField(max_length=120, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        request = self.context["request"]
        ingredient = attrs["ingredient"]

        if ingredient.tenant_id != request.user.tenant_id:
            raise serializers.ValidationError({"ingredient": "Ingredient must belong to your tenant."})

        if attrs["quantity"] <= 0:
            raise serializers.ValidationError({"quantity": "Quantity must be greater than zero."})

        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        supplier = validated_data.get("supplier_name", "")
        notes = validated_data.get("notes", "")
        reason = "Receiving stock"
        if supplier:
            reason = f"Receiving stock - {supplier}"
        if notes:
            reason = f"{reason}: {notes}"

        return StockMovement.record_movement(
            ingredient=validated_data["ingredient"],
            movement_type=StockMovement.MovementType.RECEIVING,
            quantity=validated_data["quantity"],
            created_by=request.user,
            reason=reason,
            reference=validated_data.get("document_no", ""),
        )


class InventoryUsageQuerySerializer(serializers.Serializer):
    branch = serializers.IntegerField(required=False)
    ingredient = serializers.IntegerField(required=False)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)

    def validate(self, attrs):
        date_from = attrs.get("date_from")
        date_to = attrs.get("date_to")
        if date_from and date_to and date_to < date_from:
            raise serializers.ValidationError({"date_to": "date_to must be on or after date_from."})
        return attrs
