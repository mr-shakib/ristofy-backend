from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Branch, FeatureFlag, SubscriptionPlan, Tenant, TenantSubscription

User = get_user_model()


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = [
            "id", "name", "email", "phone", "address",
            "vat_number", "fiscal_code", "logo_url",
            "timezone", "currency", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ["id", "tenant", "name", "address", "phone", "email", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "tenant", "created_at", "updated_at"]


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = [
            "id", "name", "tier", "max_branches", "max_users",
            "monthly_price", "annual_price", "features_json",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class TenantSubscriptionSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source="plan.name", read_only=True)
    plan_tier = serializers.CharField(source="plan.tier", read_only=True)

    class Meta:
        model = TenantSubscription
        fields = [
            "id", "tenant", "plan", "plan_name", "plan_tier",
            "status", "trial_ends_at", "current_period_start",
            "current_period_end", "external_subscription_id",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "tenant", "created_at", "updated_at"]


class FeatureFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureFlag
        fields = ["id", "tenant", "key", "enabled", "value_json", "created_at", "updated_at"]
        read_only_fields = ["id", "tenant", "created_at", "updated_at"]


class RegisterTenantSerializer(serializers.Serializer):
    tenant_name = serializers.CharField(max_length=255)
    branch_name = serializers.CharField(max_length=255)
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)

    def validate_tenant_name(self, value):
        if Tenant.objects.filter(name=value).exists():
            raise serializers.ValidationError("A tenant with this name already exists.")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        tenant = Tenant.objects.create(name=validated_data["tenant_name"])
        branch = Branch.objects.create(tenant=tenant, name=validated_data["branch_name"])
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            role=User.Role.OWNER,
            tenant=tenant,
            branch=branch,
            is_staff=True,
        )

        refresh = RefreshToken.for_user(user)
        response = {
            "tenant": TenantSerializer(tenant).data,
            "branch": BranchSerializer(branch).data,
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role,
            },
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
        }
        return {
            "tenant": tenant,
            "branch": branch,
            "user": user,
            "response": response,
        }
