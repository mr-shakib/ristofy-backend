from django.urls import path

from .views import (
    BranchDetailView,
    BranchListCreateView,
    FeatureFlagDetailView,
    FeatureFlagListCreateView,
    RegisterTenantView,
    SubscriptionPlanListView,
    TenantDetailView,
    TenantSubscriptionView,
)

urlpatterns = [
    path("auth/register-tenant", RegisterTenantView.as_view(), name="register-tenant"),
    path("tenant", TenantDetailView.as_view(), name="tenant-detail"),
    path("branches", BranchListCreateView.as_view(), name="branches-list-create"),
    path("branches/<int:pk>", BranchDetailView.as_view(), name="branches-detail"),
    path("subscription-plans", SubscriptionPlanListView.as_view(), name="subscription-plans-list"),
    path("subscription", TenantSubscriptionView.as_view(), name="tenant-subscription"),
    path("feature-flags", FeatureFlagListCreateView.as_view(), name="feature-flags-list-create"),
    path("feature-flags/<int:pk>", FeatureFlagDetailView.as_view(), name="feature-flags-detail"),
]
