"""
Ristofy Backend — Locust Load Test

Covers the three primary user journeys:
  1. Auth flow        — login, refresh, logout
  2. Order flow       — create order, add items, fire to kitchen, close
  3. Reporting flow   — snapshot list, sales by category

Usage:
  pip install locust
  locust -f load_tests/locustfile.py --host=http://127.0.0.1:8000

Then open http://localhost:8089 to configure and start the run.

Required environment variables (or edit defaults below):
  LOAD_TEST_USERNAME  — owner/manager account username
  LOAD_TEST_PASSWORD  — account password
  LOAD_TEST_BRANCH_ID — branch id to use for orders and reports
  LOAD_TEST_MENU_ITEM_ID — a valid menu item id
"""

import os
import random

from locust import HttpUser, SequentialTaskSet, between, task


BASE = "/api/v1"

USERNAME = os.getenv("LOAD_TEST_USERNAME", "owner")
PASSWORD = os.getenv("LOAD_TEST_PASSWORD", "StrongPass123")
BRANCH_ID = int(os.getenv("LOAD_TEST_BRANCH_ID", "1"))
MENU_ITEM_ID = int(os.getenv("LOAD_TEST_MENU_ITEM_ID", "1"))


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def _login(client):
    res = client.post(f"{BASE}/auth/login", json={"username": USERNAME, "password": PASSWORD}, name="/auth/login")
    if res.status_code == 200:
        return res.json()["tokens"]["access"]
    return None


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Task sets
# ---------------------------------------------------------------------------

class AuthFlow(SequentialTaskSet):
    """Login → refresh token → logout."""

    @task
    def login(self):
        res = self.client.post(
            f"{BASE}/auth/login",
            json={"username": USERNAME, "password": PASSWORD},
            name="/auth/login",
        )
        if res.status_code == 200:
            data = res.json()
            self.access = data["tokens"]["access"]
            self.refresh = data["tokens"]["refresh"]
        else:
            self.access = None
            self.refresh = None
            self.interrupt()

    @task
    def refresh_token(self):
        if not getattr(self, "refresh", None):
            self.interrupt()
        self.client.post(
            f"{BASE}/auth/refresh",
            json={"refresh": self.refresh},
            name="/auth/refresh",
        )

    @task
    def logout(self):
        if not getattr(self, "refresh", None):
            self.interrupt()
        self.client.post(
            f"{BASE}/auth/logout",
            json={"refresh": self.refresh},
            headers=_auth_headers(self.access) if self.access else {},
            name="/auth/logout",
        )
        self.interrupt()


class OrderFlow(SequentialTaskSet):
    """Login → create order → add item → fire to kitchen."""

    def on_start(self):
        self.access = _login(self.client)

    @task
    def create_order(self):
        if not self.access:
            self.interrupt()
        res = self.client.post(
            f"{BASE}/orders",
            json={"branch": BRANCH_ID, "source": "waiter", "mode": "a_la_carte"},
            headers=_auth_headers(self.access),
            name="/orders [POST]",
        )
        if res.status_code == 201:
            self.order_id = res.json()["id"]
        else:
            self.order_id = None
            self.interrupt()

    @task
    def add_item(self):
        if not getattr(self, "order_id", None):
            self.interrupt()
        self.client.post(
            f"{BASE}/orders/{self.order_id}/items",
            json={
                "menu_item": MENU_ITEM_ID,
                "quantity": random.randint(1, 3),
                "course": "MAIN",
            },
            headers=_auth_headers(self.access),
            name="/orders/{id}/items [POST]",
        )

    @task
    def fire_to_kitchen(self):
        if not getattr(self, "order_id", None):
            self.interrupt()
        self.client.post(
            f"{BASE}/orders/{self.order_id}/fire",
            headers=_auth_headers(self.access),
            name="/orders/{id}/fire",
        )
        self.interrupt()


class ReportFlow(SequentialTaskSet):
    """Login → snapshots list → sales by category."""

    def on_start(self):
        self.access = _login(self.client)

    @task
    def snapshot_list(self):
        if not self.access:
            self.interrupt()
        self.client.get(
            f"{BASE}/reports/snapshots",
            headers=_auth_headers(self.access),
            name="/reports/snapshots",
        )

    @task
    def sales_by_category(self):
        if not self.access:
            self.interrupt()
        self.client.get(
            f"{BASE}/reports/sales/by-category?branch={BRANCH_ID}",
            headers=_auth_headers(self.access),
            name="/reports/sales/by-category",
        )
        self.interrupt()


class HealthFlow(SequentialTaskSet):
    """Probe health endpoints — simulates monitoring agent traffic."""

    @task
    def liveness(self):
        self.client.get(f"{BASE}/health", name="/health")

    @task
    def readiness(self):
        self.client.get(f"{BASE}/health/db", name="/health/db")
        self.interrupt()


# ---------------------------------------------------------------------------
# User classes — mix of realistic user roles
# ---------------------------------------------------------------------------

class ManagerUser(HttpUser):
    """Simulates a manager running reports and supervising orders."""

    wait_time = between(1, 3)
    tasks = {ReportFlow: 3, OrderFlow: 1}


class WaiterUser(HttpUser):
    """Simulates a waiter creating and firing orders continuously."""

    wait_time = between(0.5, 2)
    tasks = {OrderFlow: 5, AuthFlow: 1}


class MonitorAgent(HttpUser):
    """Simulates an uptime monitoring agent hitting health probes."""

    wait_time = between(5, 10)
    tasks = [HealthFlow]
