from rest_framework import serializers

from orders.models import Order

from .models import Bill, BillLine


class BillLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillLine
        fields = [
            "id",
            "source_type",
            "source_id",
            "description",
            "quantity",
            "unit_price",
            "vat_rate",
            "line_total",
            "created_at",
        ]
        read_only_fields = fields


class BillSerializer(serializers.ModelSerializer):
    lines = BillLineSerializer(many=True, read_only=True)

    class Meta:
        model = Bill
        fields = [
            "id",
            "tenant",
            "branch",
            "order",
            "bill_no",
            "status",
            "subtotal",
            "vat_total",
            "coperto_total",
            "service_charge_total",
            "waste_total",
            "discount_total",
            "grand_total",
            "lines",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class BillCreateFromOrderSerializer(serializers.Serializer):
    order = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all())

    def validate_order(self, value):
        request = self.context["request"]
        if value.tenant_id != request.user.tenant_id:
            raise serializers.ValidationError("Order must belong to your tenant.")
        return value