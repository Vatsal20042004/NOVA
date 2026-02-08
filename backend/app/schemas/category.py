"""
Category schemas
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class CategoryBase(BaseModel):
    """Base category schema"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    image_url: Optional[str] = None
    parent_id: Optional[int] = None


class CategoryCreate(CategoryBase):
    """Category creation schema"""
    slug: Optional[str] = None


class CategoryUpdate(BaseModel):
    """Category update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    image_url: Optional[str] = None
    parent_id: Optional[int] = None
    slug: Optional[str] = None


class CategoryResponse(BaseModel):
    """Category response schema"""
    id: int
    name: str
    description: Optional[str] = None
    slug: str
    image_url: Optional[str] = None
    parent_id: Optional[int] = None
    product_count: int = 0
    children: List["CategoryResponse"] = []
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class CategoryBrief(BaseModel):
    """Brief category info"""
    id: int
    name: str
    slug: str
    
    model_config = ConfigDict(from_attributes=True)


class CategoryTreeResponse(BaseModel):
    """Category tree response"""
    categories: List[CategoryResponse]


# Update forward references
CategoryResponse.model_rebuild()
