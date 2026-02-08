"""
Category API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.exceptions import NotFoundError, ConflictError
from app.services.category import CategoryService
from app.schemas.category import (
    CategoryCreate, CategoryUpdate, CategoryResponse
)
from app.api.deps import get_current_active_user, get_current_admin_user
from app.models.user import User


router = APIRouter()


@router.get("", response_model=list[CategoryResponse])
async def list_categories(
    db: AsyncSession = Depends(get_db)
):
    """
    Get all root categories with their children.
    """
    category_service = CategoryService(db)
    categories = await category_service.get_tree()
    
    result = []
    for cat in categories:
        product_count = await category_service.get_product_count(cat.id)
        result.append(CategoryResponse(
            id=cat.id,
            name=cat.name,
            description=cat.description,
            slug=cat.slug,
            image_url=cat.image_url,
            parent_id=cat.parent_id,
            product_count=product_count,
            children=[
                CategoryResponse(
                    id=c.id,
                    name=c.name,
                    description=c.description,
                    slug=c.slug,
                    image_url=c.image_url,
                    parent_id=c.parent_id,
                    product_count=0,
                    children=[],
                    created_at=c.created_at,
                    updated_at=c.updated_at
                )
                for c in cat.children
            ],
            created_at=cat.created_at,
            updated_at=cat.updated_at
        ))
    
    return result


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get category by ID.
    """
    category_service = CategoryService(db)
    
    try:
        category = await category_service.get_by_id(category_id)
        product_count = await category_service.get_product_count(category_id)
        
        return CategoryResponse(
            id=category.id,
            name=category.name,
            description=category.description,
            slug=category.slug,
            image_url=category.image_url,
            parent_id=category.parent_id,
            product_count=product_count,
            children=[
                CategoryResponse(
                    id=c.id,
                    name=c.name,
                    description=c.description,
                    slug=c.slug,
                    image_url=c.image_url,
                    parent_id=c.parent_id,
                    product_count=0,
                    children=[],
                    created_at=c.created_at,
                    updated_at=c.updated_at
                )
                for c in category.children
            ],
            created_at=category.created_at,
            updated_at=category.updated_at
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Create a new category (admin only).
    """
    category_service = CategoryService(db)
    
    try:
        category = await category_service.create(data)
        
        return CategoryResponse(
            id=category.id,
            name=category.name,
            description=category.description,
            slug=category.slug,
            image_url=category.image_url,
            parent_id=category.parent_id,
            product_count=0,
            children=[],
            created_at=category.created_at,
            updated_at=category.updated_at
        )
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Update a category (admin only).
    """
    category_service = CategoryService(db)
    
    try:
        category = await category_service.update(category_id, data)
        product_count = await category_service.get_product_count(category_id)
        
        return CategoryResponse(
            id=category.id,
            name=category.name,
            description=category.description,
            slug=category.slug,
            image_url=category.image_url,
            parent_id=category.parent_id,
            product_count=product_count,
            children=[],
            created_at=category.created_at,
            updated_at=category.updated_at
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Delete a category (admin only).
    """
    category_service = CategoryService(db)
    
    try:
        await category_service.delete(category_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
