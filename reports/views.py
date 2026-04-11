from decimal import Decimal

from django.core.cache import cache
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from billing.models import Bill, BillLine
from core.pagination import StandardResultsSetPagination
from orders.models import BuffetSession, OrderItem, WasteLog
from tenants.models import Branch
from users.audit import log_activity
from users.permissions import IsOwnerOrManager

from .models import DailyReportSnapshot
from .serializers import (
	DailyReportSnapshotSerializer,
	ReportFilterSerializer,
	SnapshotRefreshSerializer,
)
from .services import compute_daily_snapshot


def _money(value):
	return (value or Decimal("0.00")).quantize(Decimal("0.01"))


def _tenant_cache_index_key(tenant_id):
	return f"reports:index:{tenant_id}"


def _cache_key_for(tenant_id, name, params):
	if not params:
		return f"reports:{tenant_id}:{name}:default"
	parts = [f"{k}={params[k]}" for k in sorted(params.keys())]
	return f"reports:{tenant_id}:{name}:{'|'.join(parts)}"


def _track_cache_key(tenant_id, key):
	index_key = _tenant_cache_index_key(tenant_id)
	keys = set(cache.get(index_key, []))
	keys.add(key)
	cache.set(index_key, list(keys), 60 * 60 * 24)


def _cached_payload(tenant_id, key):
	return cache.get(key)


def _save_cached_payload(tenant_id, key, payload):
	cache.set(key, payload, 60 * 5)
	_track_cache_key(tenant_id, key)


def _invalidate_tenant_report_cache(tenant_id):
	index_key = _tenant_cache_index_key(tenant_id)
	keys = cache.get(index_key, [])
	for key in keys:
		cache.delete(key)
	cache.delete(index_key)
	return len(keys)


class DailyReportSnapshotListView(generics.ListAPIView):
	serializer_class = DailyReportSnapshotSerializer
	permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]
	pagination_class = StandardResultsSetPagination

	def get_queryset(self):
		qs = DailyReportSnapshot.objects.filter(tenant=self.request.user.tenant).select_related("branch")
		serializer = ReportFilterSerializer(data=self.request.query_params)
		serializer.is_valid(raise_exception=True)

		branch = serializer.validated_data.get("branch")
		if branch:
			qs = qs.filter(branch_id=branch)

		date_from = serializer.validated_data.get("date_from")
		if date_from:
			qs = qs.filter(business_date__gte=date_from)

		date_to = serializer.validated_data.get("date_to")
		if date_to:
			qs = qs.filter(business_date__lte=date_to)

		return qs.order_by("-business_date", "branch__name")


class DailyReportSnapshotRefreshView(APIView):
	permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

	def post(self, request):
		serializer = SnapshotRefreshSerializer(data=request.data, context={"request": request})
		serializer.is_valid(raise_exception=True)
		business_date = serializer.validated_data["business_date"]
		branch = serializer.validated_data.get("branch")

		if branch:
			branches = [branch]
		else:
			branches = list(Branch.objects.filter(tenant=request.user.tenant).order_by("id"))

		snapshots = [
			compute_daily_snapshot(tenant=request.user.tenant, branch=target, business_date=business_date)
			for target in branches
		]
		invalidated = _invalidate_tenant_report_cache(request.user.tenant_id)

		log_activity(
			actor_user=request.user,
			action="report_snapshot_refreshed",
			entity_type="daily_report_snapshot",
			entity_id=str(business_date),
			tenant=request.user.tenant,
			branch=branch,
			metadata={"snapshots": len(snapshots), "cache_keys_invalidated": invalidated},
		)

		return Response(
			{
				"business_date": business_date,
				"snapshots": DailyReportSnapshotSerializer(snapshots, many=True).data,
				"cache_keys_invalidated": invalidated,
			},
			status=status.HTTP_200_OK,
		)


