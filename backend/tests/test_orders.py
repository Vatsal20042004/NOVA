"""
Order API Tests
"""

import pytest
from httpx import AsyncClient


class TestOrders:
    """Test order endpoints."""
    
    async def setup_data(self, client: AsyncClient, db_session) -> tuple:
        """Helper to create user, product, and inventory."""
        from app.models.user import User, UserRole
        from app.models.product import Product
        from app.models.inventory import Inventory
        from app.core.security import get_password_hash
        
        # 1. Create Buyer
        buyer = User(
            email="buyer@example.com",
            hashed_password=get_password_hash("BuyerPassword123!"),
            full_name="Buyer User",
            role=UserRole.CUSTOMER,
            is_active=True
        )
        db_session.add(buyer)
        
        # 2. Create Product
        product = Product(
            name="Test Product",
            slug="test-product-order",
            price=29.99,
            is_active=True
        )
        db_session.add(product)
        await db_session.flush()
        
        # 3. Create Inventory
        inventory = Inventory(
            product_id=product.id,
            quantity=100,
            reserved=0
        )
        db_session.add(inventory)
        
        await db_session.commit()
        await db_session.refresh(buyer)
        await db_session.refresh(product)
        
        # 4. Login as Buyer
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "buyer@example.com",
                "password": "BuyerPassword123!"
            }
        )
        token = login_response.json()["access_token"]
        
        return token, product.id
    
    @pytest.mark.asyncio
    async def test_create_order(self, client: AsyncClient, db_session):
        """Test creating an order."""
        token, product_id = await self.setup_data(client, db_session)
        
        order_data = {
            "items": [
                {"product_id": product_id, "quantity": 2}
            ],
            "shipping_address": {
                "address_line1": "123 Test St",
                "city": "Test City",
                "state": "TS",
                "postal_code": "12345",
                "country": "TestCountry"
            }
        }
        
        response = await client.post(
            "/api/v1/orders",
            json=order_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "pending"
    
    @pytest.mark.asyncio
    async def test_create_order_insufficient_stock(self, client: AsyncClient, db_session):
        """Test creating order with insufficient stock fails."""
        token, product_id = await self.setup_data(client, db_session)
        
        order_data = {
            "items": [
                {"product_id": product_id, "quantity": 1000}
            ],
            "shipping_address": {
                "address_line1": "123 Test St",
                "city": "Test City",
                "state": "TS",
                "postal_code": "12345",
                "country": "TestCountry"
            }
        }
        
        response = await client.post(
            "/api/v1/orders",
            json=order_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
        assert "stock" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_list_orders(self, client: AsyncClient, db_session):
        """Test listing user's orders."""
        token, product_id = await self.setup_data(client, db_session)
        
        # Create order
        order_data = {
            "items": [{"product_id": product_id, "quantity": 1}],
             "shipping_address": {
                "address_line1": "123 Test St",
                "city": "Test City",
                "state": "TS",
                "postal_code": "12345",
                "country": "TestCountry"
            }
        }
        await client.post(
            "/api/v1/orders",
            json=order_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # List
        response = await client.get(
            "/api/v1/orders",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["orders"]) >= 1
    
    @pytest.mark.asyncio
    async def test_cancel_order(self, client: AsyncClient, db_session):
        """Test cancelling an order."""
        token, product_id = await self.setup_data(client, db_session)
        
        # Create order
        response = await client.post(
            "/api/v1/orders",
            json={
                "items": [{"product_id": product_id, "quantity": 1}],
                "shipping_address": {
                    "address_line1": "123 Test St",
                    "city": "Test City",
                    "state": "TS",
                    "postal_code": "12345",
                    "country": "TestCountry"
                }
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        order_id = response.json()["id"]
        
        # Cancel order
        response = await client.post(
            f"/api/v1/orders/{order_id}/cancel",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"
    
    @pytest.mark.asyncio
    async def test_order_unauthorized(self, client: AsyncClient):
        """Test creating order without auth fails."""
        response = await client.post(
            "/api/v1/orders",
            json={
                "items": [{"product_id": 1, "quantity": 1}],
                "shipping_address": {
                    "address_line1": "123 Test St",
                    "city": "Test City",
                    "state": "TS",
                    "postal_code": "12345",
                    "country": "TestCountry"
                }
            }
        )
        
        assert response.status_code == 401
