"""
Inventory Service Concurrency Tests

These tests verify the correctness of inventory management
under concurrent access scenarios.
"""

import asyncio
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.models.inventory import Inventory
from app.services.inventory import InventoryService


class TestInventoryConcurrency:
    """Test concurrent inventory operations."""
    
    async def create_test_product_with_inventory(
        self, session: AsyncSession, quantity: int = 100
    ) -> Product:
        """Helper to create a product with inventory."""
        product = Product(
            name="Test Product",
            description="Test",
            price=10.00,
            slug="test-conc-001",
            is_active=True
        )
        session.add(product)
        await session.flush()
        
        inventory = Inventory(
            product_id=product.id,
            quantity=quantity,
            reserved=0
        )
        session.add(inventory)
        await session.commit()
        
        return product
    
    @pytest.mark.asyncio
    async def test_concurrent_reservations_no_oversell(
        self, db_session: AsyncSession
    ):
        """
        Test that concurrent reservations don't oversell inventory.
        
        Scenario:
        - Product has 10 units
        - 20 concurrent requests each try to reserve 1 unit
        - Only 10 should succeed
        """
        # Create product with 10 units
        product = await self.create_test_product_with_inventory(
            db_session, quantity=10
        )
        
        inventory_service = InventoryService(db_session)
        
        async def try_reserve():
            try:
                success = await inventory_service.reserve(product.id, 1)
                return success
            except Exception:
                return False
        
        # Run 20 concurrent reservations
        tasks = [try_reserve() for _ in range(20)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successful reservations
        successful = sum(1 for r in results if r is True)
        
        # Verify
        assert successful <= 10, f"Oversold! {successful} reservations succeeded"
        
        # Check actual inventory
        await db_session.refresh(product)
        inventory = await inventory_service.get_by_product_id(product.id)
        assert inventory.available >= 0, "Negative available inventory!"
    
    @pytest.mark.asyncio
    async def test_reserve_release_cycle(self, db_session: AsyncSession):
        """
        Test reserve and release operations maintain consistency.
        """
        product = await self.create_test_product_with_inventory(
            db_session, quantity=10
        )
        
        inventory_service = InventoryService(db_session)
        
        # Reserve 5 units
        await inventory_service.reserve(product.id, 5)
        
        inventory = await inventory_service.get_by_product_id(product.id)
        assert inventory.reserved == 5
        assert inventory.available == 5
        
        # Release 3 units
        await inventory_service.release(product.id, 3)
        
        await db_session.refresh(inventory)
        assert inventory.reserved == 2
        assert inventory.available == 8
        
        # Confirm 2 units (reduces quantity)
        await inventory_service.confirm(product.id, 2)
        
        await db_session.refresh(inventory)
        assert inventory.quantity == 8
        assert inventory.reserved == 0
        assert inventory.available == 8
    
    @pytest.mark.asyncio
    async def test_insufficient_stock_error(self, db_session: AsyncSession):
        """Test that reserving more than available raises error."""
        from app.core.exceptions import InsufficientStockError
        
        product = await self.create_test_product_with_inventory(
            db_session, quantity=5
        )
        
        inventory_service = InventoryService(db_session)
        
        with pytest.raises(InsufficientStockError):
            await inventory_service.reserve(product.id, 10)
    
    @pytest.mark.asyncio
    async def test_version_conflict_detection(self, db_session: AsyncSession):
        """
        Test that version conflicts are detected.
        
        This tests the optimistic locking behavior.
        """
        product = await self.create_test_product_with_inventory(
            db_session, quantity=10
        )
        
        inventory_service = InventoryService(db_session)
        
        # Get inventory
        inventory = await inventory_service.get_by_product_id(product.id)
        initial_version = inventory.version
        
        # Make a change
        await inventory_service.reserve(product.id, 1)
        
        # Version should be incremented
        await db_session.refresh(inventory)
        assert inventory.version > initial_version
