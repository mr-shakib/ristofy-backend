from rest_framework import serializers

from .models import Allergen, MenuCategory, MenuItem, MenuSchedule


class AllergenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Allergen
        fields = [
            "id",
            "code",
            "name_it",
            "name_en",
            "name_de",
            "name_fr",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


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
    allergens = serializers.PrimaryKeyRelatedField(queryset=Allergen.objects.all(), many=True, required=False)

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
            "allergens",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "tenant", "created_at", "updated_at"]

    def validate(self, attrs):
        request = self.context["request"]
        instance = getattr(self, "instance", None)
        user_tenant_id = request.user.tenant_id

        branch = attrs.get("branch", instance.branch if instance else None)
        category = attrs.get("category", instance.category if instance else None)

        if branch and branch.tenant_id != user_tenant_id:
            raise serializers.ValidationError({"branch": "Branch must belong to your tenant."})

        if not category:
            raise serializers.ValidationError({"category": "Category is required."})

        if category.tenant_id != user_tenant_id:
            raise serializers.ValidationError({"category": "Category must belong to your tenant."})

        if branch and category.branch_id and category.branch_id != branch.id:
            raise serializers.ValidationError({
                "branch": "Item branch must match category branch when category is branch-specific."
            })

        return attrs

    def create(self, validated_data):
        allergens = validated_data.pop("allergens", [])
        item = super().create(validated_data)
        if allergens:
            item.allergens.set(allergens)
        return item

    def update(self, instance, validated_data):
        allergens = validated_data.pop("allergens", None)
        item = super().update(instance, validated_data)
        if allergens is not None:
            item.allergens.set(allergens)
        return item


class MenuScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuSchedule
        fields = [
            "id",
            "tenant",
            "branch",
            "menu_item",
            "day_of_week",
            "start_time",
            "end_time",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "tenant", "created_at", "updated_at"]

    def validate(self, attrs):
        request = self.context["request"]
        instance = getattr(self, "instance", None)
        tenant_id = request.user.tenant_id

        branch = attrs.get("branch", instance.branch if instance else None)
        menu_item = attrs.get("menu_item", instance.menu_item if instance else None)
        start_time = attrs.get("start_time", instance.start_time if instance else None)
        end_time = attrs.get("end_time", instance.end_time if instance else None)

        if branch and branch.tenant_id != tenant_id:
            raise serializers.ValidationError({"branch": "Branch must belong to your tenant."})

        if not menu_item:
            raise serializers.ValidationError({"menu_item": "Menu item is required."})

        if menu_item.tenant_id != tenant_id:
            raise serializers.ValidationError({"menu_item": "Menu item must belong to your tenant."})

        if branch and menu_item.branch_id and menu_item.branch_id != branch.id:
            raise serializers.ValidationError({
                "branch": "Schedule branch must match menu item branch when item is branch-specific."
            })

        if start_time and end_time and end_time <= start_time:
            raise serializers.ValidationError({"end_time": "End time must be after start time."})

        return attrs