class _CachedReportBaseView(APIView):
	permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]
	report_name = ""

	def get_filters(self, request):
		serializer = ReportFilterSerializer(data=request.query_params)
		serializer.is_valid(raise_exception=True)
		return serializer.validated_data

	def response_with_cache(self, request, params_for_key, payload_builder):
		key = _cache_key_for(request.user.tenant_id, self.report_name, params_for_key)
		use_cache = params_for_key.get("use_cache", True)

		if use_cache:
			cached = _cached_payload(request.user.tenant_id, key)
			if cached is not None:
				return Response({"cached": True, "data": cached}, status=status.HTTP_200_OK)

		payload = payload_builder()
		_save_cached_payload(request.user.tenant_id, key, payload)
		return Response({"cached": False, "data": payload}, status=status.HTTP_200_OK)


class SalesByCategoryView(_CachedReportBaseView):
	report_name = "sales-by-category"

	def get(self, request):
		filters = self.get_filters(request)

		def builder():
			qs = OrderItem.objects.filter(
				order__tenant=request.user.tenant,
				order__bill__status__in=[Bill.Status.FINALIZED, Bill.Status.PAID],
				menu_item__isnull=False,
			)

			branch = filters.get("branch")
			if branch:
				qs = qs.filter(order__branch_id=branch)

			date_from = filters.get("date_from")
			if date_from:
				qs = qs.filter(order__bill__created_at__date__gte=date_from)

			date_to = filters.get("date_to")
			if date_to:
				qs = qs.filter(order__bill__created_at__date__lte=date_to)

			sales_expr = ExpressionWrapper(F("quantity") * F("unit_price"), output_field=DecimalField(max_digits=14, decimal_places=2))
			rows = (
				qs.values("menu_item__category_id", "menu_item__category__name")
				.annotate(total_quantity=Sum("quantity"), net_sales=Sum(sales_expr))
				.order_by("-net_sales", "menu_item__category__name")
			)

			return [
				{
					"category_id": row["menu_item__category_id"],
					"category_name": row["menu_item__category__name"],
					"total_quantity": row["total_quantity"] or 0,
					"net_sales": f"{_money(row['net_sales']):.2f}",
				}
				for row in rows
			]

		return self.response_with_cache(request, filters, builder)


class SalesByTableView(_CachedReportBaseView):
	report_name = "sales-by-table"

	def get(self, request):
		filters = self.get_filters(request)

		def builder():
			qs = Bill.objects.filter(tenant=request.user.tenant).exclude(status=Bill.Status.DRAFT)

			branch = filters.get("branch")
			if branch:
				qs = qs.filter(branch_id=branch)

			date_from = filters.get("date_from")
			if date_from:
				qs = qs.filter(created_at__date__gte=date_from)

			date_to = filters.get("date_to")
			if date_to:
				qs = qs.filter(created_at__date__lte=date_to)

			rows = (
				qs.values("order__table_id", "order__table__code")
				.annotate(total_bills=Count("id"), net_sales=Sum("grand_total"))
				.order_by("order__table__code")
			)

			payload = []
			for row in rows:
				table_code = row["order__table__code"] or "TAKEAWAY/NO_TABLE"
				payload.append(
					{
						"table_id": row["order__table_id"],
						"table_code": table_code,
						"total_bills": row["total_bills"] or 0,
						"net_sales": f"{_money(row['net_sales']):.2f}",
					}
				)
			return payload

		return self.response_with_cache(request, filters, builder)


class SalesByWaiterView(_CachedReportBaseView):
	report_name = "sales-by-waiter"

	def get(self, request):
		filters = self.get_filters(request)

		def builder():
			qs = Bill.objects.filter(tenant=request.user.tenant).exclude(status=Bill.Status.DRAFT)

			branch = filters.get("branch")
			if branch:
				qs = qs.filter(branch_id=branch)

			date_from = filters.get("date_from")
			if date_from:
				qs = qs.filter(created_at__date__gte=date_from)

			date_to = filters.get("date_to")
			if date_to:
				qs = qs.filter(created_at__date__lte=date_to)

			rows = (
				qs.values("order__waiter_user_id", "order__waiter_user__username")
				.annotate(total_bills=Count("id"), net_sales=Sum("grand_total"))
				.order_by("order__waiter_user__username")
			)

			payload = []
			for row in rows:
				waiter_name = row["order__waiter_user__username"] or "UNASSIGNED"
				payload.append(
					{
						"waiter_user_id": row["order__waiter_user_id"],
						"waiter_username": waiter_name,
						"total_bills": row["total_bills"] or 0,
						"net_sales": f"{_money(row['net_sales']):.2f}",
					}
				)
			return payload

		return self.response_with_cache(request, filters, builder)


