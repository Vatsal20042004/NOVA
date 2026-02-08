"""
Payment model
"""

import enum
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    String, Text, Numeric, Integer,
    ForeignKey, Enum, CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.order import Order


class PaymentStatus(str, enum.Enum):
    """Payment status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class PaymentMethod(str, enum.Enum):
    """Payment method enumeration"""
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PAYPAL = "paypal"
    BANK_TRANSFER = "bank_transfer"
    CASH_ON_DELIVERY = "cash_on_delivery"


class Payment(Base, TimestampMixin):
    """Payment model for order transactions"""
    
    __tablename__ = "payments"
    
    __table_args__ = (
        CheckConstraint("amount >= 0", name="amount_non_negative"),
        CheckConstraint("retry_count >= 0", name="retry_non_negative"),
    )
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Order relationship
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    
    # Idempotency key for preventing duplicate payments
    idempotency_key: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )
    
    # Payment details
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    
    method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, name="payment_method"),
        nullable=False
    )
    
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status"),
        default=PaymentStatus.PENDING,
        nullable=False
    )
    
    # External payment provider reference
    provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    provider_transaction_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Card details (last 4 digits only for display)
    card_last_four: Mapped[str | None] = mapped_column(String(4), nullable=True)
    card_brand: Mapped[str | None] = mapped_column(String(20), nullable=True)
    
    # Retry tracking
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    
    # Error tracking
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="payment")
    
    @property
    def can_retry(self) -> bool:
        """Check if payment can be retried"""
        return (
            self.status == PaymentStatus.FAILED and 
            self.retry_count < self.max_retries
        )
    
    @property
    def is_successful(self) -> bool:
        """Check if payment was successful"""
        return self.status == PaymentStatus.COMPLETED
    
    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, order_id={self.order_id}, status={self.status})>"
