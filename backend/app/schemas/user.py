"""
User schemas
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models.user import UserRole


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)


class UserCreate(UserBase):
    """User creation schema"""
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """User update schema"""
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = None


class UserResponse(BaseModel):
    """User response schema"""
    id: int
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    role: UserRole
    is_active: bool
    is_verified: bool
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UserInDB(UserResponse):
    """User in database schema (includes hashed password)"""
    hashed_password: str


class UserListResponse(BaseModel):
    """User list response"""
    users: list[UserResponse]
    total: int
    page: int
    per_page: int
