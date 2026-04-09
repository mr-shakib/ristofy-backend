from django.utils import timezone
from rest_framework import serializers

from .models import BuffetPlan, BuffetRound, BuffetSession, WasteLog


class BuffetPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuffetPlan
        fields = [
            "id", "branch", "name", "base_price", "kids_price",
            "time_limit_minutes", "waste_penalty_amount",
            "round_limit_per_person", "round_delay_seconds",
            "active_from", "active_to", "is_active",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_branch(self, value):
        if value.tenant_id != self.context["request"].user.tenant_id:
            raise serializers.ValidationError("Branch must belong to your tenant.")
        return value

    def validate(self, attrs):
        active_from = attrs.get("active_from")
        active_to = attrs.get("active_to")
        if active_from and active_to and active_to < active_from:
            raise serializers.ValidationError({"active_to": "active_to must be after active_from."})
        return attrs


class BuffetRoundSerializer(serializers.ModelSerializer):
    is_open = serializers.BooleanField(read_only=True)

    class Meta:
        model = BuffetRound
        fields = ["id", "round_number", "opened_at", "closed_at", "is_open"]
        read_only_fields = ["id", "round_number", "opened_at", "closed_at", "is_open"]


class BuffetSessionSerializer(serializers.ModelSerializer):
    rounds = BuffetRoundSerializer(many=True, read_only=True)
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = BuffetSession
        fields = [
            "id", "tenant", "branch", "order", "buffet_plan",
            "adults_count", "kids_count", "started_at", "ends_at",
            "status", "rounds", "is_expired",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "tenant", "ends_at", "status", "created_at", "updated_at"]

    def get_is_expired(self, obj):
        return obj.status == BuffetSession.Status.ACTIVE and timezone.now() > obj.ends_at

    def validate(self, attrs):
        request = self.context["request"]
        branch = attrs.get("branch")
        buffet_plan = attrs.get("buffet_plan")
        order = attrs.get("order")

        if branch and branch.tenant_id != request.user.tenant_id:
            raise serializers.ValidationError({"branch": "Branch must belong to your tenant."})

        if buffet_plan and branch and buffet_plan.branch_id != branch.id:
            raise serializers.ValidationError({"buffet_plan": "Buffet plan must belong to the selected branch."})

        if order and order.tenant_id != request.user.tenant_id:
            raise serializers.ValidationError({"order": "Order must belong to your tenant."})

        return attrs


class WasteLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WasteLog
        fields = [
            "id", "tenant", "branch", "order_item",
            "quantity_wasted", "penalty_applied",
            "marked_by", "reason", "created_at",
        ]
        read_only_fields = ["id", "tenant", "penalty_applied", "marked_by", "created_at"]

    def validate(self, attrs):
        request = self.context["request"]
        branch = attrs.get("branch")
        order_item = attrs.get("order_item")

        if branch and branch.tenant_id != request.user.tenant_id:
            raise serializers.ValidationError({"branch": "Branch must belong to your tenant."})

        if order_item and order_item.order.tenant_id != request.user.tenant_id:
            raise serializers.ValidationError({"order_item": "Order item must belong to your tenant."})

        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        order_item = validated_data.get("order_item")
        branch = validated_data.get("branch")

        # Auto-calculate penalty from the active buffet session's plan if one exists
        penalty = 0
        if order_item:
            session = getattr(order_item.order, "buffet_session", None)
            if session:
                penalty = session.buffet_plan.waste_penalty_amount * validated_data.get("quantity_wasted", 1)

        return WasteLog.objects.create(
            tenant=request.user.tenant,
            marked_by=request.user,
            penalty_applied=penalty,
            **validated_data,
        )