class SalesByVatView(_CachedReportBaseView):
	report_name = "sales-by-vat"

	def get(self, request):
		filters = self.get_filters(request)

		def builder():
			qs = BillLine.objects.filter(bill__tenant=request.user.tenant, bill__status__in=[Bill.Status.FINALIZED, Bill.Status.PAID])

			branch = filters.get("branch")
			if branch:
				qs = qs.filter(bill__branch_id=branch)

			date_from = filters.get("date_from")
			if date_from:
				qs = qs.filter(bill__created_at__date__gte=date_from)

			date_to = filters.get("date_to")
			if date_to:
				qs = qs.filter(bill__created_at__date__lte=date_to)

			vat_expr = ExpressionWrapper(
				(F("line_total") * F("vat_rate")) / Decimal("100.00"),
				output_field=DecimalField(max_digits=14, decimal_places=2),
			)
			rows = (
				qs.values("vat_rate")
				.annotate(taxable_amount=Sum("line_total"), vat_amount=Sum(vat_expr))
				.order_by("vat_rate")
			)

			return [
				{
					"vat_rate": f"{row['vat_rate']:.2f}",
					"taxable_amount": f"{_money(row['taxable_amount']):.2f}",
					"vat_amount": f"{_money(row['vat_amount']):.2f}",
				}
				for row in rows
			]

		return self.response_with_cache(request, filters, builder)


class BuffetBranchComparisonView(_CachedReportBaseView):
	report_name = "buffet-branch-comparison"

	def get(self, request):
		filters = self.get_filters(request)

		def builder():
			branch_qs = Branch.objects.filter(tenant=request.user.tenant).order_by("name")
			selected_branch = filters.get("branch")
			if selected_branch:
				branch_qs = branch_qs.filter(id=selected_branch)

			date_from = filters.get("date_from")
			date_to = filters.get("date_to")

			payload = []
			for branch in branch_qs:
				session_qs = BuffetSession.objects.filter(tenant=request.user.tenant, branch=branch)
				waste_qs = WasteLog.objects.filter(tenant=request.user.tenant, branch=branch)
				buffet_bill_qs = Bill.objects.filter(
					tenant=request.user.tenant,
					branch=branch,
					order__buffet_session__isnull=False,
				).exclude(status=Bill.Status.DRAFT)

				if date_from:
					session_qs = session_qs.filter(started_at__date__gte=date_from)
					waste_qs = waste_qs.filter(created_at__date__gte=date_from)
					buffet_bill_qs = buffet_bill_qs.filter(created_at__date__gte=date_from)
				if date_to:
					session_qs = session_qs.filter(started_at__date__lte=date_to)
					waste_qs = waste_qs.filter(created_at__date__lte=date_to)
					buffet_bill_qs = buffet_bill_qs.filter(created_at__date__lte=date_to)

				total_sessions = session_qs.count()
				total_guests = session_qs.aggregate(total=Sum(F("adults_count") + F("kids_count")))["total"] or 0
				waste_penalty_total = _money(waste_qs.aggregate(total=Sum("penalty_applied"))["total"])
				buffet_sales = _money(buffet_bill_qs.aggregate(total=Sum("grand_total"))["total"])

				payload.append(
					{
						"branch_id": branch.id,
						"branch_name": branch.name,
						"total_sessions": total_sessions,
						"total_guests": total_guests,
						"waste_penalty_total": f"{waste_penalty_total:.2f}",
						"buffet_sales": f"{buffet_sales:.2f}",
					}
				)

			return payload

		return self.response_with_cache(request, filters, builder)


class ReportCacheInvalidateView(APIView):
	permission_classes = [permissions.IsAuthenticated, IsOwnerOrManager]

	def post(self, request):
		count = _invalidate_tenant_report_cache(request.user.tenant_id)
		log_activity(
			actor_user=request.user,
			action="report_cache_invalidated",
			entity_type="report_cache",
			entity_id=str(request.user.tenant_id),
			tenant=request.user.tenant,
			metadata={"cache_keys_invalidated": count},
		)
		return Response({"cache_keys_invalidated": count}, status=status.HTTP_200_OK)
