from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import StandardResultsSetPagination
from users.audit import log_activity
from users.permissions import IsOwnerOrManager

from .models import Branch, FeatureFlag, SubscriptionPlan, TenantSubscription
from .serializers import (
    BranchSerializer,
    FeatureFlagSerializer,
    RegisterTenantSerializer,
    SubscriptionPlanSerializer,
    TenantSerializer,
    TenantSubscriptionSerializer,
)


class RegisterTenantView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterTenantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.save()
        user = payload["user"]
        log_activity(
            actor_user=user,
            action="tenant_registered",
            entity_type="tenant",
            entity_id=str(payload["tenant"].id),
            tenant=payload["tenant"],
            branch=payload["branch"],
        )
        return Response(payload["response"], status=201)


class TenantDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def get(self, request):
        serializer = TenantSerializer(request.user.tenant)
        return Response(serializer.data)

    def patch(self, request):
        serializer = TenantSerializer(request.user.tenant, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        tenant = serializer.save()
        log_activity(
            actor_user=request.user,
            action="tenant_updated",
            entity_type="tenant",
            entity_id=str(tenant.id),
            tenant=tenant,
        )
        return Response(serializer.data)


class BranchListCreateView(generics.ListCreateAPIView):
    serializer_class = BranchSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Branch.objects.filter(tenant=self.request.user.tenant).select_related("tenant").order_by("id")

    def perform_create(self, serializer):
        branch = serializer.save(tenant=self.request.user.tenant)
        log_activity(
            actor_user=self.request.user,
            action="branch_created",
            entity_type="branch",
            entity_id=str(branch.id),
            tenant=self.request.user.tenant,
            branch=branch,
        )


class BranchDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BranchSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def get_queryset(self):
        return Branch.objects.filter(tenant=self.request.user.tenant).select_related("tenant")

    def perform_update(self, serializer):
        branch = serializer.save()
        log_activity(
            actor_user=self.request.user,
            action="branch_updated",
            entity_type="branch",
            entity_id=str(branch.id),
            tenant=self.request.user.tenant,
            branch=branch,
        )

    def perform_destroy(self, instance):
        log_activity(
            actor_user=self.request.user,
            action="branch_deleted",
            entity_type="branch",
            entity_id=str(instance.id),
            tenant=self.request.user.tenant,
            branch=instance,
        )
        instance.delete()


class SubscriptionPlanListView(generics.ListAPIView):
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = SubscriptionPlan.objects.all().order_by("monthly_price")


class TenantSubscriptionView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def get(self, request):
        try:
            sub = TenantSubscription.objects.select_related("plan").get(tenant=request.user.tenant)
        except TenantSubscription.DoesNotExist:
            return Response({"detail": "No active subscription found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(TenantSubscriptionSerializer(sub).data)

    def patch(self, request):
        try:
            sub = TenantSubscription.objects.select_related("plan").get(tenant=request.user.tenant)
        except TenantSubscription.DoesNotExist:
            return Response({"detail": "No active subscription found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = TenantSubscriptionSerializer(sub, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        log_activity(
            actor_user=request.user,
            action="subscription_updated",
            entity_type="tenant_subscription",
            entity_id=str(sub.id),
            tenant=request.user.tenant,
        )
        return Response(serializer.data)


class FeatureFlagListCreateView(generics.ListCreateAPIView):
    serializer_class = FeatureFlagSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return FeatureFlag.objects.filter(tenant=self.request.user.tenant).order_by("key")

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user.tenant)


class FeatureFlagDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FeatureFlagSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def get_queryset(self):
        return FeatureFlag.objects.filter(tenant=self.request.user.tenant)
