"""
Delivery Schemas
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.models.delivery import DeliveryStatus


# Base Schema
class DeliveryBase(BaseModel):
    current_location: Optional[str] = None
    delivery_notes: Optional[str] = None


# Create Schema
class DeliveryCreate(DeliveryBase):
    order_id: int
    driver_id: int


# Update Schema
class DeliveryUpdate(DeliveryBase):
    status: Optional[DeliveryStatus] = None
    proof_of_delivery: Optional[str] = None
    picked_up_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None


# Response Schema
class DeliveryResponse(DeliveryBase):
    id: int
    order_id: int
    driver_id: Optional[int]
    status: DeliveryStatus
    proof_of_delivery: Optional[str]
    picked_up_at: Optional[datetime]
    delivered_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
