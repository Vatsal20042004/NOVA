"""
Admin API Tests
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient, db_session):
    """Create admin user and return auth token."""
    from app.models.user import User, UserRole
    from app.core.security import get_password_hash

    admin = User(
        email="admin@test.com",
        hashed_password=get_password_hash("AdminPass123!"),
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)

    login = await client.post(
        "/api/v1/auth/login",
        data={"username": "admin@test.com", "password": "AdminPass123!"},
    )
    return login.json()["access_token"]


@pytest_asyncio.fixture
async def admin_and_customer(client: AsyncClient, db_session):
    """Create admin and customer; return admin token and customer user id."""
    from app.models.user import User, UserRole
    from app.core.security import get_password_hash

    admin = User(
        email="admin2@test.com",
        hashed_password=get_password_hash("AdminPass123!"),
        full_name="Admin Two",
        role=UserRole.ADMIN,
        is_active=True,
    )
    customer = User(
        email="customer@test.com",
        hashed_password=get_password_hash("CustomerPass123!"),
        full_name="Customer User",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db_session.add(admin)
    db_session.add(customer)
    await db_session.commit()
    await db_session.refresh(customer)

    login = await client.post(
        "/api/v1/auth/login",
        data={"username": "admin2@test.com", "password": "AdminPass123!"},
    )
    return login.json()["access_token"], customer.id


class TestAdmin:
    """Test admin-only endpoints."""

    @pytest.mark.asyncio
    async def test_list_users_requires_admin(self, client: AsyncClient, admin_token):
        """Test GET /admin/users returns list when admin."""
        response = await client.get(
            "/api/v1/admin/users",
            params={"page": 1, "per_page": 10},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_list_users_unauthorized(self, client: AsyncClient):
        """Test admin/users without auth returns 401."""
        response = await client.get(
            "/api/v1/admin/users",
            params={"page": 1, "per_page": 10},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_low_stock_requires_admin(self, client: AsyncClient, admin_token):
        """Test GET /admin/inventory/low-stock as admin."""
        response = await client.get(
            "/api/v1/admin/inventory/low-stock",
            params={"limit": 20},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_set_user_role(self, client: AsyncClient, admin_and_customer):
        """Test admin can set user role."""
        token, customer_id = admin_and_customer
        response = await client.put(
            f"/api/v1/admin/users/{customer_id}/role",
            params={"role": "driver"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["role"] == "driver"

    @pytest.mark.asyncio
    async def test_simulate_error_admin(self, client: AsyncClient, admin_token):
        """Test admin can call simulate error endpoint."""
        response = await client.post(
            "/api/v1/admin/simulate/error",
            params={"error_code": 418},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 418
