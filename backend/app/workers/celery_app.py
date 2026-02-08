"""
Celery Application Configuration
"""

from celery import Celery

from app.core.config import settings


# Create Celery app
celery_app = Celery(
    "ecommerce_workers",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Result expiry
    result_expires=3600,  # 1 hour
    
    # Task execution settings
    task_acks_late=True,  # For at-least-once delivery
    task_reject_on_worker_lost=True,
    
    # Retry settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    
    # Worker settings
    worker_prefetch_multiplier=1,  # Disable prefetching for fair distribution
    
    # Rate limiting
    task_annotations={
        "app.workers.tasks.send_order_confirmation_email": {
            "rate_limit": "10/s"
        },
        "app.workers.tasks.process_payment_retry": {
            "rate_limit": "5/s"
        }
    },
    
    # Beat schedule for periodic tasks
    beat_schedule={
        "update-recommendations-hourly": {
            "task": "app.workers.tasks.update_recommendation_matrix",
            "schedule": 3600.0,  # Every hour
        },
        "check-low-stock-daily": {
            "task": "app.workers.tasks.check_low_stock_products",
            "schedule": 86400.0,  # Every day
        },
    }
)


if __name__ == "__main__":
    celery_app.start()
