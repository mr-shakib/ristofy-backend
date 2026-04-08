from django.urls import path

from .views import BranchListCreateView, RegisterTenantView

urlpatterns = [
    path("auth/register-tenant", RegisterTenantView.as_view(), name="register-tenant"),
    path("branches", BranchListCreateView.as_view(), name="branches-list-create"),
]
