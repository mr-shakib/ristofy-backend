from rest_framework import serializers

from .models import MenuCategory, MenuItem


class MenuCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuCategory
        fields = [
            "id",
            "tenant",
            "branch",
            "name",
            "sort_order",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "tenant", "created_at", "updated_at"]

    def validate_branch(self, value):
        if value and value.tenant_id != self.context["request"].user.tenant_id:
            raise serializers.ValidationError("Branch must belong to your tenant.")
        return value


class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = [
            "id",
            "tenant",
            "branch",
            "category",
            "name",
            "description",
            "base_price",
            "vat_rate",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "tenant", "created_at", "updated_at"]

    def validate(self, attrs):
        request = self.context["request"]
        user_tenant_id = request.user.tenant_id

        branch = attrs.get("branch")
        category = attrs.get("category")

        if branch and branch.tenant_id != user_tenant_id:
            raise serializers.ValidationError({"branch": "Branch must belong to your tenant."})

        if category.tenant_id != user_tenant_id:
            raise serializers.ValidationError({"category": "Category must belong to your tenant."})

        if branch and category.branch_id and category.branch_id != branch.id:
            raise serializers.ValidationError({
                "branch": "Item branch must match category branch when category is branch-specific."
            })

        return attrs
