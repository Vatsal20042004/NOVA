"""
API v1 Router
Aggregates all API endpoints
"""

from fastapi import APIRouter

from app.api.v1 import auth, users, products, categories, orders, payments, recommendations, admin, deliveries, newsletter

api_router = APIRouter()

# Include all routers with their prefixes
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(products.router, prefix="/products", tags=["Products"])
api_router.include_router(categories.router, prefix="/categories", tags=["Categories"])
api_router.include_router(orders.router, prefix="/orders", tags=["Orders"])
api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
api_router.include_router(deliveries.router, prefix="/deliveries", tags=["Deliveries"])
api_router.include_router(newsletter.router, prefix="/newsletter", tags=["Newsletter"])
