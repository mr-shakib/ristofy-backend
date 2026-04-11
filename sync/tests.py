from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from tenants.models import Branch, Tenant

from .models import Device, OutboxEvent, SyncPushRecord

User = get_user_model()

DEVICE_UUID = "test-device-uuid-001"
DEVICE_UUID_2 = "test-device-uuid-002"


class SyncPhase10Tests(APITestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tenant Sync")
        self.branch = Branch.objects.create(tenant=self.tenant, name="Main Sync Branch")
        self.owner = User.objects.create_user(
            username="owner_sync",
            password="StrongPass123",
            role=User.Role.OWNER,
            tenant=self.tenant,
            branch=self.branch,
        )
        self.waiter = User.objects.create_user(
            username="waiter_sync",
            password="StrongPass123",
            role=User.Role.WAITER,
            tenant=self.tenant,
            branch=self.branch,
        )

        self.other_tenant = Tenant.objects.create(name="Other Sync Tenant")
        self.other_branch = Branch.objects.create(tenant=self.other_tenant, name="Other Sync Branch")
        self.other_owner = User.objects.create_user(
            username="owner_sync_other",
            password="StrongPass123",
            role=User.Role.OWNER,
            tenant=self.other_tenant,
            branch=self.other_branch,
        )

    def _auth(self, user):
        access = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    def _register_device(self, device_uuid=DEVICE_UUID, user=None, branch=None):
        user = user or self.owner
        branch = branch or self.branch
        self._auth(user)
        return self.client.post(
            "/api/v1/devices/register",
            {
                "device_uuid": device_uuid,
                "name": f"POS-{device_uuid}",
                "device_type": "POS",
                "app_version": "1.0.0",
                "branch_id": branch.id,
            },
            format="json",
        )

    # ------------------------------------------------------------------
    # Device registration
    # ------------------------------------------------------------------

    def test_device_register_creates_new_device(self):
        res = self._register_device()
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["device_uuid"], DEVICE_UUID)
        self.assertEqual(Device.objects.filter(tenant=self.tenant).count(), 1)

    def test_device_register_upserts_existing_device(self):
        self._register_device()
        res = self._register_device()  # second call — update
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(Device.objects.filter(tenant=self.tenant).count(), 1)

    def test_device_register_requires_auth(self):
        self.client.credentials()
        res = self.client.post("/api/v1/devices/register", {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_device_register_wrong_tenant_branch_rejected(self):
        self._auth(self.owner)
        res = self.client.post(
            "/api/v1/devices/register",
            {
                "device_uuid": DEVICE_UUID,
                "name": "POS-x",
                "device_type": "POS",
                "branch_id": self.other_branch.id,  # wrong tenant
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_waiter_can_register_device(self):
        self._auth(self.waiter)
        res = self.client.post(
            "/api/v1/devices/register",
            {
                "device_uuid": DEVICE_UUID,
                "name": "Tablet-W1",
                "device_type": "TABLET",
                "branch_id": self.branch.id,
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    # ------------------------------------------------------------------
    # Device heartbeat
    # ------------------------------------------------------------------

    def test_heartbeat_updates_last_seen(self):
        self._register_device()
        self._auth(self.owner)
        res = self.client.post(
            "/api/v1/devices/heartbeat",
            {"device_uuid": DEVICE_UUID, "app_version": "1.0.1"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], "ok")
        device = Device.objects.get(device_uuid=DEVICE_UUID)
        self.assertIsNotNone(device.last_seen_at)

    def test_heartbeat_unknown_device_rejected(self):
        self._auth(self.owner)
        res = self.client.post(
            "/api/v1/devices/heartbeat",
            {"device_uuid": "does-not-exist"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_heartbeat_cross_tenant_device_rejected(self):
        # Register device on other_tenant
        self._register_device(DEVICE_UUID_2, user=self.other_owner, branch=self.other_branch)
        # Try heartbeat as self.owner (different tenant)
        self._auth(self.owner)
        res = self.client.post(
            "/api/v1/devices/heartbeat",
            {"device_uuid": DEVICE_UUID_2},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # ------------------------------------------------------------------
    # Sync push
    # ------------------------------------------------------------------

    def test_push_accepted_without_conflict(self):
        self._register_device()
        self._auth(self.owner)
        res = self.client.post(
            "/api/v1/sync/push",
            {
                "device_uuid": DEVICE_UUID,
                "items": [
                    {
                        "idempotency_key": "idem-001",
                        "entity_type": "order",
                        "entity_id": "999",
                        "payload": {"note": "offline order"},
                    }
                ],
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"][0]["status"], SyncPushRecord.PushStatus.ACCEPTED)
        self.assertEqual(SyncPushRecord.objects.filter(tenant=self.tenant).count(), 1)

    def test_push_idempotent_repeat_returns_stored_result(self):
        self._register_device()
        self._auth(self.owner)
        payload = {
            "device_uuid": DEVICE_UUID,
            "items": [
                {
                    "idempotency_key": "idem-002",
                    "entity_type": "order",
                    "entity_id": "998",
                }
            ],
        }
        self.client.post("/api/v1/sync/push", payload, format="json")
        res = self.client.post("/api/v1/sync/push", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Only one record should exist
        self.assertEqual(SyncPushRecord.objects.filter(idempotency_key="idem-002").count(), 1)

    def test_push_conflict_when_server_newer(self):
        from menu.models import MenuCategory, MenuItem

        category = MenuCategory.objects.create(tenant=self.tenant, branch=self.branch, name="Food")
        item = MenuItem.objects.create(
            tenant=self.tenant,
            branch=self.branch,
            category=category,
            name="Pizza",
            base_price="10.00",
            vat_rate="10.00",
        )

        self._register_device()
        self._auth(self.owner)

        # Device claims it last updated the item 1 hour ago, but server record is newer
        device_ts = (item.updated_at - timedelta(hours=1)).isoformat()

        res = self.client.post(
            "/api/v1/sync/push",
            {
                "device_uuid": DEVICE_UUID,
                "items": [
                    {
                        "idempotency_key": "idem-conflict-001",
                        "entity_type": "menu_item",
                        "entity_id": str(item.id),
                        "device_updated_at": device_ts,
                        "payload": {"name": "Stale Pizza"},
                    }
                ],
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"][0]["status"], SyncPushRecord.PushStatus.CONFLICT)
        self.assertIn("newer", res.data["results"][0]["conflict_detail"])

    def test_push_accepted_when_device_newer(self):
        from menu.models import MenuCategory, MenuItem

        category = MenuCategory.objects.create(tenant=self.tenant, branch=self.branch, name="Drinks")
        item = MenuItem.objects.create(
            tenant=self.tenant,
            branch=self.branch,
            category=category,
            name="Water",
            base_price="2.00",
            vat_rate="4.00",
        )

        self._register_device()
        self._auth(self.owner)

        # Device updated_at is in the future relative to server record
        device_ts = (item.updated_at + timedelta(hours=1)).isoformat()

        res = self.client.post(
            "/api/v1/sync/push",
            {
                "device_uuid": DEVICE_UUID,
                "items": [
                    {
                        "idempotency_key": "idem-newer-001",
                        "entity_type": "menu_item",
                        "entity_id": str(item.id),
                        "device_updated_at": device_ts,
                        "payload": {"name": "Sparkling Water"},
                    }
                ],
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"][0]["status"], SyncPushRecord.PushStatus.ACCEPTED)

    def test_push_unknown_device_rejected(self):
        self._auth(self.owner)
        res = self.client.post(
            "/api/v1/sync/push",
            {
                "device_uuid": "ghost-device",
                "items": [{"idempotency_key": "x", "entity_type": "order", "entity_id": "1"}],
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # ------------------------------------------------------------------
    # Sync pull
    # ------------------------------------------------------------------

    def test_pull_returns_events_since_cursor(self):
        self._register_device()

        # Seed outbox events
        OutboxEvent.objects.create(
            tenant=self.tenant, branch=self.branch, entity_type="order", entity_id="1",
            event_type="created", payload_json={"order_no": 1}
        )
        OutboxEvent.objects.create(
            tenant=self.tenant, branch=self.branch, entity_type="order", entity_id="2",
            event_type="updated", payload_json={"order_no": 2}
        )

        self._auth(self.owner)
        res = self.client.post(
            "/api/v1/sync/pull",
            {"device_uuid": DEVICE_UUID, "cursor": 0, "branch_id": self.branch.id},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["events"]), 2)
        self.assertFalse(res.data["has_more"])

    def test_pull_cursor_advances(self):
        self._register_device()

        e1 = OutboxEvent.objects.create(
            tenant=self.tenant, branch=self.branch, entity_type="menu_item", entity_id="10",
            event_type="updated", payload_json={}
        )
        OutboxEvent.objects.create(
            tenant=self.tenant, branch=self.branch, entity_type="menu_item", entity_id="11",
            event_type="updated", payload_json={}
        )

        self._auth(self.owner)
        # First pull: get only second event
        res = self.client.post(
            "/api/v1/sync/pull",
            {"device_uuid": DEVICE_UUID, "cursor": e1.id, "branch_id": self.branch.id},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["events"]), 1)
        self.assertEqual(res.data["next_cursor"], res.data["events"][-1]["id"])

    def test_pull_tenant_isolation(self):
        self._register_device(DEVICE_UUID_2, user=self.other_owner, branch=self.other_branch)

        # Create event for self.tenant
        OutboxEvent.objects.create(
            tenant=self.tenant, branch=self.branch, entity_type="order", entity_id="1",
            event_type="created", payload_json={}
        )

        self._auth(self.other_owner)
        res = self.client.post(
            "/api/v1/sync/pull",
            {"device_uuid": DEVICE_UUID_2, "cursor": 0, "branch_id": self.other_branch.id},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Other tenant should see zero events
        self.assertEqual(len(res.data["events"]), 0)

    def test_pull_has_more_flag(self):
        self._register_device()

        for i in range(5):
            OutboxEvent.objects.create(
                tenant=self.tenant, branch=self.branch, entity_type="order",
                entity_id=str(i), event_type="created", payload_json={}
            )

        self._auth(self.owner)
        res = self.client.post(
            "/api/v1/sync/pull",
            {"device_uuid": DEVICE_UUID, "cursor": 0, "branch_id": self.branch.id, "limit": 3},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data["has_more"])
        self.assertEqual(len(res.data["events"]), 3)

    def test_pull_wrong_branch_rejected(self):
        self._register_device()
        self._auth(self.owner)
        res = self.client.post(
            "/api/v1/sync/pull",
            {"device_uuid": DEVICE_UUID, "cursor": 0, "branch_id": self.other_branch.id},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pull_unauthenticated_rejected(self):
        self.client.credentials()
        res = self.client.post("/api/v1/sync/pull", {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
