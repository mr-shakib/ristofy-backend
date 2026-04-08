from datetime import datetime, timedelta, timezone as dt_timezone

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .audit import log_activity
from .models import ActivityLog, UserPinCredential, UserSession
from .permissions import IsOwnerOrManager
from .serializers import (
    ActivityLogSerializer,
    LoginSerializer,
    LogoutSerializer,
    MeUpdateSerializer,
    PinLoginSerializer,
    SetUserPinSerializer,
    UserCreateSerializer,
    UserSerializer,
)

User = get_user_model()


def _issue_tokens_and_session(*, user, request):
    refresh = RefreshToken.for_user(user)
    expires_at = datetime.fromtimestamp(int(refresh["exp"]), tz=dt_timezone.utc)
    UserSession.objects.create(
        user=user,
        refresh_jti=str(refresh["jti"]),
        device_id=request.headers.get("X-Device-Id", ""),
        ip_address=request.META.get("REMOTE_ADDR"),
        user_agent=request.headers.get("User-Agent", ""),
        expires_at=expires_at,
    )
    return {"refresh": str(refresh), "access": str(refresh.access_token)}


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request,
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )
        if not user:
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

        tokens = _issue_tokens_and_session(user=user, request=request)
        log_activity(
            actor_user=user,
            action="auth_login",
            entity_type="user",
            entity_id=str(user.id),
            tenant=user.tenant,
            branch=user.branch,
        )
        return Response({"tokens": tokens, "user": UserSerializer(user).data})


class PinLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PinLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = User.objects.get(username=serializer.validated_data["username"])
        except User.DoesNotExist:
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            credential = user.pin_credential
        except UserPinCredential.DoesNotExist:
            return Response({"detail": "PIN is not configured for this account."}, status=status.HTTP_403_FORBIDDEN)

        now = timezone.now()
        if credential.locked_until and credential.locked_until > now:
            return Response({"detail": "PIN login is temporarily locked."}, status=status.HTTP_423_LOCKED)

        if not check_password(serializer.validated_data["pin"], credential.pin_hash):
            credential.failed_attempts += 1
            if credential.failed_attempts >= 5:
                credential.locked_until = now + timedelta(minutes=15)
            credential.save(update_fields=["failed_attempts", "locked_until", "updated_at"])
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

        credential.failed_attempts = 0
        credential.locked_until = None
        credential.save(update_fields=["failed_attempts", "locked_until", "updated_at"])

        tokens = _issue_tokens_and_session(user=user, request=request)
        log_activity(
            actor_user=user,
            action="auth_pin_login",
            entity_type="user",
            entity_id=str(user.id),
            tenant=user.tenant,
            branch=user.branch,
        )
        return Response({"tokens": tokens, "user": UserSerializer(user).data})


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            refresh = RefreshToken(serializer.validated_data["refresh"])
            if int(refresh["user_id"]) != request.user.id:
                raise PermissionDenied("You can only logout your own session.")
            jti = str(refresh["jti"])
            refresh.blacklist()
        except TokenError:
            return Response({"detail": "Invalid refresh token."}, status=status.HTTP_400_BAD_REQUEST)

        UserSession.objects.filter(
            user=request.user,
            refresh_jti=jti,
            revoked_at__isnull=True,
        ).update(revoked_at=timezone.now())

        log_activity(
            actor_user=request.user,
            action="auth_logout",
            entity_type="user",
            entity_id=str(request.user.id),
            tenant=request.user.tenant,
            branch=request.user.branch,
        )
        return Response({"detail": "Logged out successfully."}, status=status.HTTP_200_OK)


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = MeUpdateSerializer(instance=request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        log_activity(
            actor_user=request.user,
            action="profile_updated",
            entity_type="user",
            entity_id=str(request.user.id),
            tenant=request.user.tenant,
            branch=request.user.branch,
        )
        return Response(UserSerializer(request.user).data)


class ActivityLogListView(generics.ListAPIView):
    serializer_class = ActivityLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def get_queryset(self):
        queryset = ActivityLog.objects.filter(tenant=self.request.user.tenant).select_related("actor_user", "branch")
        limit = self.request.query_params.get("limit")
        if limit and limit.isdigit():
            return queryset[: int(limit)]
        return queryset[:100]


class UserListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def get_queryset(self):
        return User.objects.filter(tenant=self.request.user.tenant).select_related("branch", "tenant")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return UserCreateSerializer
        return UserSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def perform_create(self, serializer):
        user = serializer.save()
        log_activity(
            actor_user=self.request.user,
            action="user_created",
            entity_type="user",
            entity_id=str(user.id),
            tenant=self.request.user.tenant,
            branch=self.request.user.branch,
        )


class SetUserPinView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, user_id):
        serializer = SetUserPinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            target_user = User.objects.get(id=user_id, tenant=request.user.tenant)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        is_self = request.user.id == target_user.id
        is_manager_scope = request.user.role in {User.Role.OWNER, User.Role.MANAGER}
        if not is_self and not is_manager_scope:
            raise PermissionDenied("You do not have permission to set this PIN.")

        credential, _ = UserPinCredential.objects.get_or_create(user=target_user)
        credential.pin_hash = make_password(serializer.validated_data["pin"])
        credential.failed_attempts = 0
        credential.locked_until = None
        credential.pin_rotated_at = timezone.now()
        credential.save()

        log_activity(
            actor_user=request.user,
            action="pin_set",
            entity_type="user",
            entity_id=str(target_user.id),
            tenant=request.user.tenant,
            branch=request.user.branch,
        )
        return Response({"detail": "PIN updated successfully."}, status=status.HTTP_200_OK)
