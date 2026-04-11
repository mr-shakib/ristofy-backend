from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework import serializers

from menu.models import MenuItem
from tenants.models import Branch

from .models import Customer, CustomerVisit, KitchenTicket, LoyaltyRule, Order, OrderEvent, OrderItem, TakeawayOrder


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
            "course",
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
        fields = [
            "id", "menu_item", "item_name", "unit_price", "vat_rate",
            "quantity", "course", "notes", "status", "created_at", "updated_at",
        ]
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
        fields = ["id", "quantity", "course", "notes", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value


class KitchenTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = KitchenTicket
        fields = ["id", "tenant", "branch", "order", "course", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "tenant", "branch", "order", "course", "created_at", "updated_at"]


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
            "customer",
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
        customer = attrs.get("customer")

        if branch and branch.tenant_id != request.user.tenant_id:
            raise serializers.ValidationError({"branch": "Branch must belong to your tenant."})

        if table and branch and table.branch_id != branch.id:
            raise serializers.ValidationError({"table": "Table must belong to the selected branch."})

        if waiter_user and waiter_user.tenant_id != request.user.tenant_id:
            raise serializers.ValidationError({"waiter_user": "Waiter must belong to your tenant."})

        if customer and customer.tenant_id != request.user.tenant_id:
            raise serializers.ValidationError({"customer": "Customer must belong to your tenant."})

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
            "customer",
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
        customer = attrs.get("customer", instance.customer if instance else None)

        if branch and branch.tenant_id != request.user.tenant_id:
            raise serializers.ValidationError({"branch": "Branch must belong to your tenant."})

        if table and branch and table.branch_id != branch.id:
            raise serializers.ValidationError({"table": "Table must belong to the selected branch."})

        if waiter_user and waiter_user.tenant_id != request.user.tenant_id:
            raise serializers.ValidationError({"waiter_user": "Waiter must belong to your tenant."})

        if customer and customer.tenant_id != request.user.tenant_id:
            raise serializers.ValidationError({"customer": "Customer must belong to your tenant."})

        return attrs


class OrderEventSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source="actor_user.username", read_only=True)

    class Meta:
        model = OrderEvent
        fields = [
            "id", "order", "branch", "actor_user", "actor_username",
            "event_type", "metadata_json", "created_at",
        ]
        read_only_fields = fields


def normalize_phone(value: str) -> str:
    phone = (value or "").strip()
    phone = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if phone and not phone.startswith("+") and phone.isdigit():
        phone = f"+{phone}"
    return phone


class TakeawayOrderItemInputSerializer(serializers.Serializer):
    menu_item = serializers.PrimaryKeyRelatedField(queryset=MenuItem.objects.all())
    quantity = serializers.IntegerField(min_value=1)
    course = serializers.ChoiceField(choices=OrderItem.Course.choices, required=False, default=OrderItem.Course.MAIN)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_menu_item(self, value):
        request = self.context["request"]
        if value.tenant_id != request.user.tenant_id:
            raise serializers.ValidationError("Menu item must belong to your tenant.")
        return value


