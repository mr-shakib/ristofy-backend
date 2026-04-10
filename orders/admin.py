from django.contrib import admin

from .models import Customer, CustomerVisit, LoyaltyRule, TakeawayOrder


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
	list_display = ("id", "full_name", "phone", "tenant", "preferred_language", "marketing_consent")
	list_filter = ("tenant", "preferred_language", "marketing_consent")
	search_fields = ("full_name", "phone", "email")


@admin.register(CustomerVisit)
class CustomerVisitAdmin(admin.ModelAdmin):
	list_display = ("id", "customer", "branch", "spend_total", "visit_at")
	list_filter = ("tenant", "branch")
	search_fields = ("customer__full_name", "customer__phone")


@admin.register(LoyaltyRule)
class LoyaltyRuleAdmin(admin.ModelAdmin):
	list_display = ("id", "name", "tenant", "rule_type", "threshold_value", "reward_type", "reward_value", "is_active")
	list_filter = ("tenant", "rule_type", "reward_type", "is_active")
	search_fields = ("name",)


@admin.register(TakeawayOrder)
class TakeawayOrderAdmin(admin.ModelAdmin):
	list_display = ("id", "order", "branch", "pickup_name", "pickup_phone", "status", "packaging_fee", "extra_fee")
	list_filter = ("tenant", "branch", "status")
	search_fields = ("pickup_name", "pickup_phone", "order__order_no")
