from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from .models import ActivityLog

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class PinLoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    pin = serializers.CharField(max_length=8, write_only=True)


class SetUserPinSerializer(serializers.Serializer):
    pin = serializers.RegexField(regex=r"^\d{4,8}$")


class MeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "first_name", "last_name"]


class ActivityLogSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source="actor_user.username", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)

    class Meta:
        model = ActivityLog
        fields = [
            "id",
            "action",
            "entity_type",
            "entity_id",
            "metadata_json",
            "created_at",
            "actor_user",
            "actor_username",
            "branch",
            "branch_name",
        ]
        read_only_fields = fields


class UserSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source="tenant.name", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "tenant",
            "tenant_name",
            "branch",
            "branch_name",
            "is_active",
            "date_joined",
        ]
        read_only_fields = ["id", "tenant", "date_joined", "tenant_name", "branch_name"]


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "role",
            "branch",
        ]

    def validate_role(self, value):
        request = self.context["request"]
        actor_role = request.user.role
        if actor_role == User.Role.MANAGER and value in {User.Role.OWNER, User.Role.MANAGER}:
            raise serializers.ValidationError("Managers cannot create owner or manager accounts.")
        return value

    def validate_branch(self, value):
        request = self.context["request"]
        if value and value.tenant_id != request.user.tenant_id:
            raise serializers.ValidationError("Branch must belong to your tenant.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        request = self.context["request"]
        password = validated_data.pop("password")
        user = User.objects.create(
            tenant=request.user.tenant,
            **validated_data,
        )
        user.set_password(password)
        user.save(update_fields=["password"])
        return user