class TakeawayOrderCreateSerializer(serializers.Serializer):
    branch = serializers.PrimaryKeyRelatedField(queryset=Branch.objects.all())
    pickup_name = serializers.CharField(max_length=160)
    pickup_phone = serializers.CharField(max_length=40)
    customer_name = serializers.CharField(max_length=160, required=False, allow_blank=True)
    customer_phone = serializers.CharField(max_length=40, required=False, allow_blank=True)
    customer_email = serializers.EmailField(required=False, allow_blank=True)
    scheduled_for = serializers.DateTimeField(required=False)
    packaging_fee = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=Decimal("0.00"))
    extra_fee = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=Decimal("0.00"))
    notes = serializers.CharField(required=False, allow_blank=True)
    items = TakeawayOrderItemInputSerializer(many=True)

    def validate(self, attrs):
        request = self.context["request"]
        branch = attrs["branch"]

        if branch.tenant_id != request.user.tenant_id:
            raise serializers.ValidationError({"branch": "Branch must belong to your tenant."})

        if attrs.get("packaging_fee", Decimal("0.00")) < 0:
            raise serializers.ValidationError({"packaging_fee": "Packaging fee cannot be negative."})

        if attrs.get("extra_fee", Decimal("0.00")) < 0:
            raise serializers.ValidationError({"extra_fee": "Extra fee cannot be negative."})

        if not attrs.get("items"):
            raise serializers.ValidationError({"items": "At least one item is required."})

        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        items_data = validated_data.pop("items")
        branch = validated_data["branch"]
        customer_name = validated_data.pop("customer_name", "").strip()
        customer_phone = normalize_phone(validated_data.pop("customer_phone", ""))
        customer_email = validated_data.pop("customer_email", "").strip()

        with transaction.atomic():
            customer = None
            if customer_phone:
                customer, created = Customer.objects.get_or_create(
                    tenant=request.user.tenant,
                    phone=customer_phone,
                    defaults={
                        "full_name": customer_name or validated_data["pickup_name"],
                        "email": customer_email,
                    },
                )
                if not created:
                    changed = False
                    if customer_name and customer.full_name != customer_name:
                        customer.full_name = customer_name
                        changed = True
                    if customer_email and customer.email != customer_email:
                        customer.email = customer_email
                        changed = True
                    if changed:
                        customer.save(update_fields=["full_name", "email", "updated_at"])

            order = Order.objects.create(
                tenant=request.user.tenant,
                branch=branch,
                order_no=Order.next_order_no(branch),
                waiter_user=request.user,
                customer=customer,
                channel=Order.Channel.TAKEAWAY,
                notes=validated_data.get("notes", ""),
            )

            for item_data in items_data:
                menu_item = item_data["menu_item"]
                OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    item_name=menu_item.name,
                    unit_price=menu_item.base_price,
                    vat_rate=menu_item.vat_rate,
                    quantity=item_data["quantity"],
                    course=item_data.get("course", OrderItem.Course.MAIN),
                    notes=item_data.get("notes", ""),
                )

            packaging_fee = validated_data.get("packaging_fee", Decimal("0.00"))
            if packaging_fee > 0:
                OrderItem.objects.create(
                    order=order,
                    menu_item=None,
                    item_name="Packaging Fee",
                    unit_price=packaging_fee,
                    vat_rate=Decimal("22.00"),
                    quantity=1,
                    course=OrderItem.Course.OTHER,
                    status=OrderItem.Status.SERVED,
                )

            extra_fee = validated_data.get("extra_fee", Decimal("0.00"))
            if extra_fee > 0:
                OrderItem.objects.create(
                    order=order,
                    menu_item=None,
                    item_name="Extra Fee",
                    unit_price=extra_fee,
                    vat_rate=Decimal("22.00"),
                    quantity=1,
                    course=OrderItem.Course.OTHER,
                    status=OrderItem.Status.SERVED,
                )

            takeaway = TakeawayOrder.objects.create(
                tenant=request.user.tenant,
                branch=branch,
                order=order,
                customer=customer,
                pickup_name=validated_data["pickup_name"],
                pickup_phone=normalize_phone(validated_data["pickup_phone"]),
                packaging_fee=packaging_fee,
                extra_fee=extra_fee,
                scheduled_for=validated_data.get("scheduled_for"),
                notes=validated_data.get("notes", ""),
            )

            return takeaway


class TakeawayOrderSerializer(serializers.ModelSerializer):
    order = serializers.SerializerMethodField()
    customer = serializers.SerializerMethodField()

    class Meta:
        model = TakeawayOrder
        fields = [
            "id",
            "tenant",
            "branch",
            "order",
            "customer",
            "pickup_name",
            "pickup_phone",
            "packaging_fee",
            "extra_fee",
            "scheduled_for",
            "ready_at",
            "notes",
            "status",
            "created_at",
            "updated_at",
        ]

    def get_order(self, obj):
        return {
            "id": obj.order_id,
            "order_no": obj.order.order_no,
            "status": obj.order.status,
            "channel": obj.order.channel,
            "items": [
                {
                    "id": item.id,
                    "item_name": item.item_name,
                    "quantity": item.quantity,
                    "status": item.status,
                    "course": item.course,
                }
                for item in obj.order.items.all().order_by("id")
            ],
        }

    def get_customer(self, obj):
        if not obj.customer_id:
            return None
        return {
            "id": obj.customer_id,
            "full_name": obj.customer.full_name,
            "phone": obj.customer.phone,
            "email": obj.customer.email,
        }


