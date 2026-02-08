"""
Product and Category models
"""

from datetime import datetime
from decimal import Decimal
from typing import List, TYPE_CHECKING

from sqlalchemy import (
    String, Text, Numeric, Boolean, Integer, 
    ForeignKey, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.inventory import Inventory
    from app.models.review import Review


class Category(Base, TimestampMixin):
    """Product category with hierarchical support"""
    
    __tablename__ = "categories"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Self-referential for hierarchical categories
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Relationships
    parent: Mapped["Category | None"] = relationship(
        "Category",
        remote_side="Category.id",
        back_populates="children"
    )
    children: Mapped[List["Category"]] = relationship(
        "Category",
        back_populates="parent"
    )
    products: Mapped[List["Product"]] = relationship(
        "Product",
        secondary="product_categories",
        back_populates="categories"
    )
    
    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name={self.name})>"


class Product(Base, TimestampMixin):
    """Product model"""
    
    __tablename__ = "products"
    
    __table_args__ = (
        CheckConstraint("price > 0", name="price_positive"),
        CheckConstraint("discount_percent >= 0 AND discount_percent <= 100", name="discount_valid"),
    )
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    
    # Pricing
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )
    discount_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False
    )
    
    # Images
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    images: Mapped[List[str] | None] = mapped_column(Text, nullable=True)  # JSON array as text
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Metrics for ranking algorithm
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    purchase_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Relationships
    categories: Mapped[List["Category"]] = relationship(
        "Category",
        secondary="product_categories",
        back_populates="products"
    )
    inventory: Mapped["Inventory | None"] = relationship(
        "Inventory",
        back_populates="product",
        uselist=False
    )
    reviews: Mapped[List["Review"]] = relationship(
        "Review",
        back_populates="product",
        lazy="selectin"
    )
    
    @property
    def effective_price(self) -> Decimal:
        """Calculate price after discount"""
        if self.discount_percent > 0:
            discount = self.price * (self.discount_percent / 100)
            return self.price - discount
        return self.price
    
    @property
    def average_rating(self) -> float:
        """Calculate average rating from reviews"""
        if not self.reviews:
            return 0.0
        total = sum(r.rating for r in self.reviews)
        return total / len(self.reviews)
    
    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name={self.name})>"


class ProductCategory(Base):
    """Many-to-many relationship between products and categories"""
    
    __tablename__ = "product_categories"
    
    __table_args__ = (
        UniqueConstraint("product_id", "category_id", name="uq_product_category"),
    )
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
