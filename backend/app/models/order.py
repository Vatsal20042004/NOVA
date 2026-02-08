"""
Order and OrderItem models
"""

import enum
from datetime import datetime
from decimal import Decimal
from typing import List, TYPE_CHECKING

from sqlalchemy import (
    String, Text, Numeric, Integer, 
    ForeignKey, Enum, CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.product import Product
    from app.models.payment import Payment
    from app.models.delivery import Delivery


class OrderStatus(str, enum.Enum):
    """Order status enumeration"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class Order(Base, TimestampMixin):
    """Order model"""
    
    __tablename__ = "orders"
    
    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="total_non_negative"),
    )
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Order identification
    order_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )
    
    # Idempotency key for preventing duplicate orders
    request_id: Mapped[str | None] = mapped_column(
        String(100),
        unique=True,
        nullable=True,
        index=True
    )
    
    # User relationship
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Order status
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status"),
        default=OrderStatus.PENDING,
        nullable=False
    )
    
    # Pricing
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
        nullable=False
    )
    shipping_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
        nullable=False
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
        nullable=False
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )
    
    # Shipping address
    shipping_address_line1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    shipping_address_line2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    shipping_city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    shipping_state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    shipping_postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    shipping_country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Tracking
    tracking_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # Timestamps for status changes
    shipped_at: Mapped[datetime | None] = mapped_column(nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    payment: Mapped["Payment | None"] = relationship(
        "Payment",
        back_populates="order",
        uselist=False
    )
    delivery: Mapped["Delivery | None"] = relationship(
        "Delivery",
        back_populates="order",
        uselist=False,
        lazy="selectin"
    )
    
    @property
    def item_count(self) -> int:
        """Total number of items in order"""
        return sum(item.quantity for item in self.items)
    
    def __repr__(self) -> str:
        return f"<Order(id={self.id}, order_number={self.order_number}, status={self.status})>"


class OrderItem(Base, TimestampMixin):
    """Order line item model"""
    
    __tablename__ = "order_items"
    
    __table_args__ = (
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint("unit_price >= 0", name="unit_price_non_negative"),
    )
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,  # Allow null if product deleted
        index=True
    )
    
    # Product snapshot at time of order (for historical accuracy)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    product_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    @property
    def total_price(self) -> Decimal:
        """Calculate line item total"""
        return self.unit_price * self.quantity
    
    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="items")
    product: Mapped["Product | None"] = relationship("Product")
    
    def __repr__(self) -> str:
        return f"<OrderItem(id={self.id}, product={self.product_name}, qty={self.quantity})>"