class LoyaltyVisitCreateSerializer(serializers.Serializer):
    branch = serializers.PrimaryKeyRelatedField(queryset=Branch.objects.all())
    customer_id = serializers.IntegerField(required=False)
    phone = serializers.CharField(max_length=40, required=False, allow_blank=True)
    full_name = serializers.CharField(max_length=160, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    order = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all(), required=False)
    spend_total = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=Decimal("0.00"))
    visit_at = serializers.DateTimeField(required=False)

    def validate(self, attrs):
        request = self.context["request"]
        branch = attrs["branch"]
        if branch.tenant_id != request.user.tenant_id:
            raise serializers.ValidationError({"branch": "Branch must belong to your tenant."})

        order = attrs.get("order")
        if order and order.tenant_id != request.user.tenant_id:
            raise serializers.ValidationError({"order": "Order must belong to your tenant."})

        if attrs.get("spend_total", Decimal("0.00")) < 0:
            raise serializers.ValidationError({"spend_total": "Spend total cannot be negative."})

        customer_id = attrs.get("customer_id")
        phone = attrs.get("phone", "").strip()
        if not customer_id and not phone:
            raise serializers.ValidationError({"phone": "phone is required when customer_id is not provided."})

        return attrs

    def create(self, validated_data):
        request = self.context["request"]

        customer = None
        customer_id = validated_data.get("customer_id")
        if customer_id:
            customer = Customer.objects.filter(id=customer_id, tenant=request.user.tenant).first()
            if not customer:
                raise serializers.ValidationError({"customer_id": "Customer not found."})
        else:
            phone = normalize_phone(validated_data.get("phone", ""))
            defaults = {
                "full_name": validated_data.get("full_name", "Guest") or "Guest",
                "email": validated_data.get("email", ""),
            }
            customer, created = Customer.objects.get_or_create(
                tenant=request.user.tenant,
                phone=phone,
                defaults=defaults,
            )
            if not created:
                changed = False
                full_name = validated_data.get("full_name", "").strip()
                if full_name and customer.full_name != full_name:
                    customer.full_name = full_name
                    changed = True
                email = validated_data.get("email", "").strip()
                if email and customer.email != email:
                    customer.email = email
                    changed = True
                if changed:
                    customer.save(update_fields=["full_name", "email", "updated_at"])

        return CustomerVisit.objects.create(
            tenant=request.user.tenant,
            branch=validated_data["branch"],
            customer=customer,
            order=validated_data.get("order"),
            spend_total=validated_data.get("spend_total", Decimal("0.00")),
            visit_at=validated_data.get("visit_at", timezone.now()),
        )


class LoyaltyEligibilityQuerySerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=40)
    branch = serializers.IntegerField(required=False)


def loyalty_customer_payload(*, customer, branch_id=None):
    visits = customer.visits.all()
    if branch_id:
        visits = visits.filter(branch_id=branch_id)

    total_visits = visits.count()
    total_spend = visits.aggregate(total=Sum("spend_total"))["total"] or Decimal("0.00")
    last_visit = visits.order_by("-visit_at").first()

    return {
        "id": customer.id,
        "full_name": customer.full_name,
        "phone": customer.phone,
        "email": customer.email,
        "preferred_language": customer.preferred_language,
        "marketing_consent": customer.marketing_consent,
        "stats": {
            "total_visits": total_visits,
            "total_spend": f"{total_spend:.2f}",
            "last_visit_at": last_visit.visit_at if last_visit else None,
        },
    }


def loyalty_eligibility_payload(*, tenant, phone, branch_id=None):
    normalized_phone = normalize_phone(phone)
    customer = Customer.objects.filter(tenant=tenant, phone=normalized_phone).first()
    if not customer and normalized_phone.startswith("+"):
        customer = Customer.objects.filter(tenant=tenant, phone=normalized_phone[1:]).first()
    if not customer:
        return {
            "eligible": False,
            "reason": "Customer not found.",
            "customer": None,
            "matched_rule": None,
        }

    base = loyalty_customer_payload(customer=customer, branch_id=branch_id)
    total_visits = base["stats"]["total_visits"]
    total_spend = Decimal(base["stats"]["total_spend"])

    rules = LoyaltyRule.objects.filter(tenant=tenant, is_active=True).order_by("threshold_value", "id")
    matched = None
    for rule in rules:
        if rule.rule_type == LoyaltyRule.RuleType.VISIT_COUNT and Decimal(total_visits) >= rule.threshold_value:
            matched = rule
        if rule.rule_type == LoyaltyRule.RuleType.SPEND_TOTAL and total_spend >= rule.threshold_value:
            matched = rule

    if not matched:
        return {
            "eligible": False,
            "reason": "No active loyalty rule matched.",
            "customer": base,
            "matched_rule": None,
        }

    return {
        "eligible": True,
        "reason": "Eligible for loyalty reward.",
        "customer": base,
        "matched_rule": {
            "id": matched.id,
            "name": matched.name,
            "rule_type": matched.rule_type,
            "threshold_value": f"{matched.threshold_value:.2f}",
            "reward_type": matched.reward_type,
            "reward_value": f"{matched.reward_value:.2f}",
        },
    }
