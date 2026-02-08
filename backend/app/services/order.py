"""
Order Service
Handles order creation with transactional integrity
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    NotFoundError,
    ValidationError,
    ConflictError,
    InsufficientStockError
)
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.models.user import User
from app.services.inventory import InventoryService
from app.schemas.order import OrderCreate, OrderUpdate


class OrderService:
    """
    Order management service with transactional support.
    
    Implements ACID properties:
    - Atomicity: Order creation is all-or-nothing
    - Consistency: Inventory is properly reserved
    - Isolation: Uses database transactions
    - Durability: Committed orders are persisted
    """
    
    TAX_RATE = Decimal("0.08")  # 8% tax
    FREE_SHIPPING_THRESHOLD = Decimal("5000.00")  # INR
    SHIPPING_COST = Decimal("499.00")  # INR
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.inventory_service = InventoryService(db)
    
    async def get_by_id(self, order_id: int) -> Order:
        """Get order by ID with all items"""
        result = await self.db.execute(
            select(Order)
            .options(
                selectinload(Order.items),
                selectinload(Order.delivery)
            )
            .where(Order.id == order_id)
            .execution_options(populate_existing=True)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise NotFoundError("Order", order_id)
        
        return order
    
    async def get_by_order_number(self, order_number: str) -> Order:
        """Get order by order number"""
        result = await self.db.execute(
            select(Order)
            .options(
                selectinload(Order.items),
                selectinload(Order.delivery)
            )
            .where(Order.order_number == order_number)
            .execution_options(populate_existing=True)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise NotFoundError("Order", order_number)
        
        return order
    
    async def get_by_request_id(self, request_id: str) -> Optional[Order]:
        """Get order by idempotency key (request_id)"""
        result = await self.db.execute(
            select(Order)
            .options(
                selectinload(Order.items),
                selectinload(Order.delivery)
            )
            .where(Order.request_id == request_id)
            .execution_options(populate_existing=True)
        )
        return result.scalar_one_or_none()
    
    async def list_by_user(
        self,
        user_id: int,
        page: int = 1,
        per_page: int = 20,
        status: Optional[OrderStatus] = None
    ) -> Tuple[List[Order], int]:
        """
        List orders for a user with pagination.
        
        Returns:
            Tuple of (orders list, total count)
        """
        query = (
            select(Order)
            .options(
                selectinload(Order.items),
                selectinload(Order.delivery)
            )
            .where(Order.user_id == user_id)
            .execution_options(populate_existing=True)
        )
        count_query = (
            select(func.count(Order.id))
            .where(Order.user_id == user_id)
        )
        
        if status:
            query = query.where(Order.status == status)
            count_query = count_query.where(Order.status == status)
        
        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Get paginated results
        query = (
            query
            .order_by(Order.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        
        result = await self.db.execute(query)
        orders = list(result.scalars().unique().all())
        
        return orders, total
    
    async def create(
        self,
        user_id: int,
        data: OrderCreate
    ) -> Order:
        """
        Create a new order with inventory reservation.
        
        This is a transactional operation:
        1. Check idempotency key
        2. Validate products exist and are active
        3. Reserve inventory for all items
        4. Create order and order items
        5. Calculate totals
        6. Commit transaction
        
        On any failure, all changes are rolled back.
        
        Args:
            user_id: User placing the order
            data: Order creation data
            
        Returns:
            Created order
        """
        # Check idempotency - return existing order if request_id matches
        if data.request_id:
            existing = await self.get_by_request_id(data.request_id)
            if existing:
                return existing
        
        # Generate order number
        order_number = self._generate_order_number()
        
        # Validate and get products
        products = await self._validate_products(data.items)
        
        # Reserve inventory for all items
        reserved_items = []
        try:
            for item in data.items:
                await self.inventory_service.reserve(
                    product_id=item.product_id,
                    quantity=item.quantity,
                    use_redis_lock=True
                )
                reserved_items.append(item)
        except (InsufficientStockError, Exception) as e:
            # Rollback any reservations made
            for reserved in reserved_items:
                try:
                    await self.inventory_service.release(
                        product_id=reserved.product_id,
                        quantity=reserved.quantity
                    )
                except:
                    pass
            raise
        
        # Calculate order totals
        subtotal = Decimal("0.00")
        order_items = []
        
        for item_data in data.items:
            product = products[item_data.product_id]
            unit_price = product.effective_price
            
            order_item = OrderItem(
                product_id=product.id,
                product_name=product.name,
                product_image_url=product.image_url,
                quantity=item_data.quantity,
                unit_price=unit_price
            )
            order_items.append(order_item)
            subtotal += unit_price * item_data.quantity
        
        # Calculate shipping
        shipping_amount = (
            Decimal("0.00") 
            if subtotal >= self.FREE_SHIPPING_THRESHOLD 
            else self.SHIPPING_COST
        )
        
        # Calculate tax
        tax_amount = subtotal * self.TAX_RATE
        
        # Total
        total_amount = subtotal + tax_amount + shipping_amount
        
        # Create order
        order = Order(
            order_number=order_number,
            request_id=data.request_id,
            user_id=user_id,
            status=OrderStatus.PENDING,
            subtotal=subtotal,
            tax_amount=tax_amount,
            shipping_amount=shipping_amount,
            discount_amount=Decimal("0.00"),
            total_amount=total_amount,
            shipping_address_line1=data.shipping_address.address_line1,
            shipping_address_line2=data.shipping_address.address_line2,
            shipping_city=data.shipping_address.city,
            shipping_state=data.shipping_address.state,
            shipping_postal_code=data.shipping_address.postal_code,
            shipping_country=data.shipping_address.country,
            notes=data.notes
        )
        
        self.db.add(order)
        await self.db.flush()
        
        # Add order items
        for order_item in order_items:
            order_item.order_id = order.id
            self.db.add(order_item)
        
        # Update product purchase counts
        for item_data in data.items:
            product = products[item_data.product_id]
            product.purchase_count += item_data.quantity
        
        await self.db.commit()
        await self.db.refresh(order)
        
        return order
    
    async def update_status(
        self,
        order_id: int,
        status: OrderStatus,
        tracking_number: Optional[str] = None
    ) -> Order:
        """Update order status"""
        order = await self.get_by_id(order_id)
        
        # Validate status transition
        self._validate_status_transition(order.status, status)
        
        order.status = status
        
        if tracking_number:
            order.tracking_number = tracking_number
        
        # Update timestamps based on status
        now = datetime.now(timezone.utc)
        if status == OrderStatus.SHIPPED:
            order.shipped_at = now
        elif status == OrderStatus.DELIVERED:
            order.delivered_at = now
        elif status == OrderStatus.CANCELLED:
            order.cancelled_at = now
            # Release inventory
            await self._release_order_inventory(order)
        
        await self.db.commit()
        await self.db.refresh(order)
        
        return order
    
    async def cancel(
        self,
        order_id: int,
        user_id: int,
        reason: Optional[str] = None
    ) -> Order:
        """
        Cancel an order and release inventory.
        
        Can only cancel pending or confirmed orders.
        """
        order = await self.get_by_id(order_id)
        
        # Verify ownership
        if order.user_id != user_id:
            raise ValidationError("Cannot cancel another user's order")
        
        # Check if cancellable
        if order.status not in (OrderStatus.PENDING, OrderStatus.CONFIRMED):
            raise ValidationError(
                f"Cannot cancel order with status '{order.status.value}'"
            )
        
        # Update status
        order.status = OrderStatus.CANCELLED
        order.cancelled_at = datetime.now(timezone.utc)
        if reason:
            order.notes = f"Cancelled: {reason}"
        
        # Release inventory
        await self._release_order_inventory(order)
        
        await self.db.commit()
        await self.db.refresh(order)
        
        return order
    
    async def confirm_payment(self, order_id: int) -> Order:
        """Confirm order after successful payment"""
        order = await self.get_by_id(order_id)
        
        if order.status != OrderStatus.PENDING:
            raise ValidationError(
                f"Cannot confirm order with status '{order.status.value}'"
            )
        
        order.status = OrderStatus.CONFIRMED
        
        # Confirm inventory (deduct from actual stock)
        for item in order.items:
            await self.inventory_service.confirm(
                product_id=item.product_id,
                quantity=item.quantity
            )
        
        await self.db.commit()
        await self.db.refresh(order)
        
        return order
    
    async def _validate_products(
        self,
        items: List
    ) -> dict[int, Product]:
        """Validate products exist and are active"""
        product_ids = [item.product_id for item in items]
        
        result = await self.db.execute(
            select(Product)
            .where(
                and_(
                    Product.id.in_(product_ids),
                    Product.is_active == True
                )
            )
        )
        products = {p.id: p for p in result.scalars().all()}
        
        # Check all products found
        missing = set(product_ids) - set(products.keys())
        if missing:
            raise ValidationError(
                f"Products not found or inactive: {missing}"
            )
        
        return products
    
    async def _release_order_inventory(self, order: Order) -> None:
        """Release inventory for all items in an order"""
        for item in order.items:
            if item.product_id:
                try:
                    await self.inventory_service.release(
                        product_id=item.product_id,
                        quantity=item.quantity
                    )
                except NotFoundError:
                    pass  # Product may have been deleted
    
    def _validate_status_transition(
        self,
        current: OrderStatus,
        new: OrderStatus
    ) -> None:
        """Validate order status transition is allowed"""
        valid_transitions = {
            OrderStatus.PENDING: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
            OrderStatus.CONFIRMED: {OrderStatus.PROCESSING, OrderStatus.CANCELLED},
            OrderStatus.PROCESSING: {OrderStatus.SHIPPED, OrderStatus.CANCELLED},
            OrderStatus.SHIPPED: {OrderStatus.DELIVERED},
            OrderStatus.DELIVERED: {OrderStatus.REFUNDED},
            OrderStatus.CANCELLED: set(),
            OrderStatus.REFUNDED: set(),
        }
        
        if new not in valid_transitions.get(current, set()):
            raise ValidationError(
                f"Cannot transition from '{current.value}' to '{new.value}'"
            )
    
    def _generate_order_number(self) -> str:
        """Generate unique order number"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = uuid.uuid4().hex[:6].upper()
        return f"ORD-{timestamp}-{unique_id}"
