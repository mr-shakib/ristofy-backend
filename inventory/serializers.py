from rest_framework import serializers

from .models import Ingredient, StockMovement


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
