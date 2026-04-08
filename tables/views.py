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
