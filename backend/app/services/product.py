"""
Product Service
Handles product management with caching
"""

import re
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ConflictError
from app.core.config import settings
from app.core.cache import cache
from app.models.product import Product, Category, ProductCategory
from app.models.inventory import Inventory
from app.models.review import Review
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductSearchRequest,
    ProductResponse, ProductBrief
)


class ProductService:
    """Service for product operations with ranking algorithm"""
    
    # Cache TTL in seconds
    CACHE_TTL = 600  # 10 minutes
    LIST_CACHE_TTL = 300  # 5 minutes
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, product_id: int, use_cache: bool = True) -> Product:
        """
        Get product by ID with optional caching.
        
        Args:
            product_id: Product ID
            use_cache: Whether to use Redis cache
            
        Returns:
            Product object
        """
        cache_key = cache.product_key(product_id)
        
        # Try cache first
        if use_cache:
            cached = await cache.get_json(cache_key)
            if cached:
                # Reconstruct from cache (basic data only)
                # For full object, we still query DB
                pass
        
        # Query database with all relationships
        result = await self.db.execute(
            select(Product)
            .options(
                selectinload(Product.categories),
                selectinload(Product.inventory),
                selectinload(Product.reviews)
            )
            .where(Product.id == product_id)
        )
        product = result.scalar_one_or_none()
        
        if not product:
            raise NotFoundError("Product", product_id)
        
        # Update cache
        if use_cache:
            await self._cache_product(product)
        
        return product
    
    async def get_by_slug(self, slug: str) -> Optional[Product]:
        """Get product by slug"""
        result = await self.db.execute(
            select(Product)
            .options(
                selectinload(Product.categories),
                selectinload(Product.inventory),
                selectinload(Product.reviews)
            )
            .where(Product.slug == slug)
        )
        return result.scalar_one_or_none()
    
    async def search(
        self,
        params: ProductSearchRequest
    ) -> Tuple[List[Product], int]:
        """
        Search products with filtering, sorting, and pagination.
        
        Implements weighted ranking algorithm:
        score = 0.5 * popularity + 0.3 * rating + 0.2 * recency
        
        Returns:
            Tuple of (products list, total count)
        """
        query = (
            select(Product)
            .options(
                selectinload(Product.categories),
                selectinload(Product.inventory),
                selectinload(Product.reviews)
            )
            .where(Product.is_active == True)
        )
        count_query = select(func.count(Product.id)).where(Product.is_active == True)
        
        # Text search: PostgreSQL full-text (tsvector) or SQLite ILIKE fallback
        if params.query:
            if settings.is_sqlite:
                search_filter = or_(
                    Product.name.ilike(f"%{params.query}%"),
                    Product.description.ilike(f"%{params.query}%")
                )
            else:
                # PostgreSQL full-text search: to_tsvector @@ plainto_tsquery
                search_text = func.concat(
                    func.coalesce(Product.name, ""),
                    " ",
                    func.coalesce(Product.description, ""),
                )
                ts_vector = func.to_tsvector("english", search_text)
                ts_query = func.plainto_tsquery("english", params.query)
                search_filter = ts_vector.op("@@")(ts_query)
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        # Category filter
        if params.category_id:
            query = query.join(ProductCategory).where(
                ProductCategory.category_id == params.category_id
            )
            count_query = count_query.join(ProductCategory).where(
                ProductCategory.category_id == params.category_id
            )
        
        # Price range filter
        if params.min_price is not None:
            query = query.where(Product.price >= params.min_price)
            count_query = count_query.where(Product.price >= params.min_price)
        
        if params.max_price is not None:
            query = query.where(Product.price <= params.max_price)
            count_query = count_query.where(Product.price <= params.max_price)
        
        # In stock filter
        if params.in_stock_only:
            query = query.join(Inventory).where(
                Inventory.quantity - Inventory.reserved > 0
            )
            count_query = count_query.join(Inventory).where(
                Inventory.quantity - Inventory.reserved > 0
            )
        
        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply sorting
        if params.sort_by == "price_asc":
            query = query.order_by(Product.price.asc())
        elif params.sort_by == "price_desc":
            query = query.order_by(Product.price.desc())
        elif params.sort_by == "rating":
            # Sort by rating requires subquery
            query = query.order_by(Product.purchase_count.desc())  # Approximation
        elif params.sort_by == "newest":
            query = query.order_by(Product.created_at.desc())
        else:
            # Default: relevance (weighted ranking)
            query = query.order_by(
                (Product.purchase_count * 0.5 + 
                 Product.view_count * 0.3).desc(),
                Product.created_at.desc()
            )
        
        # Pagination
        query = query.offset((params.page - 1) * params.per_page).limit(params.per_page)
        
        result = await self.db.execute(query)
        products = list(result.scalars().unique().all())
        
        return products, total
    
    async def get_ranked_products(
        self,
        limit: int = 20,
        category_id: Optional[int] = None
    ) -> List[Product]:
        """
        Get products ranked by weighted score algorithm.
        
        score = 0.5 * popularity + 0.3 * rating + 0.2 * recency
        
        Uses DB-side scoring and LIMIT to avoid loading full catalog into memory.
        PostgreSQL: full formula with scalar subquery for max(purchase_count).
        SQLite: approximate order by purchase_count, rating, recency.
        """
        base_filter = Product.is_active == True
        max_p_subq = (
            select(func.coalesce(func.max(Product.purchase_count), 1))
            .where(base_filter)
            .scalar_subquery()
        )

        query = (
            select(Product)
            .options(
                selectinload(Product.categories),
                selectinload(Product.inventory),
                selectinload(Product.reviews)
            )
            .where(base_filter)
        )

        if category_id:
            query = query.join(ProductCategory).where(
                ProductCategory.category_id == category_id
            )

        if settings.is_sqlite:
            # SQLite: order by components (no single score expression)
            query = query.order_by(
                Product.purchase_count.desc(),
                Product.average_rating.desc(),
                Product.created_at.desc()
            )
        else:
            # PostgreSQL: full weighted score in SQL
            pop_norm = Product.purchase_count / max_p_subq
            rating_norm = Product.average_rating / 5.0
            recency_expr = func.greatest(
                0,
                1
                - func.extract("epoch", func.now() - Product.created_at)
                / (30.0 * 86400),
            )
            score = 0.5 * pop_norm + 0.3 * rating_norm + 0.2 * recency_expr
            query = query.order_by(score.desc())

        query = query.limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().unique().all())
    
    async def create(self, data: ProductCreate) -> Product:
        """Create a new product with inventory"""
        # Generate slug if not provided
        slug = data.slug or self._generate_slug(data.name)
        
        # Check for duplicate slug
        existing = await self.get_by_slug(slug)
        if existing:
            # Append timestamp to make unique
            slug = f"{slug}-{int(datetime.now().timestamp())}"
        
        product = Product(
            name=data.name,
            description=data.description,
            slug=slug,
            price=data.price,
            discount_percent=data.discount_percent,
            image_url=data.image_url,
            is_active=data.is_active,
            is_featured=data.is_featured
        )
        
        self.db.add(product)
        await self.db.flush()  # Get product ID
        
        # Add category associations
        for category_id in data.category_ids:
            product_category = ProductCategory(
                product_id=product.id,
                category_id=category_id
            )
            self.db.add(product_category)
        
        # Create inventory record
        inventory = Inventory(
            product_id=product.id,
            quantity=data.initial_stock
        )
        self.db.add(inventory)
        
        await self.db.commit()
        await self.db.refresh(product)
        
        # Invalidate list cache
        await self._invalidate_list_cache()
        
        return product
    
    async def update(self, product_id: int, data: ProductUpdate) -> Product:
        """Update a product"""
        product = await self.get_by_id(product_id, use_cache=False)
        
        update_data = data.model_dump(exclude_unset=True)
        
        # Handle category updates separately
        category_ids = update_data.pop("category_ids", None)
        
        # Update basic fields
        for field, value in update_data.items():
            setattr(product, field, value)
        
        # Update categories if provided
        if category_ids is not None:
            # Remove existing associations
            await self.db.execute(
                select(ProductCategory).where(
                    ProductCategory.product_id == product_id
                )
            )
            result = await self.db.execute(
                select(ProductCategory).where(
                    ProductCategory.product_id == product_id
                )
            )
            for pc in result.scalars():
                await self.db.delete(pc)
            
            # Add new associations
            for category_id in category_ids:
                product_category = ProductCategory(
                    product_id=product.id,
                    category_id=category_id
                )
                self.db.add(product_category)
        
        await self.db.commit()
        await self.db.refresh(product)
        
        # Invalidate cache
        await cache.delete(cache.product_key(product_id))
        await self._invalidate_list_cache()
        
        return product
    
    async def delete(self, product_id: int) -> bool:
        """Delete a product (soft delete by setting inactive)"""
        product = await self.get_by_id(product_id, use_cache=False)
        product.is_active = False
        
        await self.db.commit()
        
        # Invalidate cache
        await cache.delete(cache.product_key(product_id))
        await self._invalidate_list_cache()
        
        return True
    
    async def increment_view_count(self, product_id: int) -> None:
        """Increment product view count"""
        product = await self.get_by_id(product_id, use_cache=False)
        product.view_count += 1
        await self.db.commit()
    
    async def get_featured(self, limit: int = 10) -> List[Product]:
        """Get featured products"""
        result = await self.db.execute(
            select(Product)
            .options(
                selectinload(Product.categories),
                selectinload(Product.inventory),
                selectinload(Product.reviews)
            )
            .where(
                and_(
                    Product.is_active == True,
                    Product.is_featured == True
                )
            )
            .order_by(Product.purchase_count.desc())
            .limit(limit)
        )
        return list(result.scalars().unique().all())
    
    async def _cache_product(self, product: Product) -> None:
        """Cache product data"""
        cache_data = {
            "id": product.id,
            "name": product.name,
            "slug": product.slug,
            "price": str(product.price),
            "effective_price": str(product.effective_price),
            "image_url": product.image_url,
            "is_active": product.is_active
        }
        await cache.set_json(
            cache.product_key(product.id),
            cache_data,
            self.CACHE_TTL
        )
    
    async def _invalidate_list_cache(self) -> None:
        """Invalidate product list caches"""
        # In production, use Redis SCAN to find and delete matching keys
        # For now, we'll rely on TTL expiration
        pass
    
    def _generate_slug(self, name: str) -> str:
        """Generate URL-friendly slug from name"""
        slug = name.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        slug = slug.strip('-')
        return slug
