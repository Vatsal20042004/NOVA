"""
Review schemas
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ReviewBase(BaseModel):
    """Base review schema"""
    rating: int = Field(..., ge=1, le=5)
    title: Optional[str] = Field(None, max_length=255)
    comment: Optional[str] = None


class ReviewCreate(ReviewBase):
    """Review creation schema"""
    product_id: int


class ReviewUpdate(BaseModel):
    """Review update schema"""
    rating: Optional[int] = Field(None, ge=1, le=5)
    title: Optional[str] = Field(None, max_length=255)
    comment: Optional[str] = None


class ReviewResponse(BaseModel):
    """Review response schema"""
    id: int
    user_id: int
    user_name: str = ""
    product_id: int
    rating: int
    title: Optional[str] = None
    comment: Optional[str] = None
    is_verified_purchase: bool
    helpful_count: int
    not_helpful_count: int
    helpfulness_ratio: float
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ReviewListResponse(BaseModel):
    """Paginated review list response"""
    reviews: List[ReviewResponse]
    total: int
    page: int
    per_page: int
    pages: int
    average_rating: float
    rating_distribution: dict[int, int]  # {1: count, 2: count, ...}


class ReviewHelpfulRequest(BaseModel):
    """Mark review as helpful/not helpful"""
    helpful: bool
