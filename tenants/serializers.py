from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Branch, Tenant

User = get_user_model()


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ["id", "name", "created_at", "updated_at"]
        read_only_fields = fields


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ["id", "tenant", "name", "created_at", "updated_at"]
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
