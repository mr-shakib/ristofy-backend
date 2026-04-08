from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from users.audit import log_activity
from users.permissions import IsOwnerOrManager
from .models import Branch
from .serializers import BranchSerializer, RegisterTenantSerializer


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


class BranchListCreateView(generics.ListCreateAPIView):
    serializer_class = BranchSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def get_queryset(self):
        return Branch.objects.filter(tenant=self.request.user.tenant).select_related("tenant")

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
