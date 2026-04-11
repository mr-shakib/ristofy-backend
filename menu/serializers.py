from rest_framework import serializers

from .models import AddonGroup, AddonItem, Allergen, MenuCategory, MenuItem, MenuSchedule, MenuVariant


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


class MenuVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuVariant
        fields = ["id", "menu_item", "name", "price_delta", "is_default", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "menu_item", "created_at", "updated_at"]

    def validate_is_default(self, value):
        if value and self.instance is None:
            item = self.context.get("menu_item")
            if item and item.variants.filter(is_default=True).exists():
                raise serializers.ValidationError("A default variant already exists for this item.")
        return value


class AddonItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddonItem
        fields = ["id", "addon_group", "name", "price_delta", "vat_rate", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "addon_group", "created_at", "updated_at"]


class AddonGroupSerializer(serializers.ModelSerializer):
    items = AddonItemSerializer(many=True, read_only=True)

    class Meta:
        model = AddonGroup
        fields = [
            "id", "menu_item", "name", "min_select", "max_select",
            "required", "is_active", "items", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "menu_item", "items", "created_at", "updated_at"]

    def validate(self, attrs):
        min_select = attrs.get("min_select", getattr(self.instance, "min_select", 0))
        max_select = attrs.get("max_select", getattr(self.instance, "max_select", 1))
        if max_select < min_select:
            raise serializers.ValidationError({"max_select": "max_select must be >= min_select."})
        return attrs


class MenuItemPublicSerializer(serializers.ModelSerializer):
    """Lean read-only serializer for the public customer menu endpoint."""

    category_name = serializers.CharField(source="category.name", read_only=True)
    allergens = AllergenSerializer(many=True, read_only=True)
    variants = MenuVariantSerializer(many=True, read_only=True)
    addon_groups = AddonGroupSerializer(many=True, read_only=True)

    class Meta:
        model = MenuItem
        fields = [
            "id", "name", "description", "base_price", "vat_rate",
            "category", "category_name", "allergens", "variants", "addon_groups",
        ]
