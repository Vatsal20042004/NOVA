"""
User model
"""

import enum
from datetime import datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import String, Enum, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.review import Review


class UserRole(str, enum.Enum):
    """User roles enumeration"""
    CUSTOMER = "customer"
    ADMIN = "admin"
    DRIVER = "driver"


class User(Base, TimestampMixin):
    """User model for authentication and profile"""
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"),
        default=UserRole.CUSTOMER,
        nullable=False
    )
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Address fields
    address_line1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # Profile
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Relationships
    orders: Mapped[List["Order"]] = relationship(
        "Order",
        back_populates="user",
        lazy="selectin"
    )
    reviews: Mapped[List["Review"]] = relationship(
        "Review",
        back_populates="user",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"
