"""
Delivery model
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.user import User


class DeliveryStatus(str, enum.Enum):
    """Delivery status enumeration"""
    ASSIGNED = "assigned"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    FAILED = "failed"


class Delivery(Base, TimestampMixin):
    """Delivery model for tracking order deliveries"""
    
    __tablename__ = "deliveries"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Relationships
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )
    driver_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Status
    status: Mapped[DeliveryStatus] = mapped_column(
        Enum(DeliveryStatus, name="delivery_status"),
        default=DeliveryStatus.ASSIGNED,
        nullable=False
    )
    
    # Tracking
    current_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    proof_of_delivery: Mapped[str | None] = mapped_column(Text, nullable=True)  # URL to image
    delivery_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Timestamps
    picked_up_at: Mapped[datetime | None] = mapped_column(nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(nullable=True)
    
    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="delivery", uselist=False)
    driver: Mapped["User"] = relationship("User")
    
    def __repr__(self) -> str:
        return f"<Delivery(id={self.id}, order_id={self.order_id}, status={self.status})>"
