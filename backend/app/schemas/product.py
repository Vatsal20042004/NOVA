"""
Product schemas
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator


class ProductBase(BaseModel):
    """Base product schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    price: Decimal = Field(..., gt=0, decimal_places=2)
    discount_percent: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    image_url: Optional[str] = None
    is_active: bool = True
    is_featured: bool = False


class ProductCreate(ProductBase):
    """Product creation schema"""
    slug: Optional[str] = None
    category_ids: List[int] = Field(default_factory=list)
    initial_stock: int = Field(default=0, ge=0)
    
    @field_validator("slug", mode="before")
    @classmethod
    def generate_slug(cls, v: Optional[str], info) -> str:
        """Generate slug from name if not provided"""
        if v:
            return v.lower().replace(" ", "-")
        # Will be generated in service from name
        return v


class ProductUpdate(BaseModel):
    """Product update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=0)
    discount_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    image_url: Optional[str] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    category_ids: Optional[List[int]] = None


class ProductResponse(BaseModel):
    """Product response schema"""
    id: int
    name: str
    description: Optional[str] = None
    slug: str
    price: Decimal
    discount_percent: Decimal
    effective_price: Decimal
    image_url: Optional[str] = None
    is_active: bool
    is_featured: bool
    view_count: int
    purchase_count: int
    average_rating: float
    review_count: int = 0
    stock_available: int = 0
    is_in_stock: bool = True
    categories: List["CategoryBrief"] = []
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ProductBrief(BaseModel):
    """Brief product info for lists"""
    id: int
    name: str
    slug: str
    price: Decimal
    effective_price: Decimal
    image_url: Optional[str] = None
    average_rating: float
    review_count: int = 0
    is_in_stock: bool = True
    
    model_config = ConfigDict(from_attributes=True)


class ProductListResponse(BaseModel):
    """Paginated product list response"""
    products: List[ProductBrief]
    total: int
    page: int
    per_page: int
    pages: int


class ProductSearchRequest(BaseModel):
    """Product search request"""
    query: Optional[str] = None
    category_id: Optional[int] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    in_stock_only: bool = False
    sort_by: str = Field(default="relevance", pattern="^(relevance|price_asc|price_desc|rating|newest)$")
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)


class CategoryBrief(BaseModel):
    """Brief category info for product response"""
    id: int
    name: str
    slug: str
    
    model_config = ConfigDict(from_attributes=True)


# Update forward references
ProductResponse.model_rebuild()
