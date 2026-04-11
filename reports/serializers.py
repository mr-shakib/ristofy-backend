from django.utils import timezone
from rest_framework import serializers

from tenants.models import Branch

from .models import DailyReportSnapshot


class ReportFilterSerializer(serializers.Serializer):
    branch = serializers.IntegerField(required=False)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    use_cache = serializers.BooleanField(required=False, default=True)

    def validate(self, attrs):
        date_from = attrs.get("date_from")
        date_to = attrs.get("date_to")
        if date_from and date_to and date_to < date_from:
            raise serializers.ValidationError({"date_to": "date_to must be on or after date_from."})
        return attrs


class SnapshotRefreshSerializer(serializers.Serializer):
    branch = serializers.PrimaryKeyRelatedField(queryset=Branch.objects.all(), required=False)
    business_date = serializers.DateField(required=False)

    def validate(self, attrs):
        request = self.context["request"]
        branch = attrs.get("branch")
        if branch and branch.tenant_id != request.user.tenant_id:
            raise serializers.ValidationError({"branch": "Branch must belong to your tenant."})

        attrs.setdefault("business_date", timezone.localdate())
        return attrs


class DailyReportSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyReportSnapshot
        fields = [
            "id",
            "tenant",
            "branch",
            "business_date",
            "total_orders",
            "completed_orders",
            "canceled_orders",
            "dine_in_orders",
            "takeaway_orders",
            "gross_sales",
            "net_sales",
            "vat_total",
            "discount_total",
            "average_order_value",
            "buffet_sessions",
            "buffet_guests",
            "waste_penalty_total",
            "generated_at",
            "created_at",
        ]
        read_only_fields = fields
