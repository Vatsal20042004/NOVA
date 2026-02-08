"""
Inventory model with version column for optimistic locking
"""

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.product import Product


class Inventory(Base, TimestampMixin):
    """
    Inventory model for tracking product stock.
    
    Uses version column for optimistic locking to prevent overselling.
    """
    
    __tablename__ = "inventory"
    
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="quantity_non_negative"),
        CheckConstraint("reserved >= 0", name="reserved_non_negative"),
        CheckConstraint("low_stock_threshold >= 0", name="threshold_non_negative"),
    )
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    
    # Stock quantities
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reserved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Warehouse support for future multi-warehouse
    warehouse_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Optimistic locking version
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Stock alerts
    low_stock_threshold: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    
    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="inventory")
    
    @property
    def available(self) -> int:
        """Calculate available stock (quantity - reserved)"""
        return max(0, self.quantity - self.reserved)
    
    @property
    def is_low_stock(self) -> bool:
        """Check if stock is below threshold"""
        return self.available <= self.low_stock_threshold
    
    @property
    def is_out_of_stock(self) -> bool:
        """Check if product is out of stock"""
        return self.available <= 0
    
    def reserve(self, amount: int) -> bool:
        """
        Reserve stock for an order.
        Returns True if successful, False if insufficient stock.
        """
        if self.available >= amount:
            self.reserved += amount
            self.version += 1
            return True
        return False
    
    def release(self, amount: int) -> None:
        """Release reserved stock (e.g., order cancelled)"""
        self.reserved = max(0, self.reserved - amount)
        self.version += 1
    
    def confirm(self, amount: int) -> None:
        """Confirm reservation and deduct from quantity (order completed)"""
        self.quantity -= amount
        self.reserved -= amount
        self.version += 1
    
    def restock(self, amount: int) -> None:
        """Add stock to inventory"""
        self.quantity += amount
        self.version += 1
    
    def __repr__(self) -> str:
        return f"<Inventory(product_id={self.product_id}, available={self.available})>"
