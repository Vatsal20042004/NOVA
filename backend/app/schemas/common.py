"""
Common schema types used across the application
"""

from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class MessageResponse(BaseModel):
    """Standard message response"""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Standard error response"""
    message: str
    success: bool = False
    details: Optional[dict[str, Any]] = None
    error_code: Optional[str] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper"""
    items: List[T]
    total: int
    page: int
    per_page: int
    pages: int
    
    model_config = ConfigDict(from_attributes=True)
    
    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        per_page: int
    ) -> "PaginatedResponse[T]":
        """Create paginated response from items"""
        pages = (total + per_page - 1) // per_page if per_page > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages
        )


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    version: str
    database: str = "connected"
    redis: str = "connected"
