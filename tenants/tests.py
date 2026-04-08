from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from tenants.models import Branch, Tenant

User = get_user_model()


class BranchApiTests(APITestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tenant Branch")
        self.branch = Branch.objects.create(tenant=self.tenant, name="Main")
        self.owner = User.objects.create_user(
            username="owner_branch",
            password="StrongPass123",
            role=User.Role.OWNER,
            tenant=self.tenant,
            branch=self.branch,
        )
        self.waiter = User.objects.create_user(
            username="waiter_branch",
            password="StrongPass123",
            role=User.Role.WAITER,
            tenant=self.tenant,
            branch=self.branch,
        )

    def _auth(self, user):
        access = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    def test_owner_can_create_branch(self):
        self._auth(self.owner)
        res = self.client.post("/api/v1/branches", {"name": "Second"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_waiter_cannot_access_branch_management(self):
        self._auth(self.waiter)
        res = self.client.get("/api/v1/branches")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
