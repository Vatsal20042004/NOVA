"""
API Dependencies
Common dependencies for API endpoints
"""

from typing import Optional

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import verify_token
from app.core.cache import cache
from app.core.exceptions import RateLimitError
from app.core.config import settings
from app.models.user import User, UserRole
from app.services.auth import AuthService


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login",
    auto_error=False
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token.
    
    Raises:
        HTTPException: If token is invalid or user not found
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    auth_service = AuthService(db)
    
    try:
        user = await auth_service.get_current_user(token)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Get the current user if authenticated, otherwise None.
    Used for endpoints that work for both authenticated and anonymous users.
    """
    if not token:
        return None
    
    try:
        auth_service = AuthService(db)
        return await auth_service.get_current_user(token)
    except:
        return None


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current user and verify they are active.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current user and verify they have admin role.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def get_current_driver_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current user and verify they have driver role.
    """
    if current_user.role != UserRole.DRIVER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Driver access required"
        )
    return current_user


async def check_rate_limit(
    request_id: Optional[str] = Header(None, alias="X-Request-ID")
) -> str:
    """
    Check rate limit for the request.
    Returns the request ID (generated if not provided).
    """
    import uuid
    
    req_id = request_id or str(uuid.uuid4())
    
    # Rate limiting is handled by middleware
    # This dependency just ensures request ID exists
    
    return req_id


class RateLimiter:
    """
    Rate limiter dependency for specific endpoints.
    """
    
    def __init__(self, limit: int = 100, window: int = 60):
        self.limit = limit
        self.window = window
    
    async def __call__(
        self,
        current_user: Optional[User] = Depends(get_current_user_optional)
    ) -> None:
        """Check rate limit for user or IP"""
        # Use user ID if authenticated, otherwise would use IP
        if current_user:
            key = f"rate:user:{current_user.id}"
        else:
            # In production, would get IP from request
            key = f"rate:anon:{hash('anonymous')}"
        
        try:
            is_allowed, remaining = await cache.check_rate_limit(
                key,
                self.limit,
                self.window
            )
            
            if not is_allowed:
                raise RateLimitError(retry_after=self.window)
        except RateLimitError:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(self.window)}
            )
        except Exception:
            # If rate limiting fails, allow the request
            pass


# Pre-configured rate limiters
rate_limit_auth = RateLimiter(limit=20, window=60)  # 20 requests/min for auth
rate_limit_default = RateLimiter(limit=100, window=60)  # 100 requests/min default
