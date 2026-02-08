"""
Payment API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.exceptions import NotFoundError, ValidationError, PaymentError
from app.services.payment import PaymentService
from app.schemas.payment import (
    PaymentCreate, PaymentResponse, 
    PaymentRetryRequest, PaymentSimulateRequest
)
from app.api.deps import get_current_active_user
from app.models.user import User


router = APIRouter()


@router.post("/process", response_model=PaymentResponse)
async def process_payment(
    data: PaymentCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Process a payment for an order.
    
    Payment is simulated for this demo.
    Uses idempotency_key to prevent duplicate charges.
    """
    payment_service = PaymentService(db)
    
    try:
        payment = await payment_service.process(data)
        
        return PaymentResponse(
            id=payment.id,
            order_id=payment.order_id,
            idempotency_key=payment.idempotency_key,
            amount=payment.amount,
            currency=payment.currency,
            method=payment.method,
            status=payment.status,
            provider=payment.provider,
            provider_transaction_id=payment.provider_transaction_id,
            card_last_four=payment.card_last_four,
            card_brand=payment.card_brand,
            retry_count=payment.retry_count,
            can_retry=payment.can_retry,
            error_message=payment.error_message,
            error_code=payment.error_code,
            created_at=payment.created_at,
            updated_at=payment.updated_at
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/simulate", response_model=PaymentResponse)
async def simulate_payment(
    data: PaymentSimulateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Simulate a payment for testing.
    
    Allows explicit control over success/failure.
    """
    payment_service = PaymentService(db)
    
    try:
        payment = await payment_service.process_simulated(data)
        
        return PaymentResponse(
            id=payment.id,
            order_id=payment.order_id,
            idempotency_key=payment.idempotency_key,
            amount=payment.amount,
            currency=payment.currency,
            method=payment.method,
            status=payment.status,
            provider=payment.provider,
            provider_transaction_id=payment.provider_transaction_id,
            card_last_four=payment.card_last_four,
            card_brand=payment.card_brand,
            retry_count=payment.retry_count,
            can_retry=payment.can_retry,
            error_message=payment.error_message,
            error_code=payment.error_code,
            created_at=payment.created_at,
            updated_at=payment.updated_at
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/retry", response_model=PaymentResponse)
async def retry_payment(
    data: PaymentRetryRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retry a failed payment.
    
    Max 3 retries allowed.
    """
    payment_service = PaymentService(db)
    
    try:
        payment = await payment_service.retry(data.payment_id)
        
        return PaymentResponse(
            id=payment.id,
            order_id=payment.order_id,
            idempotency_key=payment.idempotency_key,
            amount=payment.amount,
            currency=payment.currency,
            method=payment.method,
            status=payment.status,
            provider=payment.provider,
            provider_transaction_id=payment.provider_transaction_id,
            card_last_four=payment.card_last_four,
            card_brand=payment.card_brand,
            retry_count=payment.retry_count,
            can_retry=payment.can_retry,
            error_message=payment.error_message,
            error_code=payment.error_code,
            created_at=payment.created_at,
            updated_at=payment.updated_at
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get payment details.
    """
    payment_service = PaymentService(db)
    
    try:
        payment = await payment_service.get_by_id(payment_id)
        
        return PaymentResponse(
            id=payment.id,
            order_id=payment.order_id,
            idempotency_key=payment.idempotency_key,
            amount=payment.amount,
            currency=payment.currency,
            method=payment.method,
            status=payment.status,
            provider=payment.provider,
            provider_transaction_id=payment.provider_transaction_id,
            card_last_four=payment.card_last_four,
            card_brand=payment.card_brand,
            retry_count=payment.retry_count,
            can_retry=payment.can_retry,
            error_message=payment.error_message,
            error_code=payment.error_code,
            created_at=payment.created_at,
            updated_at=payment.updated_at
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
