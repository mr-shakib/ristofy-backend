from django.db import connection, OperationalError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    """Lightweight liveness probe. Returns 200 if the process is up."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response({"status": "ok"})


class DBHealthCheckView(APIView):
    """Readiness probe. Returns 200 only when the DB is reachable."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        try:
            connection.ensure_connection()
            return Response({"status": "ok", "db": "reachable"})
        except OperationalError as exc:
            return Response(
                {"status": "error", "db": "unreachable", "detail": str(exc)},
                status=503,
            )
