"""
Delivery Service
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.delivery import Delivery, DeliveryStatus
from app.models.user import User, UserRole
from app.models.order import Order
from app.schemas.delivery import DeliveryCreate, DeliveryUpdate


class DeliveryService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def assign_delivery(self, delivery_in: DeliveryCreate) -> Delivery:
        """Assign an order to a driver"""
        # Validate Driver
        driver = await self.session.get(User, delivery_in.driver_id)
        if not driver or driver.role != UserRole.DRIVER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid driver"
            )

        # Validate Order
        order = await self.session.get(Order, delivery_in.order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
            
        # Check if delivery already exists
        stmt = select(Delivery).where(Delivery.order_id == delivery_in.order_id)
        result = await self.session.execute(stmt)
        existing_delivery = result.scalar_one_or_none()
        
        if existing_delivery:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order already assigned"
            )

        delivery = Delivery(
            order_id=delivery_in.order_id,
            driver_id=delivery_in.driver_id,
            status=DeliveryStatus.ASSIGNED
        )
        self.session.add(delivery)
        await self.session.commit()
        await self.session.refresh(delivery)
        return delivery

    async def get_driver_deliveries(self, driver_id: int) -> List[Delivery]:
        """Get all deliveries assigned to a driver"""
        stmt = select(Delivery).where(Delivery.driver_id == driver_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_status(self, delivery_id: int, update_in: DeliveryUpdate, driver_id: int) -> Delivery:
        """Update delivery status"""
        delivery = await self.session.get(Delivery, delivery_id)
        if not delivery:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Delivery not found"
            )
            
        if delivery.driver_id != driver_id:
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this delivery"
            )

        for field, value in update_in.model_dump(exclude_unset=True).items():
            setattr(delivery, field, value)
            
        # Handle timestamp updates based on status
        if update_in.status == DeliveryStatus.PICKED_UP and not delivery.picked_up_at:
            delivery.picked_up_at = datetime.utcnow()
        elif update_in.status == DeliveryStatus.DELIVERED and not delivery.delivered_at:
            delivery.delivered_at = datetime.utcnow()

        await self.session.commit()
        await self.session.refresh(delivery)
        return delivery
