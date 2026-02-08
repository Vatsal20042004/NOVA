"""
Celery Tasks
Background workers for async processing
"""

import logging
from typing import Optional

from celery import shared_task

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=3
)
def send_order_confirmation_email(
    self,
    order_id: int,
    user_email: str,
    order_number: str
) -> dict:
    """
    Send order confirmation email.
    
    Uses exponential backoff for retries.
    Idempotent - can be safely retried.
    """
    try:
        logger.info(f"Sending confirmation email for order {order_number} to {user_email}")
        
        # In production, integrate with email service (SendGrid, SES, etc.)
        # For now, just log
        
        # Simulate email sending
        email_content = f"""
        Thank you for your order!
        
        Order Number: {order_number}
        
        We'll notify you when your order ships.
        """
        
        logger.info(f"Email sent successfully for order {order_number}")
        
        return {
            "success": True,
            "order_id": order_id,
            "email": user_email
        }
        
    except Exception as e:
        logger.error(f"Failed to send email for order {order_number}: {e}")
        raise self.retry(exc=e)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=1800,  # Max 30 minutes between retries
    retry_jitter=True,
    max_retries=5
)
def process_payment_retry(
    self,
    payment_id: int,
    order_id: int
) -> dict:
    """
    Retry a failed payment.
    
    Uses exponential backoff: 1min, 2min, 4min, 8min, 16min
    """
    try:
        logger.info(f"Processing payment retry for payment {payment_id}")
        
        # Import here to avoid circular imports
        import asyncio
        from app.db.session import async_session_maker
        from app.services.payment import PaymentService
        
        async def retry_payment():
            async with async_session_maker() as session:
                payment_service = PaymentService(session)
                return await payment_service.retry(payment_id)
        
        # Run async function
        payment = asyncio.get_event_loop().run_until_complete(retry_payment())
        
        return {
            "success": payment.is_successful,
            "payment_id": payment_id,
            "status": payment.status.value
        }
        
    except Exception as e:
        logger.error(f"Payment retry failed for payment {payment_id}: {e}")
        raise self.retry(exc=e)


@celery_app.task(bind=True)
def update_recommendation_matrix(self) -> dict:
    """
    Rebuild the recommendation co-occurrence matrix.
    
    Scheduled to run hourly via Celery Beat.
    """
    try:
        logger.info("Starting recommendation matrix update")
        
        import asyncio
        from app.db.session import async_session_maker
        from app.services.recommendation import RecommendationService
        
        async def rebuild_matrix():
            async with async_session_maker() as session:
                recommendation_service = RecommendationService(session)
                return await recommendation_service.rebuild_recommendations_matrix()
        
        matrix = asyncio.get_event_loop().run_until_complete(rebuild_matrix())
        
        product_count = len(matrix)
        logger.info(f"Recommendation matrix updated for {product_count} products")
        
        return {
            "success": True,
            "products_processed": product_count
        }
        
    except Exception as e:
        logger.error(f"Recommendation matrix update failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@celery_app.task(bind=True)
def send_low_stock_alert(
    self,
    product_id: int,
    product_name: str,
    available_quantity: int
) -> dict:
    """
    Send alert for low stock product.
    """
    try:
        logger.warning(
            f"LOW STOCK ALERT: Product '{product_name}' (ID: {product_id}) "
            f"has only {available_quantity} units available"
        )
        
        # In production, send to Slack, email, PagerDuty, etc.
        
        return {
            "success": True,
            "product_id": product_id,
            "available": available_quantity
        }
        
    except Exception as e:
        logger.error(f"Failed to send low stock alert: {e}")
        return {"success": False, "error": str(e)}


@celery_app.task(bind=True)
def check_low_stock_products(self) -> dict:
    """
    Check all products for low stock and send alerts.
    
    Scheduled to run daily via Celery Beat.
    """
    try:
        logger.info("Checking for low stock products")
        
        import asyncio
        from app.db.session import async_session_maker
        from app.services.inventory import InventoryService
        
        async def get_low_stock():
            async with async_session_maker() as session:
                inventory_service = InventoryService(session)
                return await inventory_service.get_low_stock(100)
        
        low_stock_items = asyncio.get_event_loop().run_until_complete(get_low_stock())
        
        # Queue alerts for each low stock item
        for inventory in low_stock_items:
            send_low_stock_alert.delay(
                product_id=inventory.product_id,
                product_name=f"Product {inventory.product_id}",
                available_quantity=inventory.available
            )
        
        logger.info(f"Found {len(low_stock_items)} low stock products")
        
        return {
            "success": True,
            "low_stock_count": len(low_stock_items)
        }
        
    except Exception as e:
        logger.error(f"Low stock check failed: {e}")
        return {"success": False, "error": str(e)}


@celery_app.task(bind=True)
def sync_inventory_to_cache(self, product_id: int) -> dict:
    """
    Sync inventory data to Redis cache.
    """
    try:
        import asyncio
        from app.db.session import async_session_maker
        from app.services.inventory import InventoryService
        from app.core.cache import cache
        
        async def sync():
            async with async_session_maker() as session:
                inventory_service = InventoryService(session)
                inventory = await inventory_service.get_by_product_id(product_id)
                
                await cache.set_json(
                    f"inventory:{product_id}",
                    {
                        "quantity": inventory.quantity,
                        "reserved": inventory.reserved,
                        "available": inventory.available
                    },
                    ttl=300  # 5 minutes
                )
                
                return inventory.available
        
        available = asyncio.get_event_loop().run_until_complete(sync())
        
        return {
            "success": True,
            "product_id": product_id,
            "available": available
        }
        
    except Exception as e:
        logger.error(f"Inventory cache sync failed for product {product_id}: {e}")
        return {"success": False, "error": str(e)}
