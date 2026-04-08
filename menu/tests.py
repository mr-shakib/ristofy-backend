from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from tenants.models import Branch, Tenant

User = get_user_model()


class MenuApiTests(APITestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tenant Menu")
        self.branch = Branch.objects.create(tenant=self.tenant, name="Main")
        self.owner = User.objects.create_user(
            username="owner_menu",
            password="StrongPass123",
            role=User.Role.OWNER,
            tenant=self.tenant,
            branch=self.branch,
        )

    def _auth(self):
        access = str(RefreshToken.for_user(self.owner).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    def test_create_category_and_item(self):
        self._auth()
        cat_res = self.client.post(
            "/api/v1/menu/categories",
            {"branch": self.branch.id, "name": "Pizza", "sort_order": 1},
            format="json",
        )
        self.assertEqual(cat_res.status_code, status.HTTP_201_CREATED)

        item_res = self.client.post(
            "/api/v1/menu/items",
            {
                "branch": self.branch.id,
                "category": cat_res.data["id"],
                "name": "Margherita",
                "description": "Classic",
                "base_price": "10.00",
                "vat_rate": "10.00",
            },
            format="json",
        )
        self.assertEqual(item_res.status_code, status.HTTP_201_CREATED)
