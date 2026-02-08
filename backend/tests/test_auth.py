"""
Authentication API Tests
"""

import pytest
from httpx import AsyncClient


class TestAuth:
    """Test authentication endpoints."""
    
    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient, test_user_data: dict):
        """Test successful user registration."""
        response = await client.post(
            "/api/v1/auth/register",
            json=test_user_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert "id" in data
        assert "password" not in data
    
    @pytest.mark.asyncio
    async def test_register_duplicate_email(
        self, client: AsyncClient, test_user_data: dict
    ):
        """Test registration with existing email fails."""
        # First registration
        await client.post("/api/v1/auth/register", json=test_user_data)
        
        # Second registration with same email
        response = await client.post(
            "/api/v1/auth/register",
            json=test_user_data
        )
        
        assert response.status_code == 409
        # Detail might vary based on exception message but verify status code mainly
        assert "exists" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_register_weak_password(self, client: AsyncClient):
        """Test registration with weak password fails."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "123",
                "full_name": "Test User"
            }
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user_data: dict):
        """Test successful login."""
        # Register first
        await client.post("/api/v1/auth/register", json=test_user_data)
        
        # Login
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_login_wrong_password(
        self, client: AsyncClient, test_user_data: dict
    ):
        """Test login with wrong password fails."""
        # Register first
        await client.post("/api/v1/auth/register", json=test_user_data)
        
        # Login with wrong password
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user fails."""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_refresh_token(self, client: AsyncClient, test_user_data: dict):
        """Test refreshing access token."""
        # Register and login
        await client.post("/api/v1/auth/register", json=test_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
