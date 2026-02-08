"""
Payment schemas
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from app.models.payment import PaymentStatus, PaymentMethod


class PaymentCreate(BaseModel):
    """Payment creation schema"""
    order_id: int
    method: PaymentMethod
    card_number: Optional[str] = Field(None, min_length=16, max_length=16)
    card_expiry: Optional[str] = None  # MM/YY format
    card_cvv: Optional[str] = Field(None, min_length=3, max_length=4)
    idempotency_key: Optional[str] = None  # Auto-generated if not provided


class PaymentResponse(BaseModel):
    """Payment response schema"""
    id: int
    order_id: int
    idempotency_key: str
    amount: Decimal
    currency: str
    method: PaymentMethod
    status: PaymentStatus
    provider: Optional[str] = None
    provider_transaction_id: Optional[str] = None
    card_last_four: Optional[str] = None
    card_brand: Optional[str] = None
    retry_count: int
    can_retry: bool
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class PaymentRetryRequest(BaseModel):
    """Payment retry request schema"""
    payment_id: int


class PaymentSimulateRequest(BaseModel):
    """Simulated payment request (for testing)"""
    order_id: int
    method: PaymentMethod = PaymentMethod.CREDIT_CARD
    should_succeed: bool = True  # For testing failures
    delay_seconds: int = Field(default=0, ge=0, le=10)


class PaymentRefundRequest(BaseModel):
    """Payment refund request"""
    payment_id: int
    amount: Optional[Decimal] = None  # Full refund if not specified
    reason: Optional[str] = None


class PaymentRefundResponse(BaseModel):
    """Payment refund response"""
    success: bool
    payment_id: int
    refund_amount: Decimal
    message: str
