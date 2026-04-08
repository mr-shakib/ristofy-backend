from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from tenants.models import Branch, Tenant
from users.models import ActivityLog, UserPinCredential, UserSession

User = get_user_model()


class UserApiTests(APITestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tenant One")
        self.branch = Branch.objects.create(tenant=self.tenant, name="Main")
        self.owner = User.objects.create_user(
            username="owner",
            password="StrongPass123",
            role=User.Role.OWNER,
            tenant=self.tenant,
            branch=self.branch,
        )

    def _auth(self, user):
        access = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    def test_me_get_and_patch(self):
        self._auth(self.owner)

        get_res = self.client.get("/api/v1/me")
        self.assertEqual(get_res.status_code, status.HTTP_200_OK)
        self.assertEqual(get_res.data["username"], "owner")

        patch_res = self.client.patch(
            "/api/v1/me",
            {"first_name": "Updated", "last_name": "Owner"},
            format="json",
        )
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        self.owner.refresh_from_db()
        self.assertEqual(self.owner.first_name, "Updated")

    def test_logout_blacklists_refresh_and_revokes_session(self):
        login_res = self.client.post(
            "/api/v1/auth/login",
            {"username": "owner", "password": "StrongPass123"},
            format="json",
        )
        self.assertEqual(login_res.status_code, status.HTTP_200_OK)
        access = login_res.data["tokens"]["access"]
        refresh = login_res.data["tokens"]["refresh"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        logout_res = self.client.post("/api/v1/auth/logout", {"refresh": refresh}, format="json")
        self.assertEqual(logout_res.status_code, status.HTTP_200_OK)

        refresh_res = self.client.post("/api/v1/auth/refresh", {"refresh": refresh}, format="json")
        self.assertEqual(refresh_res.status_code, status.HTTP_401_UNAUTHORIZED)

        session = UserSession.objects.filter(user=self.owner).latest("created_at")
        self.assertIsNotNone(session.revoked_at)

    def test_activity_logs_visible_to_owner(self):
        ActivityLog.objects.create(
            tenant=self.tenant,
            branch=self.branch,
            actor_user=self.owner,
            action="sample_action",
            entity_type="sample",
            entity_id="1",
        )

        self._auth(self.owner)
        res = self.client.get("/api/v1/activity-logs")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data[0]["action"], "sample_action")

    def test_pin_login_lockout_after_failed_attempts(self):
        UserPinCredential.objects.create(user=self.owner, pin_hash=make_password("1234"))

        for _ in range(5):
            res = self.client.post(
                "/api/v1/auth/login-pin",
                {"username": "owner", "pin": "0000"},
                format="json",
            )
            self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        locked_res = self.client.post(
            "/api/v1/auth/login-pin",
            {"username": "owner", "pin": "1234"},
            format="json",
        )
        self.assertEqual(locked_res.status_code, status.HTTP_423_LOCKED)
