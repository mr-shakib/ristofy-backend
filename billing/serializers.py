from decimal import Decimal

from rest_framework import serializers

from orders.models import Order

from .models import Bill, BillLine, Payment


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


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "method",
            "amount",
            "reference",
            "paid_at",
            "created_at",
        ]
        read_only_fields = fields


class BillSerializer(serializers.ModelSerializer):
    lines = BillLineSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    amount_paid = serializers.SerializerMethodField()

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
            "amount_paid",
            "lines",
            "payments",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_amount_paid(self, obj):
        return str(obj.amount_paid)


class BillCreateFromOrderSerializer(serializers.Serializer):
    order = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all())

    def validate_order(self, value):
        request = self.context["request"]
        if value.tenant_id != request.user.tenant_id:
            raise serializers.ValidationError("Order must belong to your tenant.")
        return value


class BillApplyCopertoSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0.01"))
    covers = serializers.IntegerField(min_value=1)


class BillApplyDiscountSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=[("PERCENT", "Percent"), ("FIXED", "Fixed")])
    value = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0.01"))


class BillPaySerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=Payment.Method.choices)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    reference = serializers.CharField(required=False, allow_blank=True, max_length=255)