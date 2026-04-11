from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import StandardResultsSetPagination
from users.audit import log_activity
from users.permissions import IsOwnerOrManager

from .models import PrintJob, Printer, PrinterRouteRule
from .serializers import (
    PrintJobReprintSerializer,
    PrintJobSerializer,
    PrinterRouteRuleSerializer,
    PrinterSerializer,
)


class PrinterListCreateView(generics.ListCreateAPIView):
    serializer_class = PrinterSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        qs = Printer.objects.filter(branch__tenant=self.request.user.tenant).select_related("branch")
        branch_id = self.request.query_params.get("branch")
        if branch_id:
            qs = qs.filter(branch_id=branch_id)
        return qs.order_by("branch__name", "name")

    def perform_create(self, serializer):
        printer = serializer.save()
        log_activity(
            actor_user=self.request.user,
            action="printer_created",
            entity_type="printer",
            entity_id=str(printer.id),
            tenant=self.request.user.tenant,
            branch=printer.branch,
        )


class PrinterDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PrinterSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def get_queryset(self):
        return Printer.objects.filter(branch__tenant=self.request.user.tenant).select_related("branch")

    def perform_update(self, serializer):
        printer = serializer.save()
        log_activity(
            actor_user=self.request.user,
            action="printer_updated",
            entity_type="printer",
            entity_id=str(printer.id),
            tenant=self.request.user.tenant,
            branch=printer.branch,
        )

    def perform_destroy(self, instance):
        log_activity(
            actor_user=self.request.user,
            action="printer_deleted",
            entity_type="printer",
            entity_id=str(instance.id),
            tenant=self.request.user.tenant,
            branch=instance.branch,
        )
        instance.delete()


class PrinterRouteRuleListCreateView(generics.ListCreateAPIView):
    serializer_class = PrinterRouteRuleSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        qs = PrinterRouteRule.objects.filter(
            branch__tenant=self.request.user.tenant
        ).select_related("branch", "printer", "category", "menu_item")
        branch_id = self.request.query_params.get("branch")
        if branch_id:
            qs = qs.filter(branch_id=branch_id)
        return qs

    def perform_create(self, serializer):
        rule = serializer.save()
        log_activity(
            actor_user=self.request.user,
            action="printer_route_rule_created",
            entity_type="printer_route_rule",
            entity_id=str(rule.id),
            tenant=self.request.user.tenant,
            branch=rule.branch,
        )


class PrinterRouteRuleDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PrinterRouteRuleSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def get_queryset(self):
        return PrinterRouteRule.objects.filter(
            branch__tenant=self.request.user.tenant
        ).select_related("branch", "printer", "category", "menu_item")

    def perform_update(self, serializer):
        rule = serializer.save()
        log_activity(
            actor_user=self.request.user,
            action="printer_route_rule_updated",
            entity_type="printer_route_rule",
            entity_id=str(rule.id),
            tenant=self.request.user.tenant,
            branch=rule.branch,
        )

    def perform_destroy(self, instance):
        log_activity(
            actor_user=self.request.user,
            action="printer_route_rule_deleted",
            entity_type="printer_route_rule",
            entity_id=str(instance.id),
            tenant=self.request.user.tenant,
            branch=instance.branch,
        )
        instance.delete()


class PrintJobDetailView(generics.RetrieveAPIView):
    serializer_class = PrintJobSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def get_queryset(self):
        return PrintJob.objects.filter(
            tenant=self.request.user.tenant
        ).select_related("branch", "printer", "kitchen_ticket")


class PrintJobListView(generics.ListAPIView):
    serializer_class = PrintJobSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        qs = PrintJob.objects.filter(tenant=self.request.user.tenant).select_related("branch", "printer")
        branch_id = self.request.query_params.get("branch")
        if branch_id:
            qs = qs.filter(branch_id=branch_id)
        job_status = self.request.query_params.get("status")
        if job_status:
            qs = qs.filter(status=job_status)
        return qs.order_by("-queued_at")


class PrintJobReprintView(APIView):
    """Re-queue a kitchen ticket for reprinting."""

    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

    def post(self, request):
        serializer = PrintJobReprintSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket_id = serializer.validated_data["kitchen_ticket_id"]

        from orders.models import KitchenTicket

        try:
            ticket = KitchenTicket.objects.select_related("branch", "printer").get(
                id=ticket_id,
                tenant=request.user.tenant,
            )
        except KitchenTicket.DoesNotExist:
            return Response({"detail": "Kitchen ticket not found."}, status=status.HTTP_404_NOT_FOUND)

        job = PrintJob.objects.create(
            tenant=request.user.tenant,
            branch=ticket.branch,
            printer=ticket.printer,
            kitchen_ticket=ticket,
            job_type=PrintJob.JobType.KITCHEN_TICKET,
            payload_json={
                "ticket_id": ticket.id,
                "order_id": ticket.order_id,
                "course": ticket.course,
                "reprint": True,
            },
        )

        log_activity(
            actor_user=request.user,
            action="print_job_reprint_queued",
            entity_type="print_job",
            entity_id=str(job.id),
            tenant=request.user.tenant,
            branch=ticket.branch,
            metadata={"kitchen_ticket_id": ticket_id},
        )

        return Response(PrintJobSerializer(job).data, status=status.HTTP_201_CREATED)
