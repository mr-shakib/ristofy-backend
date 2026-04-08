from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import ActivityLogListView, LoginView, LogoutView, MeView, PinLoginView, SetUserPinView, UserListCreateView

urlpatterns = [
    path("auth/login", LoginView.as_view(), name="auth-login"),
    path("auth/login-pin", PinLoginView.as_view(), name="auth-login-pin"),
    path("auth/logout", LogoutView.as_view(), name="auth-logout"),
    path("auth/refresh", TokenRefreshView.as_view(), name="auth-refresh"),
    path("me", MeView.as_view(), name="me"),
    path("users", UserListCreateView.as_view(), name="users-list-create"),
    path("users/<int:user_id>/set-pin", SetUserPinView.as_view(), name="users-set-pin"),
    path("activity-logs", ActivityLogListView.as_view(), name="activity-logs"),
]
