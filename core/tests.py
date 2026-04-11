from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from tenants.models import Branch, Tenant

User = get_user_model()


class HealthCheckTests(APITestCase):
    def test_liveness_returns_200(self):
        res = self.client.get("/api/v1/health")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], "ok")

    def test_liveness_requires_no_auth(self):
        # No credentials set — should still return 200
        self.client.credentials()
        res = self.client.get("/api/v1/health")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_db_health_returns_200_when_db_reachable(self):
        res = self.client.get("/api/v1/health/db")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], "ok")
        self.assertEqual(res.data["db"], "reachable")

    def test_db_health_returns_503_when_db_unreachable(self):
        from django.db import OperationalError
        with patch("core.health.connection.ensure_connection", side_effect=OperationalError("connection refused")):
            res = self.client.get("/api/v1/health/db")
        self.assertEqual(res.status_code, 503)
        self.assertEqual(res.data["status"], "error")
        self.assertEqual(res.data["db"], "unreachable")


class ThrottleConfigTests(APITestCase):
    """Verify throttle classes are wired to the auth endpoints."""

    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tenant Throttle")
        self.branch = Branch.objects.create(tenant=self.tenant, name="Main")
        self.user = User.objects.create_user(
            username="throttle_user",
            password="StrongPass123",
            role=User.Role.OWNER,
            tenant=self.tenant,
            branch=self.branch,
        )

    def test_login_view_has_auth_throttle(self):
        from users.views import LoginView
        from core.throttles import AuthLoginRateThrottle
        throttle_classes = [t.__class__ if not isinstance(t, type) else t for t in LoginView.throttle_classes]
        self.assertIn(AuthLoginRateThrottle, throttle_classes)

    def test_pin_login_view_has_pin_throttle(self):
        from users.views import PinLoginView
        from core.throttles import PinLoginRateThrottle
        throttle_classes = [t.__class__ if not isinstance(t, type) else t for t in PinLoginView.throttle_classes]
        self.assertIn(PinLoginRateThrottle, throttle_classes)

    def test_throttle_returns_429_when_limit_exceeded(self):
        """
        Patch AuthLoginRateThrottle.allow_request to deny the 3rd call and
        verify the view returns HTTP 429. This isolates the test from cache
        state and DRF settings reload order.
        """
        from core.throttles import AuthLoginRateThrottle

        call_count = {"n": 0}

        def side_effect(self, _request, _view):
            call_count["n"] += 1
            if call_count["n"] > 2:
                self.history = []
                self.now = 0
                return False
            return True

        payload = {"username": "throttle_user", "password": "WrongPass"}
        with patch.object(AuthLoginRateThrottle, "allow_request", side_effect):
            self.client.post("/api/v1/auth/login", payload, format="json")
            self.client.post("/api/v1/auth/login", payload, format="json")
            res = self.client.post("/api/v1/auth/login", payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class LoggingConfigTests(APITestCase):
    """Verify LOGGING is configured and the ristofy logger exists."""

    def test_logging_config_has_ristofy_logger(self):
        from django.conf import settings
        self.assertIn('LOGGING', dir(settings))
        loggers = settings.LOGGING.get('loggers', {})
        self.assertIn('ristofy', loggers)

    def test_logging_config_has_console_handler(self):
        from django.conf import settings
        handlers = settings.LOGGING.get('handlers', {})
        self.assertIn('console', handlers)
