"""
Authentication Service
Handles user registration, login, and token management
"""

from datetime import timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token
)
from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError
)
from app.models.user import User
from app.schemas.auth import Token, RegisterRequest, LoginRequest


class AuthService:
    """Service for authentication operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def register(self, data: RegisterRequest) -> User:
        """
        Register a new user.
        
        Args:
            data: Registration data with email, password, and full_name
            
        Returns:
            Created user object
            
        Raises:
            ConflictError: If email already exists
        """
        # Check if email already exists
        existing = await self._get_user_by_email(data.email)
        if existing:
            raise ConflictError("User with this email already exists")
        
        # Create user
        user = User(
            email=data.email,
            hashed_password=get_password_hash(data.password),
            full_name=data.full_name,
            phone=data.phone
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        return user
    
    async def login(self, data: LoginRequest) -> Token:
        """
        Authenticate user and return tokens.
        
        Args:
            data: Login credentials
            
        Returns:
            Access and refresh tokens
            
        Raises:
            AuthenticationError: If credentials are invalid
        """
        user = await self._get_user_by_email(data.email)
        
        if not user:
            raise AuthenticationError("Invalid email or password")
        
        if not verify_password(data.password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")
        
        if not user.is_active:
            raise AuthenticationError("User account is disabled")
        
        # Generate tokens
        access_token = create_access_token(
            subject=str(user.id),
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        refresh_token = create_refresh_token(
            subject=str(user.id),
            expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    async def refresh_tokens(self, refresh_token: str) -> Token:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New access and refresh tokens
            
        Raises:
            AuthenticationError: If refresh token is invalid
        """
        user_id = verify_token(refresh_token, token_type="refresh")
        
        if not user_id:
            raise AuthenticationError("Invalid or expired refresh token")
        
        # Verify user still exists and is active
        user = await self._get_user_by_id(int(user_id))
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")
        
        # Generate new tokens
        access_token = create_access_token(
            subject=str(user.id),
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        new_refresh_token = create_refresh_token(
            subject=str(user.id),
            expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        
        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    async def get_current_user(self, token: str) -> User:
        """
        Get current user from access token.
        
        Args:
            token: Valid access token
            
        Returns:
            Current user object
            
        Raises:
            AuthenticationError: If token is invalid
        """
        user_id = verify_token(token, token_type="access")
        
        if not user_id:
            raise AuthenticationError("Invalid or expired access token")
        
        user = await self._get_user_by_id(int(user_id))
        
        if not user:
            raise AuthenticationError("User not found")
        
        if not user.is_active:
            raise AuthenticationError("User account is disabled")
        
        return user
    
    async def _get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def _get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
