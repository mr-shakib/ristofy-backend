from rest_framework import serializers

from .models import DiningTable, FloorPlan, Reservation


class FloorPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = FloorPlan
        fields = [
            "id",
            "branch",
            "name",
            "layout_json",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_branch(self, value):
        if value.tenant_id != self.context["request"].user.tenant_id:
            raise serializers.ValidationError("Branch must belong to your tenant.")
        return value


class DiningTableSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiningTable
        fields = [
            "id",
            "branch",
            "floor_plan",
            "code",
            "seats",
            "state",
            "x",
            "y",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        request = self.context["request"]
        branch = attrs.get("branch")
        floor_plan = attrs.get("floor_plan")

        if branch and branch.tenant_id != request.user.tenant_id:
            raise serializers.ValidationError({"branch": "Branch must belong to your tenant."})

        if floor_plan and branch and floor_plan.branch_id != branch.id:
            raise serializers.ValidationError({"floor_plan": "Floor plan must belong to selected branch."})

        return attrs


class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = [
            "id",
            "branch",
            "table",
            "customer_name",
            "customer_phone",
            "party_size",
            "reserved_for",
            "status",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        request = self.context["request"]
        branch = attrs.get("branch")
        table = attrs.get("table")

        if branch and branch.tenant_id != request.user.tenant_id:
            raise serializers.ValidationError({"branch": "Branch must belong to your tenant."})

        if table and branch and table.branch_id != branch.id:
            raise serializers.ValidationError({"table": "Table must belong to selected branch."})

        return attrs
