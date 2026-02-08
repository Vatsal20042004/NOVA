"""
Payment API Tests
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest_asyncio.fixture
async def order_and_token(client: AsyncClient, db_session):
    """Create user, product, inventory via DB; create order via API so inventory is reserved. Return token and order_id."""
    from app.models.user import User, UserRole
    from app.models.product import Product
    from app.models.inventory import Inventory
    from app.core.security import get_password_hash
    from decimal import Decimal

    user = User(
        email="payuser@example.com",
        hashed_password=get_password_hash("PayPass123!"),
        full_name="Pay User",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db_session.add(user)
    product = Product(
        name="Pay Test Product",
        slug="pay-test-product",
        price=Decimal("19.99"),
        is_active=True,
    )
    db_session.add(product)
    await db_session.flush()
    inv = Inventory(product_id=product.id, quantity=50, reserved=0)
    db_session.add(inv)
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(product)

    login = await client.post(
        "/api/v1/auth/login",
        data={"username": "payuser@example.com", "password": "PayPass123!"},
    )
    token = login.json()["access_token"]
    order_response = await client.post(
        "/api/v1/orders",
        json={
            "items": [{"product_id": product.id, "quantity": 1}],
            "shipping_address": {
                "address_line1": "123 Pay St",
                "city": "Pay City",
                "state": "PS",
                "postal_code": "12345",
                "country": "PayCountry",
            },
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert order_response.status_code == 201
    order_id = order_response.json()["id"]
    return token, order_id


class TestPayments:
    """Test payment endpoints."""

    @pytest.mark.asyncio
    async def test_process_payment_success(self, client: AsyncClient, order_and_token):
        """Test successful payment processing."""
        token, order_id = order_and_token
        response = await client.post(
            "/api/v1/payments/process",
            json={
                "order_id": order_id,
                "method": "credit_card",
                "card_number": "4111111111111111",
                "card_expiry": "12/28",
                "card_cvv": "123",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["order_id"] == order_id
        assert data["status"] in ("completed", "pending", "processing")
        assert "id" in data
        assert "idempotency_key" in data

    @pytest.mark.asyncio
    async def test_process_payment_idempotency(self, client: AsyncClient, order_and_token):
        """Test idempotent payment with same key returns same result."""
        token, order_id = order_and_token
        key = "idem-key-123"
        payload = {
            "order_id": order_id,
            "method": "credit_card",
            "idempotency_key": key,
        }
        r1 = await client.post(
            "/api/v1/payments/process",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r1.status_code == 200
        r2 = await client.post(
            "/api/v1/payments/process",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r2.status_code == 200
        assert r1.json()["id"] == r2.json()["id"]
        assert r1.json()["idempotency_key"] == r2.json()["idempotency_key"]

    @pytest.mark.asyncio
    async def test_get_payment(self, client: AsyncClient, order_and_token):
        """Test get payment by ID."""
        token, order_id = order_and_token
        process = await client.post(
            "/api/v1/payments/process",
            json={"order_id": order_id, "method": "credit_card"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert process.status_code == 200
        payment_id = process.json()["id"]
        response = await client.get(
            f"/api/v1/payments/{payment_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["id"] == payment_id
        assert response.json()["order_id"] == order_id

    @pytest.mark.asyncio
    async def test_payment_unauthorized(self, client: AsyncClient, order_and_token):
        """Test payment endpoints require auth."""
        _, order_id = order_and_token
        response = await client.post(
            "/api/v1/payments/process",
            json={"order_id": order_id, "method": "credit_card"},
        )
        assert response.status_code == 401
