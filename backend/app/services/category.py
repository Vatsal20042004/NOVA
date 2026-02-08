"""
Category Service
Handles product category management
"""

import re
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ConflictError
from app.models.product import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService:
    """Service for category operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, category_id: int) -> Category:
        """Get category by ID with children loaded"""
        result = await self.db.execute(
            select(Category)
            .options(selectinload(Category.children))
            .where(Category.id == category_id)
        )
        category = result.scalar_one_or_none()
        
        if not category:
            raise NotFoundError("Category", category_id)
        
        return category
    
    async def get_by_slug(self, slug: str) -> Optional[Category]:
        """Get category by slug"""
        result = await self.db.execute(
            select(Category).where(Category.slug == slug)
        )
        return result.scalar_one_or_none()
    
    async def list_all(self, parent_id: Optional[int] = None) -> List[Category]:
        """
        List categories, optionally filtered by parent.
        
        If parent_id is None, returns root categories (no parent).
        """
        query = select(Category).options(selectinload(Category.children))
        
        if parent_id is None:
            query = query.where(Category.parent_id.is_(None))
        else:
            query = query.where(Category.parent_id == parent_id)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_tree(self) -> List[Category]:
        """Get full category tree (all root categories with nested children)"""
        return await self.list_all(parent_id=None)
    
    async def create(self, data: CategoryCreate) -> Category:
        """
        Create a new category.
        
        Args:
            data: Category data
            
        Returns:
            Created category
        """
        # Generate slug if not provided
        slug = data.slug or self._generate_slug(data.name)
        
        # Check for duplicate slug
        existing = await self.get_by_slug(slug)
        if existing:
            raise ConflictError(f"Category with slug '{slug}' already exists")
        
        # Verify parent exists if specified
        if data.parent_id:
            await self.get_by_id(data.parent_id)
        
        category = Category(
            name=data.name,
            description=data.description,
            slug=slug,
            image_url=data.image_url,
            parent_id=data.parent_id
        )
        
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        
        return category
    
    async def update(self, category_id: int, data: CategoryUpdate) -> Category:
        """Update a category"""
        category = await self.get_by_id(category_id)
        
        update_data = data.model_dump(exclude_unset=True)
        
        # Handle slug update
        if "slug" in update_data and update_data["slug"]:
            existing = await self.get_by_slug(update_data["slug"])
            if existing and existing.id != category_id:
                raise ConflictError(f"Category with slug '{update_data['slug']}' already exists")
        
        # Verify parent exists if being updated
        if "parent_id" in update_data and update_data["parent_id"]:
            if update_data["parent_id"] == category_id:
                raise ConflictError("Category cannot be its own parent")
            await self.get_by_id(update_data["parent_id"])
        
        for field, value in update_data.items():
            setattr(category, field, value)
        
        await self.db.commit()
        await self.db.refresh(category)
        
        return category
    
    async def delete(self, category_id: int) -> bool:
        """
        Delete a category.
        
        Note: Products in this category will no longer have this category association.
        Child categories will have their parent_id set to NULL.
        """
        category = await self.get_by_id(category_id)
        
        # Update children to have no parent
        for child in category.children:
            child.parent_id = None
        
        await self.db.delete(category)
        await self.db.commit()
        
        return True
    
    async def get_product_count(self, category_id: int) -> int:
        """Get count of products in a category"""
        from app.models.product import ProductCategory
        
        result = await self.db.execute(
            select(func.count(ProductCategory.product_id))
            .where(ProductCategory.category_id == category_id)
        )
        return result.scalar() or 0
    
    def _generate_slug(self, name: str) -> str:
        """Generate URL-friendly slug from name"""
        slug = name.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        slug = slug.strip('-')
        return slug
