"""
Order schemas
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

from app.models.order import OrderStatus
from app.schemas.delivery import DeliveryResponse


class OrderItemCreate(BaseModel):
    """Order item creation schema"""
    product_id: int
    quantity: int = Field(..., gt=0)


class OrderItemResponse(BaseModel):
    """Order item response schema"""
    id: int
    product_id: Optional[int]
    product_name: str
    product_image_url: Optional[str] = None
    quantity: int
    unit_price: Decimal
    total_price: Decimal
    
    model_config = ConfigDict(from_attributes=True)


class ShippingAddress(BaseModel):
    """Shipping address schema"""
    address_line1: str = Field(..., min_length=1, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=1, max_length=100)
    postal_code: str = Field(..., min_length=1, max_length=20)
    country: str = Field(..., min_length=1, max_length=100)


class OrderCreate(BaseModel):
    """Order creation schema"""
    items: List[OrderItemCreate] = Field(..., min_length=1)
    shipping_address: ShippingAddress
    notes: Optional[str] = None
    request_id: Optional[str] = None  # For idempotency


class OrderUpdate(BaseModel):
    """Order update schema (admin)"""
    status: Optional[OrderStatus] = None
    tracking_number: Optional[str] = None
    notes: Optional[str] = None


class OrderResponse(BaseModel):
    """Order response schema"""
    id: int
    order_number: str
    user_id: int
    status: OrderStatus
    subtotal: Decimal
    tax_amount: Decimal
    shipping_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    item_count: int
    items: List[OrderItemResponse]
    shipping_address_line1: Optional[str] = None
    shipping_address_line2: Optional[str] = None
    shipping_city: Optional[str] = None
    shipping_state: Optional[str] = None
    shipping_postal_code: Optional[str] = None
    shipping_country: Optional[str] = None
    notes: Optional[str] = None
    tracking_number: Optional[str] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    delivery: Optional[DeliveryResponse] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class OrderBrief(BaseModel):
    """Brief order info for lists"""
    id: int
    order_number: str
    status: OrderStatus
    total_amount: Decimal
    item_count: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class OrderListResponse(BaseModel):
    """Paginated order list response"""
    orders: List[OrderBrief]
    total: int
    page: int
    per_page: int
    pages: int


class OrderCancelRequest(BaseModel):
    """Order cancellation request"""
    reason: Optional[str] = None
