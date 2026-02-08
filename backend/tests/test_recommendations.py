"""
Recommendation API Tests
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest_asyncio.fixture
async def user_and_products(client: AsyncClient, db_session):
    """Create user and products; return auth token and product_ids."""
    from app.models.user import User, UserRole
    from app.models.product import Product
    from app.models.inventory import Inventory
    from app.core.security import get_password_hash
    from decimal import Decimal

    user = User(
        email="recuser@example.com",
        hashed_password=get_password_hash("RecPass123!"),
        full_name="Rec User",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    product_ids = []
    for i in range(3):
        p = Product(
            name=f"Rec Product {i}",
            slug=f"rec-product-{i}",
            price=Decimal("9.99"),
            is_active=True,
        )
        db_session.add(p)
        await db_session.flush()
        product_ids.append(p.id)
        inv = Inventory(product_id=p.id, quantity=10, reserved=0)
        db_session.add(inv)
    await db_session.commit()
    await db_session.refresh(user)

    login = await client.post(
        "/api/v1/auth/login",
        data={"username": "recuser@example.com", "password": "RecPass123!"},
    )
    token = login.json()["access_token"]
    return token, user.id, product_ids


class TestRecommendations:
    """Test recommendation endpoints."""

    @pytest.mark.asyncio
    async def test_get_my_recommendations(self, client: AsyncClient, user_and_products):
        """Test GET /recommendations/me returns list (may be empty)."""
        token, _, _ = user_and_products
        response = await client.get(
            "/api/v1/recommendations/me",
            params={"limit": 5},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_my_recommendations_unauthorized(self, client: AsyncClient):
        """Test /recommendations/me requires auth."""
        response = await client.get("/api/v1/recommendations/me", params={"limit": 5})
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_similar_products(self, client: AsyncClient, user_and_products):
        """Test GET similar products for a product ID (public)."""
        _, _, product_ids = user_and_products
        product_id = product_ids[0]
        response = await client.get(
            f"/api/v1/recommendations/product/{product_id}/similar",
            params={"limit": 3},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_also_bought(self, client: AsyncClient, user_and_products):
        """Test GET also-bought for a product ID."""
        _, _, product_ids = user_and_products
        product_id = product_ids[0]
        response = await client.get(
            f"/api/v1/recommendations/product/{product_id}/also-bought",
            params={"limit": 3},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
