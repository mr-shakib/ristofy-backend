from rest_framework import serializers

from .models import KitchenTicket, Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            "id",
            "menu_item",
            "item_name",
            "unit_price",
            "vat_rate",
            "quantity",
            "status",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "item_name", "unit_price", "vat_rate", "created_at", "updated_at"]

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value


class OrderItemAddSerializer(serializers.ModelSerializer):
    """Used for POST /orders/{id}/items — adds a new item to an existing order."""

    class Meta:
        model = OrderItem
        fields = ["id", "menu_item", "item_name", "unit_price", "vat_rate", "quantity", "notes", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "item_name", "unit_price", "vat_rate", "status", "created_at", "updated_at"]

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value

    def create(self, validated_data):
        menu_item = validated_data.get("menu_item")
        if menu_item:
            validated_data.setdefault("item_name", menu_item.name)
            validated_data.setdefault("unit_price", menu_item.base_price)
            validated_data.setdefault("vat_rate", menu_item.vat_rate)
        return OrderItem.objects.create(**validated_data)


class OrderItemUpdateSerializer(serializers.ModelSerializer):
    """Used for PATCH /orders/{id}/items/{item_id} — only mutable fields."""

    class Meta:
        model = OrderItem
        fields = ["id", "quantity", "notes", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value


class KitchenTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = KitchenTicket
        fields = ["id", "tenant", "branch", "order", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "tenant", "branch", "order", "created_at", "updated_at"]


class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, write_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "branch",
            "order_no",
            "table",
            "waiter_user",
            "channel",
            "notes",
            "status",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "order_no", "status", "created_at", "updated_at"]

    def validate(self, attrs):
        request = self.context["request"]
        branch = attrs.get("branch")
        table = attrs.get("table")
        waiter_user = attrs.get("waiter_user")

        if branch and branch.tenant_id != request.user.tenant_id:
            raise serializers.ValidationError({"branch": "Branch must belong to your tenant."})

        if table and branch and table.branch_id != branch.id:
            raise serializers.ValidationError({"table": "Table must belong to the selected branch."})

        if waiter_user and waiter_user.tenant_id != request.user.tenant_id:
            raise serializers.ValidationError({"waiter_user": "Waiter must belong to your tenant."})

        return attrs

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        branch = validated_data["branch"]
        order = Order.objects.create(
            tenant=self.context["request"].user.tenant,
            order_no=Order.next_order_no(branch),
            **validated_data,
        )

        for item_data in items_data:
            menu_item = item_data.get("menu_item")
            if menu_item:
                item_data.setdefault("item_name", menu_item.name)
                item_data.setdefault("unit_price", menu_item.base_price)
                item_data.setdefault("vat_rate", menu_item.vat_rate)
            OrderItem.objects.create(order=order, **item_data)

        return order


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "tenant",
            "branch",
            "order_no",
            "table",
            "waiter_user",
            "status",
            "channel",
            "notes",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "tenant", "order_no", "created_at", "updated_at"]

    def validate(self, attrs):
        request = self.context["request"]
        instance = getattr(self, "instance", None)
        branch = attrs.get("branch", instance.branch if instance else None)
        table = attrs.get("table", instance.table if instance else None)
        waiter_user = attrs.get("waiter_user", instance.waiter_user if instance else None)

        if branch and branch.tenant_id != request.user.tenant_id:
            raise serializers.ValidationError({"branch": "Branch must belong to your tenant."})

        if table and branch and table.branch_id != branch.id:
            raise serializers.ValidationError({"table": "Table must belong to the selected branch."})

        if waiter_user and waiter_user.tenant_id != request.user.tenant_id:
            raise serializers.ValidationError({"waiter_user": "Waiter must belong to your tenant."})

        return attrs
