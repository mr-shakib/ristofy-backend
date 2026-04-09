from django.db.models import Count, Sum
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import StandardResultsSetPagination
from users.audit import log_activity
from users.permissions import IsOwnerOrManager, IsWaiterOrAbove

from .buffet_serializers import (
    BuffetPlanSerializer,
    BuffetRoundSerializer,
    BuffetSessionSerializer,
    WasteLogSerializer,
)
from .models import BuffetPlan, BuffetRound, BuffetSession, WasteLog


# ─── Buffet Plans ─────────────────────────────────────────────────────────────

class BuffetPlanListCreateView(generics.ListCreateAPIView):
    serializer_class = BuffetPlanSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        qs = (
            BuffetPlan.objects.filter(branch__tenant=self.request.user.tenant)
            .select_related("branch")
            .order_by("name")
        )
        branch = self.request.query_params.get("branch")
        if branch:
            qs = qs.filter(branch_id=branch)
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() in {"1", "true", "yes"})
        return qs

    def perform_create(self, serializer):
        plan = serializer.save()
        log_activity(
            actor_user=self.request.user,
            action="buffet_plan_created",
            entity_type="buffet_plan",
            entity_id=str(plan.id),
            tenant=self.request.user.tenant,
            branch=plan.branch,
        )


class BuffetPlanDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = BuffetPlanSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def get_queryset(self):
        return BuffetPlan.objects.filter(branch__tenant=self.request.user.tenant).select_related("branch")

    def perform_update(self, serializer):
        plan = serializer.save()
        log_activity(
            actor_user=self.request.user,
            action="buffet_plan_updated",
            entity_type="buffet_plan",
            entity_id=str(plan.id),
            tenant=self.request.user.tenant,
            branch=plan.branch,
        )


# ─── Buffet Sessions ──────────────────────────────────────────────────────────

class BuffetSessionStartView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsWaiterOrAbove]

    def post(self, request):
        serializer = BuffetSessionSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        session = serializer.save(
            tenant=request.user.tenant,
            status=BuffetSession.Status.ACTIVE,
        )
        log_activity(
            actor_user=request.user,
            action="buffet_session_started",
            entity_type="buffet_session",
            entity_id=str(session.id),
            tenant=request.user.tenant,
            branch=session.branch,
        )
        return Response(BuffetSessionSerializer(session, context={"request": request}).data, status=status.HTTP_201_CREATED)


class BuffetSessionDetailView(generics.RetrieveAPIView):
    serializer_class = BuffetSessionSerializer
    permission_classes = [permissions.IsAuthenticated, IsWaiterOrAbove]

    def get_queryset(self):
        return (
            BuffetSession.objects.filter(tenant=self.request.user.tenant)
            .select_related("branch", "buffet_plan", "order")
            .prefetch_related("rounds")
        )


