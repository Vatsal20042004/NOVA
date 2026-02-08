"""
Delivery API Router
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_driver_user, get_current_admin_user, get_current_active_user
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.delivery import Delivery
from app.schemas.delivery import DeliveryCreate, DeliveryUpdate, DeliveryResponse
from app.services.delivery_service import DeliveryService

router = APIRouter()


@router.post("/assign", response_model=DeliveryResponse, status_code=status.HTTP_201_CREATED)
async def assign_delivery(
    *,
    db: AsyncSession = Depends(get_db),
    delivery_in: DeliveryCreate,
    current_user: User = Depends(get_current_admin_user)
):
    """
    Assign an order to a driver (Admin only).
    """
    service = DeliveryService(db)
    return await service.assign_delivery(delivery_in)


@router.get("/mine", response_model=List[DeliveryResponse])
async def read_my_deliveries(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_driver_user),
):
    """
    Get all deliveries assigned to current driver.
    """
    service = DeliveryService(db)
    return await service.get_driver_deliveries(current_user.id)


@router.patch("/{delivery_id}/status", response_model=DeliveryResponse)
async def update_delivery_status(
    *,
    db: AsyncSession = Depends(get_db),
    delivery_id: int,
    status_update: DeliveryUpdate,
    current_user: User = Depends(get_current_driver_user),
):
    """
    Update delivery status (Driver only).
    """
    service = DeliveryService(db)
    return await service.update_status(delivery_id, status_update, current_user.id)


@router.get("/{delivery_id}", response_model=DeliveryResponse)
async def read_delivery(
    *,
    db: AsyncSession = Depends(get_db),
    delivery_id: int,
    current_user: User = Depends(get_current_active_user),
):
    """
    Get delivery details.
    Accessible by Admin, the assigned Driver, or the Order owner.
    """
    delivery = await db.get(Delivery, delivery_id)
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found"
        )
    
    # Check permissions
    is_admin = current_user.role == UserRole.ADMIN
    is_driver = delivery.driver_id == current_user.id
    
    # We need to fetch the order to check if user is the owner
    # But for now, let's just allow admin and driver to see detailed info
    # TODO: Fetch order to check ownership if customer
    
    if not (is_admin or is_driver):
         # If not admin or driver, check if user owns the order
         order = await delivery.awaitable_attrs.order
         if order.user_id != current_user.id:
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this delivery"
            )
            
    return delivery
