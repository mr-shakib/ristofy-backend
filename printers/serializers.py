from rest_framework import serializers

from tenants.models import Branch

from .models import PrintJob, Printer, PrinterRouteRule


class PrinterSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source="branch.name", read_only=True)

    class Meta:
        model = Printer
        fields = [
            "id", "branch", "branch_name", "name", "type",
            "connection_mode", "ip", "port", "is_active",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "branch_name", "created_at", "updated_at"]

    def validate(self, attrs):
        request = self.context["request"]
        branch = attrs.get("branch", getattr(self.instance, "branch", None))
        if branch and branch.tenant_id != request.user.tenant_id:
            raise serializers.ValidationError({"branch": "Branch must belong to your tenant."})
        return attrs


class PrinterRouteRuleSerializer(serializers.ModelSerializer):
    printer_name = serializers.CharField(source="printer.name", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    menu_item_name = serializers.CharField(source="menu_item.name", read_only=True)

    class Meta:
        model = PrinterRouteRule
        fields = [
            "id", "branch", "printer", "printer_name",
            "category", "category_name", "menu_item", "menu_item_name",
            "course", "priority", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "printer_name", "category_name", "menu_item_name", "created_at", "updated_at"]

    def validate(self, attrs):
        request = self.context["request"]
        branch = attrs.get("branch", getattr(self.instance, "branch", None))
        if branch and branch.tenant_id != request.user.tenant_id:
            raise serializers.ValidationError({"branch": "Branch must belong to your tenant."})

        printer = attrs.get("printer", getattr(self.instance, "printer", None))
        if printer and printer.branch_id != branch.id:
            raise serializers.ValidationError({"printer": "Printer must belong to the same branch."})

        category = attrs.get("category")
        if category and category.tenant_id != request.user.tenant_id:
            raise serializers.ValidationError({"category": "Category must belong to your tenant."})

        menu_item = attrs.get("menu_item")
        if menu_item and menu_item.tenant_id != request.user.tenant_id:
            raise serializers.ValidationError({"menu_item": "Menu item must belong to your tenant."})

        return attrs


class PrintJobSerializer(serializers.ModelSerializer):
    printer_name = serializers.CharField(source="printer.name", read_only=True)

    class Meta:
        model = PrintJob
        fields = [
            "id", "tenant", "branch", "printer", "printer_name",
            "kitchen_ticket", "job_type", "payload_json",
            "status", "attempts", "queued_at", "sent_at", "acked_at", "last_error",
        ]
        read_only_fields = fields


class PrintJobReprintSerializer(serializers.Serializer):
    kitchen_ticket_id = serializers.IntegerField()
