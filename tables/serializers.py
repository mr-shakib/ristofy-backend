from rest_framework import serializers

from .models import DiningTable, FloorPlan, Reservation, TableMergeSession, TableSession, WaitlistEntry


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
        instance = getattr(self, "instance", None)
        branch = attrs.get("branch", instance.branch if instance else None)
        floor_plan = attrs.get("floor_plan", instance.floor_plan if instance else None)

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
        instance = getattr(self, "instance", None)
        branch = attrs.get("branch", instance.branch if instance else None)
        table = attrs.get("table", instance.table if instance else None)
        reserved_for = attrs.get("reserved_for", instance.reserved_for if instance else None)
        status = attrs.get("status", instance.status if instance else None)

        if branch and branch.tenant_id != request.user.tenant_id:
            raise serializers.ValidationError({"branch": "Branch must belong to your tenant."})

        if table and branch and table.branch_id != branch.id:
            raise serializers.ValidationError({"table": "Table must belong to selected branch."})

        if table and reserved_for and status != Reservation.Status.CANCELED:
            overlap_qs = Reservation.objects.filter(
                table=table,
                reserved_for=reserved_for,
            ).exclude(status=Reservation.Status.CANCELED)
            if instance:
                overlap_qs = overlap_qs.exclude(id=instance.id)

            if overlap_qs.exists():
                raise serializers.ValidationError(
                    {"reserved_for": "This table is already reserved for the selected time slot."}
                )

        return attrs


class WaitlistEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = WaitlistEntry
        fields = [
            "id",
            "branch",
            "table",
            "customer_name",
            "customer_phone",
            "party_size",
            "quoted_wait_minutes",
            "status",
            "notes",
            "seated_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        request = self.context["request"]
        instance = getattr(self, "instance", None)
        branch = attrs.get("branch", instance.branch if instance else None)
        table = attrs.get("table", instance.table if instance else None)

        if branch and branch.tenant_id != request.user.tenant_id:
            raise serializers.ValidationError({"branch": "Branch must belong to your tenant."})

        if table and branch and table.branch_id != branch.id:
            raise serializers.ValidationError({"table": "Table must belong to selected branch."})

        return attrs


class TableSessionSerializer(serializers.ModelSerializer):
    table_code = serializers.CharField(source="table.code", read_only=True)
    opened_by_username = serializers.CharField(source="opened_by.username", read_only=True)

    class Meta:
        model = TableSession
        fields = [
            "id", "branch", "table", "table_code",
            "opened_by", "opened_by_username", "covers",
            "seat_map_json", "opened_at", "closed_at",
        ]
        read_only_fields = fields


class TableMergeSessionSerializer(serializers.ModelSerializer):
    primary_table_code = serializers.CharField(source="primary_table.code", read_only=True)

    class Meta:
        model = TableMergeSession
        fields = [
            "id", "branch", "primary_table", "primary_table_code",
            "merged_table_ids", "started_at", "ended_at",
        ]
        read_only_fields = fields
