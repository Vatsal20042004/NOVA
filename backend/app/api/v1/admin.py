"""
Admin API endpoints
Includes inventory management and simulation endpoints
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.exceptions import NotFoundError
from app.services.inventory import InventoryService
from app.services.user import UserService
from app.services.order import OrderService
from app.schemas.inventory import (
    InventoryResponse, InventoryReserveRequest, 
    InventoryReleaseRequest, RestockRequest
)
from app.schemas.user import UserResponse
from app.schemas.order import OrderResponse, OrderUpdate
from app.api.deps import get_current_admin_user
from app.models.user import User, UserRole
from app.models.order import OrderStatus


router = APIRouter()


# ==================== Inventory Management ====================

@router.post("/inventory/reserve", response_model=dict)
async def reserve_inventory(
    data: InventoryReserveRequest,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Reserve inventory for a product (admin only).
    """
    inventory_service = InventoryService(db)
    
    try:
        success, available = await inventory_service.reserve(
            product_id=data.product_id,
            quantity=data.quantity
        )
        return {
            "success": success,
            "product_id": data.product_id,
            "quantity_reserved": data.quantity,
            "available_after": available
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/inventory/release", response_model=dict)
async def release_inventory(
    data: InventoryReleaseRequest,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Release reserved inventory (admin only).
    """
    inventory_service = InventoryService(db)
    
    try:
        available = await inventory_service.release(
            product_id=data.product_id,
            quantity=data.quantity
        )
        return {
            "success": True,
            "product_id": data.product_id,
            "quantity_released": data.quantity,
            "available_after": available
        }
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/inventory/restock", response_model=InventoryResponse)
async def restock_inventory(
    data: RestockRequest,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Add stock to inventory (admin only).
    """
    inventory_service = InventoryService(db)
    
    try:
        inventory = await inventory_service.restock(
            product_id=data.product_id,
            quantity=data.quantity
        )
        return InventoryResponse(
            id=inventory.id,
            product_id=inventory.product_id,
            product_name="",
            quantity=inventory.quantity,
            reserved=inventory.reserved,
            available=inventory.available,
            warehouse_id=inventory.warehouse_id,
            version=inventory.version,
            low_stock_threshold=inventory.low_stock_threshold,
            is_low_stock=inventory.is_low_stock,
            is_out_of_stock=inventory.is_out_of_stock,
            created_at=inventory.created_at,
            updated_at=inventory.updated_at
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/inventory/low-stock", response_model=list[InventoryResponse])
async def get_low_stock(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get products with low stock (admin only).
    """
    inventory_service = InventoryService(db)
    inventories = await inventory_service.get_low_stock(limit)
    
    return [
        InventoryResponse(
            id=inv.id,
            product_id=inv.product_id,
            product_name="",
            quantity=inv.quantity,
            reserved=inv.reserved,
            available=inv.available,
            warehouse_id=inv.warehouse_id,
            version=inv.version,
            low_stock_threshold=inv.low_stock_threshold,
            is_low_stock=inv.is_low_stock,
            is_out_of_stock=inv.is_out_of_stock,
            created_at=inv.created_at,
            updated_at=inv.updated_at
        )
        for inv in inventories
    ]


# ==================== User Management ====================

@router.get("/users", response_model=list[UserResponse])
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    role: Optional[UserRole] = None,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all users (admin only).
    """
    user_service = UserService(db)
    users, total = await user_service.list_users(page, per_page, role)
    return users


@router.put("/users/{user_id}/role", response_model=UserResponse)
async def set_user_role(
    user_id: int,
    role: UserRole,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Set user role (admin only).
    """
    user_service = UserService(db)
    
    try:
        user = await user_service.set_role(user_id, role)
        return user
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/users/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Deactivate a user account (admin only).
    """
    user_service = UserService(db)
    
    try:
        user = await user_service.deactivate(user_id)
        return user
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ==================== Order Management ====================

@router.put("/orders/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    order_status: OrderStatus,
    tracking_number: Optional[str] = None,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update order status (admin only).
    """
    order_service = OrderService(db)
    
    try:
        order = await order_service.update_status(
            order_id=order_id,
            status=order_status,
            tracking_number=tracking_number
        )
        return order
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== Simulation Endpoints ====================

@router.post("/simulate/db-down")
async def simulate_db_down(
    current_user: User = Depends(get_current_admin_user)
):
    """
    Simulate database failure (for testing error handling).
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Simulated database failure"
    )


@router.post("/simulate/slow-response")
async def simulate_slow_response(
    delay_seconds: int = Query(5, ge=1, le=30),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Simulate slow response (for testing timeouts).
    """
    import asyncio
    await asyncio.sleep(delay_seconds)
    return {"message": f"Response after {delay_seconds} seconds delay"}


@router.post("/simulate/error")
async def simulate_error(
    error_code: int = Query(500, ge=400, le=599),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Simulate HTTP error (for testing error handling).
    """
    raise HTTPException(
        status_code=error_code,
        detail=f"Simulated {error_code} error"
    )
