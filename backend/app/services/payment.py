"""
Payment Service
Handles payment processing with retry logic
"""

import uuid
import random
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    NotFoundError,
    PaymentError,
    ValidationError
)
from app.models.payment import Payment, PaymentStatus, PaymentMethod
from app.models.order import Order, OrderStatus
from app.services.order import OrderService
from app.schemas.payment import PaymentCreate, PaymentSimulateRequest


class PaymentService:
    """
    Payment processing service with simulated payment gateway.
    
    Features:
    - Idempotent payments using idempotency_key
    - Retry logic with exponential backoff
    - Simulated success/failure for testing
    """
    
    MAX_RETRIES = 3
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.order_service = OrderService(db)
    
    async def get_by_id(self, payment_id: int) -> Payment:
        """Get payment by ID"""
        result = await self.db.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        payment = result.scalar_one_or_none()
        
        if not payment:
            raise NotFoundError("Payment", payment_id)
        
        return payment
    
    async def get_by_order_id(self, order_id: int) -> Optional[Payment]:
        """Get payment for an order"""
        result = await self.db.execute(
            select(Payment).where(Payment.order_id == order_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_idempotency_key(self, key: str) -> Optional[Payment]:
        """Get payment by idempotency key"""
        result = await self.db.execute(
            select(Payment).where(Payment.idempotency_key == key)
        )
        return result.scalar_one_or_none()
    
    async def process(self, data: PaymentCreate) -> Payment:
        """
        Process a payment for an order.
        
        Uses idempotency key to prevent duplicate charges.
        
        Args:
            data: Payment creation data
            
        Returns:
            Payment object
        """
        # Generate idempotency key if not provided
        idempotency_key = data.idempotency_key or f"pay_{uuid.uuid4().hex}"
        
        # Check for existing payment with same idempotency key
        existing = await self.get_by_idempotency_key(idempotency_key)
        if existing:
            return existing
        
        # Get and validate order
        order = await self.order_service.get_by_id(data.order_id)
        
        if order.status != OrderStatus.PENDING:
            raise ValidationError(
                f"Cannot process payment for order with status '{order.status.value}'"
            )
        
        # Check for existing payment on this order
        existing_payment = await self.get_by_order_id(data.order_id)
        if existing_payment and existing_payment.status == PaymentStatus.COMPLETED:
            raise ValidationError("Order already has a completed payment")
        
        # Create payment record
        payment = Payment(
            order_id=data.order_id,
            idempotency_key=idempotency_key,
            amount=order.total_amount,
            currency="USD",
            method=data.method,
            status=PaymentStatus.PROCESSING
        )
        
        # Extract card info if provided
        if data.card_number:
            payment.card_last_four = data.card_number[-4:]
            payment.card_brand = self._detect_card_brand(data.card_number)
        
        self.db.add(payment)
        await self.db.flush()
        
        # Process payment (simulated)
        success, error_message, error_code = await self._process_payment(payment)
        
        if success:
            payment.status = PaymentStatus.COMPLETED
            payment.provider = "simulated"
            payment.provider_transaction_id = f"txn_{uuid.uuid4().hex[:12]}"
            
            # Confirm the order
            await self.order_service.confirm_payment(data.order_id)
        else:
            payment.status = PaymentStatus.FAILED
            payment.error_message = error_message
            payment.error_code = error_code
        
        await self.db.commit()
        await self.db.refresh(payment)
        
        return payment
    
    async def process_simulated(
        self,
        data: PaymentSimulateRequest
    ) -> Payment:
        """
        Process a simulated payment for testing.
        
        Allows explicit control over success/failure.
        """
        order = await self.order_service.get_by_id(data.order_id)
        
        idempotency_key = f"sim_{uuid.uuid4().hex}"
        
        payment = Payment(
            order_id=data.order_id,
            idempotency_key=idempotency_key,
            amount=order.total_amount,
            currency="USD",
            method=data.method,
            status=PaymentStatus.PROCESSING,
            provider="simulated"
        )
        
        self.db.add(payment)
        await self.db.flush()
        
        if data.should_succeed:
            payment.status = PaymentStatus.COMPLETED
            payment.provider_transaction_id = f"sim_txn_{uuid.uuid4().hex[:12]}"
            await self.order_service.confirm_payment(data.order_id)
        else:
            payment.status = PaymentStatus.FAILED
            payment.error_message = "Simulated payment failure"
            payment.error_code = "SIM_FAIL"
        
        await self.db.commit()
        await self.db.refresh(payment)
        
        return payment
    
    async def retry(self, payment_id: int) -> Payment:
        """
        Retry a failed payment.
        
        Uses exponential backoff tracking.
        """
        payment = await self.get_by_id(payment_id)
        
        if not payment.can_retry:
            raise ValidationError(
                f"Payment cannot be retried. Status: {payment.status.value}, "
                f"Retries: {payment.retry_count}/{payment.max_retries}"
            )
        
        payment.retry_count += 1
        payment.status = PaymentStatus.PROCESSING
        payment.error_message = None
        payment.error_code = None
        
        # Process payment (simulated with higher success rate on retry)
        success, error_message, error_code = await self._process_payment(
            payment, 
            retry=True
        )
        
        if success:
            payment.status = PaymentStatus.COMPLETED
            payment.provider_transaction_id = f"txn_{uuid.uuid4().hex[:12]}"
            
            # Confirm the order
            await self.order_service.confirm_payment(payment.order_id)
        else:
            payment.status = PaymentStatus.FAILED
            payment.error_message = error_message
            payment.error_code = error_code
        
        await self.db.commit()
        await self.db.refresh(payment)
        
        return payment
    
    async def refund(
        self,
        payment_id: int,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None
    ) -> Payment:
        """
        Refund a completed payment.
        
        Args:
            payment_id: Payment to refund
            amount: Amount to refund (full refund if None)
            reason: Reason for refund
        """
        payment = await self.get_by_id(payment_id)
        
        if payment.status != PaymentStatus.COMPLETED:
            raise ValidationError(
                f"Cannot refund payment with status '{payment.status.value}'"
            )
        
        refund_amount = amount or payment.amount
        
        if refund_amount > payment.amount:
            raise ValidationError("Refund amount exceeds payment amount")
        
        # Process refund (simulated - always succeeds)
        payment.status = PaymentStatus.REFUNDED
        payment.error_message = reason
        
        # Update order status
        order = await self.order_service.get_by_id(payment.order_id)
        order.status = OrderStatus.REFUNDED
        
        await self.db.commit()
        await self.db.refresh(payment)
        
        return payment
    
    async def _process_payment(
        self,
        payment: Payment,
        retry: bool = False
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Simulate payment processing.
        
        Returns:
            Tuple of (success, error_message, error_code)
        """
        # Simulate processing time would go here
        
        # Simulate success/failure
        # Higher success rate on retries
        success_rate = 0.95 if retry else 0.85
        
        if random.random() < success_rate:
            return True, None, None
        else:
            # Random failure reasons
            failures = [
                ("Card declined", "CARD_DECLINED"),
                ("Insufficient funds", "INSUFFICIENT_FUNDS"),
                ("Network error", "NETWORK_ERROR"),
                ("Processing error", "PROCESSING_ERROR"),
            ]
            error_msg, error_code = random.choice(failures)
            return False, error_msg, error_code
    
    def _detect_card_brand(self, card_number: str) -> str:
        """Detect card brand from card number"""
        if card_number.startswith("4"):
            return "Visa"
        elif card_number.startswith(("51", "52", "53", "54", "55")):
            return "Mastercard"
        elif card_number.startswith(("34", "37")):
            return "Amex"
        elif card_number.startswith("6011"):
            return "Discover"
        else:
            return "Unknown"
