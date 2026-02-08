"""
Product API endpoints
"""

from typing import Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.exceptions import NotFoundError, ConflictError
from app.services.product import ProductService
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse, 
    ProductListResponse, ProductSearchRequest, ProductBrief
)
from app.api.deps import get_current_active_user, get_current_admin_user, get_current_user_optional, rate_limit_default
from app.models.user import User


router = APIRouter()


@router.get("", response_model=ProductListResponse)
async def list_products(
    _: None = Depends(rate_limit_default),
    query: Optional[str] = Query(None, description="Search query"),
    category_id: Optional[int] = Query(None, description="Filter by category"),
    min_price: Optional[Decimal] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[Decimal] = Query(None, ge=0, description="Maximum price"),
    in_stock_only: bool = Query(False, description="Only show in-stock products"),
    sort_by: str = Query("relevance", description="Sort by: relevance, price_asc, price_desc, rating, newest"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db)
):
    """
    List and search products.
    
    Supports filtering by:
    - Text search (name, description)
    - Category
    - Price range
    - Stock status
    
    Sorting options:
    - relevance: Weighted ranking algorithm
    - price_asc, price_desc: By price
    - rating: By average rating
    - newest: By creation date
    """
    product_service = ProductService(db)
    
    search_params = ProductSearchRequest(
        query=query,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        in_stock_only=in_stock_only,
        sort_by=sort_by,
        page=page,
        per_page=per_page
    )
    
    products, total = await product_service.search(search_params)
    
    # Convert to brief format for list
    product_briefs = []
    for p in products:
        product_briefs.append(ProductBrief(
            id=p.id,
            name=p.name,
            slug=p.slug,
            price=p.price,
            effective_price=p.effective_price,
            image_url=p.image_url,
            average_rating=p.average_rating,
            review_count=len(p.reviews) if p.reviews else 0,
            is_in_stock=p.inventory.available > 0 if p.inventory else False
        ))
    
    pages = (total + per_page - 1) // per_page if per_page > 0 else 0
    
    return ProductListResponse(
        products=product_briefs,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages
    )


@router.get("/featured", response_model=list[ProductBrief])
async def get_featured_products(
    _: None = Depends(rate_limit_default),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """
    Get featured products.
    """
    product_service = ProductService(db)
    products = await product_service.get_featured(limit)
    
    return [
        ProductBrief(
            id=p.id,
            name=p.name,
            slug=p.slug,
            price=p.price,
            effective_price=p.effective_price,
            image_url=p.image_url,
            average_rating=p.average_rating,
            review_count=len(p.reviews) if p.reviews else 0,
            is_in_stock=p.inventory.available > 0 if p.inventory else False
        )
        for p in products
    ]


@router.get("/ranked", response_model=list[ProductBrief])
async def get_ranked_products(
    _: None = Depends(rate_limit_default),
    limit: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get products ranked by weighted algorithm.
    
    Score = 0.5 * popularity + 0.3 * rating + 0.2 * recency
    """
    product_service = ProductService(db)
    products = await product_service.get_ranked_products(limit, category_id)
    
    return [
        ProductBrief(
            id=p.id,
            name=p.name,
            slug=p.slug,
            price=p.price,
            effective_price=p.effective_price,
            image_url=p.image_url,
            average_rating=p.average_rating,
            review_count=len(p.reviews) if p.reviews else 0,
            is_in_stock=p.inventory.available > 0 if p.inventory else False
        )
        for p in products
    ]


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    _: None = Depends(rate_limit_default),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get product details by ID.
    
    Increments view count.
    """
    product_service = ProductService(db)
    
    try:
        product = await product_service.get_by_id(product_id)
        
        # Check if active or if user is admin
        from app.models.user import UserRole
        if not product.is_active:
             is_admin = current_user and current_user.role == UserRole.ADMIN
             if not is_admin:
                  raise NotFoundError("Product", product_id)
        
        # Increment view count (async, don't wait)
        await product_service.increment_view_count(product_id)
        
        # Build response with all details
        return ProductResponse(
            id=product.id,
            name=product.name,
            description=product.description,
            slug=product.slug,
            price=product.price,
            discount_percent=product.discount_percent,
            effective_price=product.effective_price,
            image_url=product.image_url,
            is_active=product.is_active,
            is_featured=product.is_featured,
            view_count=product.view_count,
            purchase_count=product.purchase_count,
            average_rating=product.average_rating,
            review_count=len(product.reviews) if product.reviews else 0,
            stock_available=product.inventory.available if product.inventory else 0,
            is_in_stock=product.inventory.available > 0 if product.inventory else False,
            categories=[
                {"id": c.id, "name": c.name, "slug": c.slug}
                for c in product.categories
            ],
            created_at=product.created_at,
            updated_at=product.updated_at
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Create a new product (admin only).
    """
    product_service = ProductService(db)
    
    try:
        product = await product_service.create(data)
        
        return ProductResponse(
            id=product.id,
            name=product.name,
            description=product.description,
            slug=product.slug,
            price=product.price,
            discount_percent=product.discount_percent,
            effective_price=product.effective_price,
            image_url=product.image_url,
            is_active=product.is_active,
            is_featured=product.is_featured,
            view_count=product.view_count,
            purchase_count=product.purchase_count,
            average_rating=0.0,
            review_count=0,
            stock_available=data.initial_stock,
            is_in_stock=data.initial_stock > 0,
            categories=[],
            created_at=product.created_at,
            updated_at=product.updated_at
        )
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Update a product (admin only).
    """
    product_service = ProductService(db)
    
    try:
        product = await product_service.update(product_id, data)
        
        return ProductResponse(
            id=product.id,
            name=product.name,
            description=product.description,
            slug=product.slug,
            price=product.price,
            discount_percent=product.discount_percent,
            effective_price=product.effective_price,
            image_url=product.image_url,
            is_active=product.is_active,
            is_featured=product.is_featured,
            view_count=product.view_count,
            purchase_count=product.purchase_count,
            average_rating=product.average_rating,
            review_count=len(product.reviews) if product.reviews else 0,
            stock_available=product.inventory.available if product.inventory else 0,
            is_in_stock=product.inventory.available > 0 if product.inventory else False,
            categories=[
                {"id": c.id, "name": c.name, "slug": c.slug}
                for c in product.categories
            ],
            created_at=product.created_at,
            updated_at=product.updated_at
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Delete a product (admin only).
    
    This performs a soft delete by setting is_active=False.
    """
    product_service = ProductService(db)
    
    try:
        await product_service.delete(product_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
