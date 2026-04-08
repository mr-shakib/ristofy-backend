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

    def test_menu_detail_update_and_delete(self):
        self._auth()
        cat_res = self.client.post(
            "/api/v1/menu/categories",
            {"branch": self.branch.id, "name": "Pasta", "sort_order": 2},
            format="json",
        )
        self.assertEqual(cat_res.status_code, status.HTTP_201_CREATED)

        patch_res = self.client.patch(
            f"/api/v1/menu/categories/{cat_res.data['id']}",
            {"name": "Fresh Pasta"},
            format="json",
        )
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_res.data["name"], "Fresh Pasta")

        delete_res = self.client.delete(f"/api/v1/menu/categories/{cat_res.data['id']}")
        self.assertEqual(delete_res.status_code, status.HTTP_204_NO_CONTENT)

    def test_menu_list_filters_and_pagination(self):
        self._auth()
        cat_a = self.client.post(
            "/api/v1/menu/categories",
            {"branch": self.branch.id, "name": "Pizza", "sort_order": 1, "is_active": True},
            format="json",
        ).data
        cat_b = self.client.post(
            "/api/v1/menu/categories",
            {"branch": self.branch.id, "name": "Dessert", "sort_order": 2, "is_active": False},
            format="json",
        ).data

        self.client.post(
            "/api/v1/menu/items",
            {
                "branch": self.branch.id,
                "category": cat_a["id"],
                "name": "Margherita",
                "description": "Classic",
                "base_price": "10.00",
                "vat_rate": "10.00",
                "is_active": True,
            },
            format="json",
        )
        self.client.post(
            "/api/v1/menu/items",
            {
                "branch": self.branch.id,
                "category": cat_b["id"],
                "name": "Tiramisu",
                "description": "Sweet",
                "base_price": "6.00",
                "vat_rate": "10.00",
                "is_active": False,
            },
            format="json",
        )

        res_categories = self.client.get("/api/v1/menu/categories?is_active=true&page_size=1")
        self.assertEqual(res_categories.status_code, status.HTTP_200_OK)
        self.assertIn("results", res_categories.data)
        self.assertEqual(res_categories.data["count"], 1)

        res_items = self.client.get("/api/v1/menu/items?q=mar&page_size=1")
        self.assertEqual(res_items.status_code, status.HTTP_200_OK)
        self.assertEqual(res_items.data["count"], 1)
        self.assertEqual(res_items.data["results"][0]["name"], "Margherita")
