"""
Product API Tests
"""

import pytest
from httpx import AsyncClient


class TestProducts:
    """Test product endpoints."""
    
    async def get_admin_token(self, client: AsyncClient, db_session) -> str:
        """Helper to get admin auth token."""
        from app.models.user import User, UserRole
        from sqlalchemy import select
        
        email = "admin@example.com"
        
        # Register admin user
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "AdminPassword123!",
                "full_name": "Admin User"
            }
        )
        
        # Upgrade to Admin manually
        result = await db_session.execute(select(User).where(User.email == email))
        user = result.scalar_one()
        user.role = UserRole.ADMIN
        await db_session.commit()
        
        # Login
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": email,
                "password": "AdminPassword123!"
            }
        )
        
        return response.json()["access_token"]
    
    @pytest.mark.asyncio
    async def test_create_product(
        self, client: AsyncClient, db_session, test_product_data: dict
    ):
        """Test creating a product."""
        token = await self.get_admin_token(client, db_session)
        
        response = await client.post(
            "/api/v1/products",
            json=test_product_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == test_product_data["name"]
        assert float(data["price"]) == float(test_product_data["price"])
    
    @pytest.mark.asyncio
    async def test_list_products(
        self, client: AsyncClient, db_session, test_product_data: dict
    ):
        """Test listing products."""
        token = await self.get_admin_token(client, db_session)
        
        # Create a product first
        await client.post(
            "/api/v1/products",
            json=test_product_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # List products (no auth required)
        response = await client.get("/api/v1/products")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["products"]) >= 1
    
    @pytest.mark.asyncio
    async def test_get_product(
        self, client: AsyncClient, db_session, test_product_data: dict
    ):
        """Test getting a single product."""
        token = await self.get_admin_token(client, db_session)
        
        # Create a product
        create_response = await client.post(
            "/api/v1/products",
            json=test_product_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        product_id = create_response.json()["id"]
        
        # Get product
        response = await client.get(f"/api/v1/products/{product_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == product_id
    
    @pytest.mark.asyncio
    async def test_update_product(
        self, client: AsyncClient, db_session, test_product_data: dict
    ):
        """Test updating a product."""
        token = await self.get_admin_token(client, db_session)
        
        # Create a product
        create_response = await client.post(
            "/api/v1/products",
            json=test_product_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        product_id = create_response.json()["id"]
        
        # Update product
        response = await client.put(
            f"/api/v1/products/{product_id}",
            json={"name": "Updated Product Name"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Product Name"
    
    @pytest.mark.asyncio
    async def test_delete_product(
        self, client: AsyncClient, db_session, test_product_data: dict
    ):
        """Test deleting a product."""
        token = await self.get_admin_token(client, db_session)
        
        # Create a product
        create_response = await client.post(
            "/api/v1/products",
            json=test_product_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        product_id = create_response.json()["id"]
        
        # Delete product
        response = await client.delete(
            f"/api/v1/products/{product_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 204
        
        # Verify product is not found
        get_response = await client.get(f"/api/v1/products/{product_id}")
        assert get_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_search_products(
        self, client: AsyncClient, db_session, test_product_data: dict
    ):
        """Test searching products."""
        token = await self.get_admin_token(client, db_session)
        
        # Create a product
        await client.post(
            "/api/v1/products",
            json=test_product_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Search by query param on list endpoint
        response = await client.get(
            "/api/v1/products",
            params={"query": "Test"}
        )
        
        assert response.status_code == 200
        assert len(response.json()["products"]) >= 1
    
    @pytest.mark.asyncio
    async def test_create_product_unauthorized(
        self, client: AsyncClient, test_product_data: dict
    ):
        """Test creating product without auth fails."""
        # Use no trailing slash to avoid 307 redirect
        response = await client.post(
            "/api/v1/products",
            json=test_product_data
        )
        
        assert response.status_code == 401
