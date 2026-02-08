
import pytest
from httpx import AsyncClient
from app.models.delivery import DeliveryStatus

class TestDelivery:
    """Test delivery endpoints."""
    
    async def get_token(self, client: AsyncClient, email: str, password: str) -> str:
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": password}
        )
        return response.json()["access_token"]

    @pytest.fixture
    async def admin_token(self, client: AsyncClient) -> str:
        # Create admin user (this needs to be done via direct DB or if there is an endpoint)
        # For now, let's register a user and manually update to admin if possible, 
        # OR just use the fact that we can't easily create admin via API.
        # Wait, I don't have an easy way to make a user an admin via API in tests without a backdoor.
        # I'll rely on a fixture to create an admin user in the DB directly if I could, 
        # but 'client' fixture re-creates DB. 
        # Let's see if I can use the 'db_session' fixture to create an admin.
        pass

    # Since I don't have a clean way to make an admin in this test setup without direct DB access in the test function,
    # I will do it inside the test method using the db_session fixture if I can pass it.
    # But pytest fixtures are resolved before test execution. 
    # The 'client' fixture depends on 'db_session'. 

    @pytest.mark.asyncio
    async def test_delivery_lifecycle(self, client: AsyncClient, db_session):
        # 1. Setup Data
        from app.models.user import User, UserRole
        from app.core.security import get_password_hash
        
        # Create Admin
        admin = User(
            email="admin@example.com",
            hashed_password=get_password_hash("admin123"),
            full_name="Admin User",
            role=UserRole.ADMIN,
            is_active=True
        )
        db_session.add(admin)
        
        # Create Driver
        driver = User(
            email="driver@example.com",
            hashed_password=get_password_hash("driver123"),
            full_name="Driver User",
            role=UserRole.DRIVER,
            is_active=True
        )
        db_session.add(driver)
        
        # Create Customer
        customer = User(
            email="customer@example.com",
            hashed_password=get_password_hash("customer123"),
            full_name="Customer User",
            role=UserRole.CUSTOMER,
            is_active=True
        )
        db_session.add(customer)
        await db_session.commit()
        await db_session.refresh(admin)
        await db_session.refresh(driver)
        await db_session.refresh(customer)

        # Create Product & Order
        from app.models.product import Product
        from app.models.order import Order, OrderItem, OrderStatus
        
        product = Product(
            name="Test Product",
            slug="test-product-unique",
            price=10.0,
            is_active=True
        )
        db_session.add(product)
        await db_session.commit()
        
        order = Order(
            order_number="ORD-1",
            user_id=customer.id,
            status=OrderStatus.CONFIRMED,
            subtotal=10.0,
            total_amount=10.0,
            shipping_address_line1="123 St"
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        # Login tokens
        admin_token = await self.get_token(client, "admin@example.com", "admin123")
        driver_token = await self.get_token(client, "driver@example.com", "driver123")
        customer_token = await self.get_token(client, "customer@example.com", "customer123")

        # 2. Assign Delivery (Admin)
        response = await client.post(
            "/api/v1/deliveries/assign",
            json={
                "order_id": order.id,
                "driver_id": driver.id
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 201
        delivery_data = response.json()
        delivery_id = delivery_data["id"]
        assert delivery_data["status"] == "assigned"
        assert delivery_data["driver_id"] == driver.id

        # 3. View Deliveries (Driver)
        response = await client.get(
            "/api/v1/deliveries/mine",
            headers={"Authorization": f"Bearer {driver_token}"}
        )
        assert response.status_code == 200
        my_deliveries = response.json()
        assert len(my_deliveries) == 1
        assert my_deliveries[0]["id"] == delivery_id

        # 4. Update Status (Driver) -> Picked Up
        response = await client.patch(
            f"/api/v1/deliveries/{delivery_id}/status",
            json={"status": "picked_up"},
            headers={"Authorization": f"Bearer {driver_token}"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "picked_up"

        # 5. Verify Customer View (Order endpoint should show delivery)
        # Note: I need to check the orders endpoint, assuming it includes delivery info now
        response = await client.get(
            f"/api/v1/orders/{order.id}",
            headers={"Authorization": f"Bearer {customer_token}"}
        )
        assert response.status_code == 200
        order_data = response.json()
        assert order_data["delivery"] is not None
        assert order_data["delivery"]["status"] == "picked_up"

        # 6. Update Status (Driver) -> Delivered
        response = await client.patch(
            f"/api/v1/deliveries/{delivery_id}/status",
            json={
                "status": "delivered", 
                "proof_of_delivery": "http://img.com/proof.jpg"
            },
            headers={"Authorization": f"Bearer {driver_token}"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "delivered"
        assert response.json()["proof_of_delivery"] == "http://img.com/proof.jpg"
