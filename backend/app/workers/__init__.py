# Workers module - Background task processing
from app.workers.celery_app import celery_app
from app.workers.tasks import (
    send_order_confirmation_email,
    process_payment_retry,
    update_recommendation_matrix,
    send_low_stock_alert
)

__all__ = [
    "celery_app",
    "send_order_confirmation_email",
    "process_payment_retry",
    "update_recommendation_matrix",
    "send_low_stock_alert",
]