class BuffetSessionEndView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def post(self, request, pk):
        try:
            session = BuffetSession.objects.select_related("branch", "buffet_plan").get(
                pk=pk, tenant=request.user.tenant
            )
        except BuffetSession.DoesNotExist:
            return Response({"detail": "Buffet session not found."}, status=status.HTTP_404_NOT_FOUND)

        if session.status == BuffetSession.Status.ENDED:
            return Response({"detail": "Session is already ended."}, status=status.HTTP_400_BAD_REQUEST)

        # Close any open round before ending
        session.rounds.filter(closed_at__isnull=True).update(closed_at=timezone.now())

        session.status = BuffetSession.Status.ENDED
        session.save(update_fields=["status", "updated_at"])

        log_activity(
            actor_user=request.user,
            action="buffet_session_ended",
            entity_type="buffet_session",
            entity_id=str(session.id),
            tenant=request.user.tenant,
            branch=session.branch,
        )
        return Response(
            BuffetSessionSerializer(session, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )


# ─── Buffet Rounds ────────────────────────────────────────────────────────────

class BuffetSessionNewRoundView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsWaiterOrAbove]

    def post(self, request, pk):
        try:
            session = BuffetSession.objects.select_related("branch", "buffet_plan").prefetch_related("rounds").get(
                pk=pk, tenant=request.user.tenant
            )
        except BuffetSession.DoesNotExist:
            return Response({"detail": "Buffet session not found."}, status=status.HTTP_404_NOT_FOUND)

        if session.status == BuffetSession.Status.ENDED:
            return Response({"detail": "Cannot open a round on an ended session."}, status=status.HTTP_400_BAD_REQUEST)

        # Check for already-open round
        if session.rounds.filter(closed_at__isnull=True).exists():
            return Response({"detail": "Close the current round before opening a new one."}, status=status.HTTP_400_BAD_REQUEST)

        # Check round limit
        if session.round_limit_reached():
            return Response(
                {"detail": f"Round limit of {session.buffet_plan.round_limit_per_person} reached."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check round delay
        delay = session.buffet_plan.round_delay_seconds
        if delay > 0:
            elapsed = session.seconds_since_last_closed_round()
            if elapsed is not None and elapsed < delay:
                wait = int(delay - elapsed)
                return Response(
                    {"detail": f"Must wait {wait} more second(s) before opening a new round."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        next_number = (session.rounds.count() or 0) + 1
        buffet_round = BuffetRound.objects.create(
            buffet_session=session,
            round_number=next_number,
        )

        log_activity(
            actor_user=request.user,
            action="buffet_round_opened",
            entity_type="buffet_round",
            entity_id=str(buffet_round.id),
            tenant=request.user.tenant,
            branch=session.branch,
        )
        return Response(BuffetRoundSerializer(buffet_round).data, status=status.HTTP_201_CREATED)


class BuffetSessionCloseRoundView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsWaiterOrAbove]

    def post(self, request, pk):
        try:
            session = BuffetSession.objects.select_related("branch").get(pk=pk, tenant=request.user.tenant)
        except BuffetSession.DoesNotExist:
            return Response({"detail": "Buffet session not found."}, status=status.HTTP_404_NOT_FOUND)

        if session.status == BuffetSession.Status.ENDED:
            return Response({"detail": "Session is already ended."}, status=status.HTTP_400_BAD_REQUEST)

        open_round = session.rounds.filter(closed_at__isnull=True).first()
        if not open_round:
            return Response({"detail": "No open round to close."}, status=status.HTTP_400_BAD_REQUEST)

        open_round.closed_at = timezone.now()
        open_round.save(update_fields=["closed_at"])

        log_activity(
            actor_user=request.user,
            action="buffet_round_closed",
            entity_type="buffet_round",
            entity_id=str(open_round.id),
            tenant=request.user.tenant,
            branch=session.branch,
        )
        return Response(BuffetRoundSerializer(open_round).data, status=status.HTTP_200_OK)


# ─── Waste Logs ───────────────────────────────────────────────────────────────

class WasteLogCreateView(generics.CreateAPIView):
    serializer_class = WasteLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def perform_create(self, serializer):
        waste = serializer.save()
        log_activity(
            actor_user=self.request.user,
            action="waste_log_created",
            entity_type="waste_log",
            entity_id=str(waste.id),
            tenant=self.request.user.tenant,
            branch=waste.branch,
        )


# ─── Buffet Analytics ─────────────────────────────────────────────────────────

class BuffetAnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def get(self, request):
        qs = BuffetSession.objects.filter(tenant=request.user.tenant)

        branch_id = request.query_params.get("branch")
        if branch_id:
            qs = qs.filter(branch_id=branch_id)

        date_from = request.query_params.get("date_from")
        if date_from:
            qs = qs.filter(started_at__date__gte=date_from)

        date_to = request.query_params.get("date_to")
        if date_to:
            qs = qs.filter(started_at__date__lte=date_to)

        agg = qs.aggregate(
            total_sessions=Count("id"),
            total_adults=Sum("adults_count"),
            total_kids=Sum("kids_count"),
        )

        waste_qs = WasteLog.objects.filter(tenant=request.user.tenant)
        if branch_id:
            waste_qs = waste_qs.filter(branch_id=branch_id)
        if date_from:
            waste_qs = waste_qs.filter(created_at__date__gte=date_from)
        if date_to:
            waste_qs = waste_qs.filter(created_at__date__lte=date_to)

        waste_agg = waste_qs.aggregate(
            total_waste_logs=Count("id"),
            total_penalty=Sum("penalty_applied"),
        )

        return Response({
            "total_sessions": agg["total_sessions"] or 0,
            "total_adults": agg["total_adults"] or 0,
            "total_kids": agg["total_kids"] or 0,
            "total_waste_logs": waste_agg["total_waste_logs"] or 0,
            "total_penalty": str(waste_agg["total_penalty"] or "0.00"),
        })
