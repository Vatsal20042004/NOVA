"""
Security utilities for authentication and authorization
- Password hashing with Argon2
- JWT token generation and validation
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import settings


# Password hashing context using bcrypt (fallback) and argon2
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto",
    argon2__memory_cost=65536,
    argon2__time_cost=3,
    argon2__parallelism=4
)


class TokenPayload(BaseModel):
    """JWT Token payload schema"""
    sub: str  # user id
    exp: datetime
    type: str  # "access" or "refresh"
    iat: datetime


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using Argon2"""
    return pwd_context.hash(password)


def create_access_token(
    subject: str | Any,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token"""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": "access",
        "iat": datetime.now(timezone.utc)
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(
    subject: str | Any,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT refresh token"""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": "refresh",
        "iat": datetime.now(timezone.utc)
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> Optional[TokenPayload]:
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        token_data = TokenPayload(
            sub=payload["sub"],
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            type=payload["type"],
            iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
        )
        return token_data
    except JWTError:
        return None


def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    """Verify token and return user ID if valid"""
    token_data = decode_token(token)
    if token_data is None:
        return None
    if token_data.type != token_type:
        return None
    if token_data.exp < datetime.now(timezone.utc):
        return None
    return token_data.sub
