"""
Review model for product reviews
"""

from typing import TYPE_CHECKING

from sqlalchemy import (
    String, Text, Integer, Boolean,
    ForeignKey, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.product import Product


class Review(Base, TimestampMixin):
    """Product review model"""
    
    __tablename__ = "reviews"
    
    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_user_product_review"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="rating_range"),
    )
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Moderation
    is_verified_purchase: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Helpfulness metrics
    helpful_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    not_helpful_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="reviews")
    product: Mapped["Product"] = relationship("Product", back_populates="reviews")
    
    @property
    def helpfulness_ratio(self) -> float:
        """Calculate helpfulness ratio"""
        total = self.helpful_count + self.not_helpful_count
        if total == 0:
            return 0.0
        return self.helpful_count / total
    
    def __repr__(self) -> str:
        return f"<Review(id={self.id}, product_id={self.product_id}, rating={self.rating})>"
