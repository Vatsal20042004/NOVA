"""
Recommendation API endpoints
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.recommendation import RecommendationService
from app.schemas.product import ProductBrief
from app.api.deps import get_current_active_user, get_current_user_optional, rate_limit_default
from app.models.user import User


router = APIRouter()


@router.get("/user/{user_id}", response_model=list[ProductBrief])
async def get_user_recommendations(
    user_id: int,
    _: None = Depends(rate_limit_default),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get personalized product recommendations for a user.
    
    Uses co-occurrence algorithm: "Users who bought A also bought B"
    """
    # Users can only get their own recommendations (or admin)
    from app.models.user import UserRole
    if user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot view another user's recommendations"
        )
    
    recommendation_service = RecommendationService(db)
    products = await recommendation_service.get_recommendations(user_id, limit)
    
    return [
        ProductBrief(
            id=p.id,
            name=p.name,
            slug=p.slug,
            price=p.price,
            effective_price=p.effective_price,
            image_url=p.image_url,
            average_rating=p.average_rating,
            review_count=len(p.reviews) if hasattr(p, 'reviews') and p.reviews else 0,
            is_in_stock=True
        )
        for p in products
    ]


@router.get("/me", response_model=list[ProductBrief])
async def get_my_recommendations(
    _: None = Depends(rate_limit_default),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get personalized recommendations for the current user.
    """
    recommendation_service = RecommendationService(db)
    products = await recommendation_service.get_recommendations(current_user.id, limit)
    
    return [
        ProductBrief(
            id=p.id,
            name=p.name,
            slug=p.slug,
            price=p.price,
            effective_price=p.effective_price,
            image_url=p.image_url,
            average_rating=p.average_rating,
            review_count=len(p.reviews) if hasattr(p, 'reviews') and p.reviews else 0,
            is_in_stock=True
        )
        for p in products
    ]


@router.get("/product/{product_id}/similar", response_model=list[ProductBrief])
async def get_similar_products(
    product_id: int,
    _: None = Depends(rate_limit_default),
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db)
):
    """
    Get products similar to a given product.
    
    Based on co-occurrence in orders.
    """
    recommendation_service = RecommendationService(db)
    products = await recommendation_service.get_similar_products(product_id, limit)
    
    return [
        ProductBrief(
            id=p.id,
            name=p.name,
            slug=p.slug,
            price=p.price,
            effective_price=p.effective_price,
            image_url=p.image_url,
            average_rating=p.average_rating,
            review_count=len(p.reviews) if hasattr(p, 'reviews') and p.reviews else 0,
            is_in_stock=True
        )
        for p in products
    ]


@router.get("/product/{product_id}/also-bought", response_model=list[ProductBrief])
async def get_frequently_bought_together(
    product_id: int,
    _: None = Depends(rate_limit_default),
    limit: int = Query(3, ge=1, le=10),
    db: AsyncSession = Depends(get_db)
):
    """
    Get products frequently bought together with a product.
    
    "Customers also bought" feature.
    """
    recommendation_service = RecommendationService(db)
    products = await recommendation_service.get_frequently_bought_together(product_id, limit)
    
    return [
        ProductBrief(
            id=p.id,
            name=p.name,
            slug=p.slug,
            price=p.price,
            effective_price=p.effective_price,
            image_url=p.image_url,
            average_rating=p.average_rating,
            review_count=len(p.reviews) if hasattr(p, 'reviews') and p.reviews else 0,
            is_in_stock=True
        )
        for p in products
    ]
