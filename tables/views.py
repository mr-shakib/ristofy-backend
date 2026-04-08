from rest_framework import generics, permissions

from users.audit import log_activity
from users.permissions import IsOwnerOrManager

from .models import DiningTable, FloorPlan, Reservation
from .serializers import DiningTableSerializer, FloorPlanSerializer, ReservationSerializer


class FloorPlanListCreateView(generics.ListCreateAPIView):
    serializer_class = FloorPlanSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def get_queryset(self):
        return FloorPlan.objects.filter(branch__tenant=self.request.user.tenant).select_related("branch")

    def perform_create(self, serializer):
        floor_plan = serializer.save()
        log_activity(
            actor_user=self.request.user,
            action="floor_plan_created",
            entity_type="floor_plan",
            entity_id=str(floor_plan.id),
            tenant=self.request.user.tenant,
            branch=floor_plan.branch,
        )


class FloorPlanDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FloorPlanSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def get_queryset(self):
        return FloorPlan.objects.filter(branch__tenant=self.request.user.tenant).select_related("branch")

    def perform_update(self, serializer):
        floor_plan = serializer.save()
        log_activity(
            actor_user=self.request.user,
            action="floor_plan_updated",
            entity_type="floor_plan",
            entity_id=str(floor_plan.id),
            tenant=self.request.user.tenant,
            branch=floor_plan.branch,
        )

    def perform_destroy(self, instance):
        log_activity(
            actor_user=self.request.user,
            action="floor_plan_deleted",
            entity_type="floor_plan",
            entity_id=str(instance.id),
            tenant=self.request.user.tenant,
            branch=instance.branch,
        )
        instance.delete()


class DiningTableListCreateView(generics.ListCreateAPIView):
    serializer_class = DiningTableSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def get_queryset(self):
        return DiningTable.objects.filter(branch__tenant=self.request.user.tenant).select_related("branch", "floor_plan")

    def perform_create(self, serializer):
        table = serializer.save()
        log_activity(
            actor_user=self.request.user,
            action="table_created",
            entity_type="table",
            entity_id=str(table.id),
            tenant=self.request.user.tenant,
            branch=table.branch,
        )


class DiningTableDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DiningTableSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def get_queryset(self):
        return DiningTable.objects.filter(branch__tenant=self.request.user.tenant).select_related("branch", "floor_plan")

    def perform_update(self, serializer):
        table = serializer.save()
        log_activity(
            actor_user=self.request.user,
            action="table_updated",
            entity_type="table",
            entity_id=str(table.id),
            tenant=self.request.user.tenant,
            branch=table.branch,
        )

    def perform_destroy(self, instance):
        log_activity(
            actor_user=self.request.user,
            action="table_deleted",
            entity_type="table",
            entity_id=str(instance.id),
            tenant=self.request.user.tenant,
            branch=instance.branch,
        )
        instance.delete()


class ReservationListCreateView(generics.ListCreateAPIView):
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def get_queryset(self):
        return Reservation.objects.filter(branch__tenant=self.request.user.tenant).select_related("branch", "table")

    def perform_create(self, serializer):
        reservation = serializer.save()
        log_activity(
            actor_user=self.request.user,
            action="reservation_created",
            entity_type="reservation",
            entity_id=str(reservation.id),
            tenant=self.request.user.tenant,
            branch=reservation.branch,
        )


class ReservationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def get_queryset(self):
        return Reservation.objects.filter(branch__tenant=self.request.user.tenant).select_related("branch", "table")

    def perform_update(self, serializer):
        reservation = serializer.save()
        log_activity(
            actor_user=self.request.user,
            action="reservation_updated",
            entity_type="reservation",
            entity_id=str(reservation.id),
            tenant=self.request.user.tenant,
            branch=reservation.branch,
        )

    def perform_destroy(self, instance):
        log_activity(
            actor_user=self.request.user,
            action="reservation_deleted",
            entity_type="reservation",
            entity_id=str(instance.id),
            tenant=self.request.user.tenant,
            branch=instance.branch,
        )
        instance.delete()
