"""
Inventory schemas
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class InventoryBase(BaseModel):
    """Base inventory schema"""
    quantity: int = Field(..., ge=0)
    low_stock_threshold: int = Field(default=10, ge=0)
    warehouse_id: Optional[str] = None


class InventoryCreate(InventoryBase):
    """Inventory creation schema"""
    product_id: int


class InventoryUpdate(BaseModel):
    """Inventory update schema"""
    quantity: Optional[int] = Field(None, ge=0)
    low_stock_threshold: Optional[int] = Field(None, ge=0)
    warehouse_id: Optional[str] = None


class InventoryResponse(BaseModel):
    """Inventory response schema"""
    id: int
    product_id: int
    product_name: str = ""
    quantity: int
    reserved: int
    available: int
    warehouse_id: Optional[str] = None
    version: int
    low_stock_threshold: int
    is_low_stock: bool
    is_out_of_stock: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class InventoryReserveRequest(BaseModel):
    """Request to reserve inventory"""
    product_id: int
    quantity: int = Field(..., gt=0)
    order_id: Optional[int] = None  # For tracking


class InventoryReserveResponse(BaseModel):
    """Response for inventory reservation"""
    success: bool
    product_id: int
    quantity_reserved: int
    available_after: int
    message: str


class InventoryReleaseRequest(BaseModel):
    """Request to release reserved inventory"""
    product_id: int
    quantity: int = Field(..., gt=0)
    order_id: Optional[int] = None


class InventoryBulkReserveRequest(BaseModel):
    """Bulk reserve multiple products"""
    items: List[InventoryReserveRequest]


class InventoryBulkReserveResponse(BaseModel):
    """Response for bulk reservation"""
    success: bool
    reserved: List[InventoryReserveResponse]
    failed: List[InventoryReserveResponse]


class RestockRequest(BaseModel):
    """Request to restock inventory"""
    product_id: int
    quantity: int = Field(..., gt=0)
    warehouse_id: Optional[str] = None
