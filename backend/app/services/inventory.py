"""
Inventory Service
Handles stock management with concurrency control
Implements both PostgreSQL FOR UPDATE and Redis distributed locking
"""

from typing import List, Optional, Tuple

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    NotFoundError, 
    InsufficientStockError,
    LockAcquisitionError
)
from app.core.cache import cache
from app.models.inventory import Inventory
from app.models.product import Product
from app.schemas.inventory import (
    InventoryCreate, InventoryUpdate,
    InventoryReserveRequest, InventoryReleaseRequest
)


class InventoryService:
    """
    Inventory management service with dual locking strategy:
    1. PostgreSQL SELECT FOR UPDATE (primary)
    2. Redis SETNX distributed lock (fallback/additional protection)
    """
    
    # Lock timeout in seconds
    LOCK_TIMEOUT = 10
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_product_id(self, product_id: int) -> Inventory:
        """Get inventory for a product"""
        result = await self.db.execute(
            select(Inventory)
            .where(Inventory.product_id == product_id)
        )
        inventory = result.scalar_one_or_none()
        
        if not inventory:
            raise NotFoundError("Inventory", product_id)
        
        return inventory
    
    async def get_by_id(self, inventory_id: int) -> Inventory:
        """Get inventory by ID"""
        result = await self.db.execute(
            select(Inventory).where(Inventory.id == inventory_id)
        )
        inventory = result.scalar_one_or_none()
        
        if not inventory:
            raise NotFoundError("Inventory", inventory_id)
        
        return inventory
    
    async def reserve(
        self,
        product_id: int,
        quantity: int,
        use_redis_lock: bool = True
    ) -> Tuple[bool, int]:
        """
        Reserve inventory for an order.
        
        Uses pessimistic locking (SELECT FOR UPDATE) to prevent overselling.
        Optionally uses Redis distributed lock for additional protection.
        
        Args:
            product_id: Product ID
            quantity: Quantity to reserve
            use_redis_lock: Whether to also use Redis distributed lock
            
        Returns:
            Tuple of (success, available_after)
            
        Raises:
            InsufficientStockError: If not enough stock available
            LockAcquisitionError: If unable to acquire lock
        """
        lock_key = f"inventory:{product_id}"
        
        # Acquire Redis lock if enabled
        if use_redis_lock:
            acquired = await cache.acquire_lock(lock_key, self.LOCK_TIMEOUT)
            if not acquired:
                raise LockAcquisitionError(f"inventory for product {product_id}")
        
        try:
            # Use SELECT FOR UPDATE for row-level locking
            result = await self.db.execute(
                select(Inventory)
                .where(Inventory.product_id == product_id)
                .with_for_update()  # Pessimistic lock
            )
            inventory = result.scalar_one_or_none()
            
            if not inventory:
                raise NotFoundError("Inventory", product_id)
            
            # Check availability
            if inventory.available < quantity:
                raise InsufficientStockError(
                    product_id=product_id,
                    requested=quantity,
                    available=inventory.available
                )
            
            # Reserve the stock
            inventory.reserved += quantity
            inventory.version += 1  # Optimistic lock version
            
            await self.db.commit()
            await self.db.refresh(inventory)
            
            return True, inventory.available
            
        finally:
            # Always release Redis lock
            if use_redis_lock:
                await cache.release_lock(lock_key)
    
    async def reserve_with_optimistic_lock(
        self,
        product_id: int,
        quantity: int,
        expected_version: int
    ) -> Tuple[bool, int]:
        """
        Reserve inventory using optimistic locking.
        
        Alternative to pessimistic locking - uses version column to detect
        concurrent modifications.
        
        Args:
            product_id: Product ID
            quantity: Quantity to reserve
            expected_version: Expected version number
            
        Returns:
            Tuple of (success, new_version)
        """
        inventory = await self.get_by_product_id(product_id)
        
        # Check version matches
        if inventory.version != expected_version:
            # Concurrent modification detected - retry required
            return False, inventory.version
        
        # Check availability
        if inventory.available < quantity:
            raise InsufficientStockError(
                product_id=product_id,
                requested=quantity,
                available=inventory.available
            )
        
        # Use conditional update with version check
        result = await self.db.execute(
            update(Inventory)
            .where(
                Inventory.product_id == product_id,
                Inventory.version == expected_version
            )
            .values(
                reserved=Inventory.reserved + quantity,
                version=Inventory.version + 1
            )
            .returning(Inventory.version)
        )
        
        new_version = result.scalar_one_or_none()
        
        if new_version is None:
            # Update failed - version mismatch
            return False, inventory.version
        
        await self.db.commit()
        return True, new_version
    
    async def release(
        self,
        product_id: int,
        quantity: int
    ) -> int:
        """
        Release reserved inventory (e.g., order cancelled).
        
        Args:
            product_id: Product ID
            quantity: Quantity to release
            
        Returns:
            Available quantity after release
        """
        result = await self.db.execute(
            select(Inventory)
            .where(Inventory.product_id == product_id)
            .with_for_update()
        )
        inventory = result.scalar_one_or_none()
        
        if not inventory:
            raise NotFoundError("Inventory", product_id)
        
        inventory.release(quantity)
        await self.db.commit()
        await self.db.refresh(inventory)
        
        return inventory.available
    
    async def confirm(
        self,
        product_id: int,
        quantity: int
    ) -> int:
        """
        Confirm reservation and deduct from stock (order completed).
        
        Args:
            product_id: Product ID
            quantity: Quantity to confirm
            
        Returns:
            Available quantity after confirmation
        """
        result = await self.db.execute(
            select(Inventory)
            .where(Inventory.product_id == product_id)
            .with_for_update()
        )
        inventory = result.scalar_one_or_none()
        
        if not inventory:
            raise NotFoundError("Inventory", product_id)
        
        inventory.confirm(quantity)
        await self.db.commit()
        await self.db.refresh(inventory)
        
        return inventory.available
    
    async def restock(
        self,
        product_id: int,
        quantity: int
    ) -> Inventory:
        """
        Add stock to inventory.
        
        Args:
            product_id: Product ID
            quantity: Quantity to add
            
        Returns:
            Updated inventory
        """
        result = await self.db.execute(
            select(Inventory)
            .where(Inventory.product_id == product_id)
            .with_for_update()
        )
        inventory = result.scalar_one_or_none()
        
        if not inventory:
            raise NotFoundError("Inventory", product_id)
        
        inventory.restock(quantity)
        await self.db.commit()
        await self.db.refresh(inventory)
        
        return inventory
    
    async def get_low_stock(self, limit: int = 50) -> List[Inventory]:
        """Get products with low stock"""
        result = await self.db.execute(
            select(Inventory)
            .where(
                (Inventory.quantity - Inventory.reserved) <= Inventory.low_stock_threshold
            )
            .order_by((Inventory.quantity - Inventory.reserved).asc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_out_of_stock(self) -> List[Inventory]:
        """Get products that are out of stock"""
        result = await self.db.execute(
            select(Inventory)
            .where((Inventory.quantity - Inventory.reserved) <= 0)
        )
        return list(result.scalars().all())
    
    async def bulk_reserve(
        self,
        items: List[InventoryReserveRequest]
    ) -> Tuple[List[int], List[int]]:
        """
        Reserve multiple products atomically with FIFO allocation.
        
        Uses consistent ordering to prevent deadlocks.
        
        Args:
            items: List of reserve requests
            
        Returns:
            Tuple of (successful_product_ids, failed_product_ids)
        """
        # Sort by product_id to ensure consistent lock ordering (prevent deadlocks)
        sorted_items = sorted(items, key=lambda x: x.product_id)
        
        successful = []
        failed = []
        
        try:
            for item in sorted_items:
                try:
                    await self.reserve(
                        product_id=item.product_id,
                        quantity=item.quantity,
                        use_redis_lock=True
                    )
                    successful.append(item.product_id)
                except (InsufficientStockError, LockAcquisitionError):
                    failed.append(item.product_id)
                    # Rollback all successful reservations
                    for success_id in successful:
                        orig_item = next(i for i in items if i.product_id == success_id)
                        await self.release(success_id, orig_item.quantity)
                    successful = []
                    break
            
            if successful:
                await self.db.commit()
            
        except Exception as e:
            # Rollback on any error
            await self.db.rollback()
            raise
        
        return successful, failed
    
    async def create(self, data: InventoryCreate) -> Inventory:
        """Create inventory record for a product"""
        # Check if inventory already exists
        existing = await self.db.execute(
            select(Inventory).where(Inventory.product_id == data.product_id)
        )
        if existing.scalar_one_or_none():
            raise Exception(f"Inventory already exists for product {data.product_id}")
        
        inventory = Inventory(
            product_id=data.product_id,
            quantity=data.quantity,
            low_stock_threshold=data.low_stock_threshold,
            warehouse_id=data.warehouse_id
        )
        
        self.db.add(inventory)
        await self.db.commit()
        await self.db.refresh(inventory)
        
        return inventory
    
    async def update(self, product_id: int, data: InventoryUpdate) -> Inventory:
        """Update inventory settings"""
        inventory = await self.get_by_product_id(product_id)
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(inventory, field, value)
        
        await self.db.commit()
        await self.db.refresh(inventory)
        
        return inventory
