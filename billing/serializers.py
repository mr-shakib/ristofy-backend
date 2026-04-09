from decimal import Decimal

from rest_framework import serializers

from orders.models import Order
from tenants.models import Branch

from .models import Bill, BillLine, FiscalTransaction, Payment, Receipt, Refund


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


class RefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = [
            "id",
            "amount",
            "reason",
            "status",
            "fiscal_refund_no",
            "created_at",
        ]
        read_only_fields = fields


class ReceiptSerializer(serializers.ModelSerializer):
    refunds = RefundSerializer(many=True, read_only=True)
    refunded_total = serializers.SerializerMethodField()

    class Meta:
        model = Receipt
        fields = [
            "id",
            "bill",
            "fiscal_receipt_no",
            "z_report_no",
            "issued_at",
            "reprint_count",
            "refunded_total",
            "refunds",
            "created_at",
        ]
        read_only_fields = fields

    def get_refunded_total(self, obj):
        return str(obj.refunded_total)


class FiscalTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FiscalTransaction
        fields = [
            "id",
            "tenant",
            "branch",
            "bill",
            "receipt",
            "transaction_type",
            "status",
            "external_id",
            "error_code",
            "request_json",
            "response_json",
            "created_at",
            "updated_at",
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


class ReceiptRefundCreateSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    reason = serializers.CharField(required=False, allow_blank=True)


class FiscalZReportSyncSerializer(serializers.Serializer):
    branch = serializers.PrimaryKeyRelatedField(queryset=Branch.objects.all())
    business_date = serializers.DateField(required=False)
    z_report_no = serializers.CharField(required=False, allow_blank=True, max_length=64)

    def validate_branch(self, value):
        request = self.context["request"]
        if value.tenant_id != request.user.tenant_id:
            raise serializers.ValidationError("Branch must belong to your tenant.")
        return value


class FiscalAckSerializer(serializers.Serializer):
    external_id = serializers.CharField(max_length=64)
    status = serializers.ChoiceField(choices=FiscalTransaction.Status.choices)
    response_json = serializers.JSONField(required=False)
    error_code = serializers.CharField(required=False, allow_blank=True, max_length=64)