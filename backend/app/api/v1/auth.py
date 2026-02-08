"""
Authentication API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.exceptions import AuthenticationError, ConflictError
from app.services.auth import AuthService
from app.schemas.auth import (
    Token, RegisterRequest, LoginRequest, RefreshTokenRequest
)
from app.schemas.user import UserResponse
from app.api.deps import get_current_active_user, rate_limit_auth
from app.models.user import User


router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(rate_limit_auth)
):
    """
    Register a new user.
    
    - **email**: Valid email address (must be unique)
    - **password**: Minimum 8 characters with uppercase, lowercase, and digit
    - **full_name**: User's full name
    """
    auth_service = AuthService(db)
    
    try:
        user = await auth_service.register(data)
        return user
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(rate_limit_auth)
):
    """
    Login and get access token.
    
    Use email as username.
    Returns access_token, refresh_token, and expiry.
    """
    auth_service = AuthService(db)
    
    login_data = LoginRequest(
        email=form_data.username,
        password=form_data.password
    )
    
    try:
        token = await auth_service.login(login_data)
        return token
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )


@router.post("/login/json", response_model=Token)
async def login_json(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(rate_limit_auth)
):
    """
    Login with JSON body (alternative to form).
    """
    auth_service = AuthService(db)
    
    try:
        token = await auth_service.login(data)
        return token
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    """
    auth_service = AuthService(db)
    
    try:
        token = await auth_service.refresh_tokens(data.refresh_token)
        return token
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current authenticated user info.
    """
    return current_user


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user)
):
    """
    Logout current user.
    
    Note: Since we use stateless JWTs, this is mainly for client-side cleanup.
    In production, you might want to blacklist the token.
    """
    return {"message": "Successfully logged out"}
