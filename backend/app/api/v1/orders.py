"""
Order API endpoints
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.exceptions import NotFoundError, ValidationError, InsufficientStockError
from app.services.order import OrderService
from app.schemas.order import (
    OrderCreate, OrderUpdate, OrderResponse, 
    OrderListResponse, OrderBrief, OrderCancelRequest
)
from app.api.deps import get_current_active_user, rate_limit_default
from app.models.user import User
from app.models.order import OrderStatus


router = APIRouter()


@router.get("", response_model=OrderListResponse)
async def list_orders(
    _: None = Depends(rate_limit_default),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[OrderStatus] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List current user's orders.
    """
    order_service = OrderService(db)
    
    orders, total = await order_service.list_by_user(
        user_id=current_user.id,
        page=page,
        per_page=per_page,
        status=status
    )
    
    pages = (total + per_page - 1) // per_page if per_page > 0 else 0
    
    return OrderListResponse(
        orders=[
            OrderBrief(
                id=o.id,
                order_number=o.order_number,
                status=o.status,
                total_amount=o.total_amount,
                item_count=o.item_count,
                created_at=o.created_at
            )
            for o in orders
        ],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages
    )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    _: None = Depends(rate_limit_default),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get order details.
    """
    order_service = OrderService(db)
    
    try:
        order = await order_service.get_by_id(order_id)
        
        # Verify ownership (unless admin)
        from app.models.user import UserRole
        if order.user_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot view another user's order"
            )
        
        return order
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    data: OrderCreate,
    _: None = Depends(rate_limit_default),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    x_request_id: Optional[str] = Header(None)
):
    """
    Create a new order.
    
    This is a transactional operation that:
    1. Validates products exist and are active
    2. Reserves inventory for all items
    3. Creates the order with calculated totals
    
    Use X-Request-ID header for idempotency.
    """
    order_service = OrderService(db)
    
    # Use request ID for idempotency
    if x_request_id:
        data.request_id = x_request_id
    
    try:
        order = await order_service.create(
            user_id=current_user.id,
            data=data
        )
        return order
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except InsufficientStockError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: int,
    _: None = Depends(rate_limit_default),
    data: Optional[OrderCancelRequest] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel an order.
    
    Can only cancel orders with status: pending, confirmed.
    """
    order_service = OrderService(db)
    
    reason = data.reason if data else None
    
    try:
        order = await order_service.cancel(
            order_id=order_id,
            user_id=current_user.id,
            reason=reason
        )
        return order
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
