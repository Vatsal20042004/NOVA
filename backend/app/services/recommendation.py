"""
Recommendation Service
Implements co-occurrence based recommendations
"""

import heapq
from collections import defaultdict
from typing import List, Dict, Tuple

from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product, ProductCategory
from app.models.user import User


class RecommendationService:
    """
    Product recommendation service using co-occurrence algorithm.
    
    Algorithm: "Users who bought A also bought B"
    - Build frequency matrix of product co-purchases
    - Use heap for efficient Top-K selection
    - Cache recommendations for performance
    """
    
    CACHE_TTL = 3600  # 1 hour
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_recommendations(
        self,
        user_id: int,
        limit: int = 10
    ) -> List[Product]:
        """
        Get personalized product recommendations for a user.
        
        Based on:
        1. Products in user's order history
        2. Co-occurrence with other users' purchases
        
        Args:
            user_id: User ID
            limit: Number of recommendations to return
            
        Returns:
            List of recommended products
        """
        cache_key = cache.recommendations_key(user_id)
        
        # Check cache
        cached = await cache.get_json(cache_key)
        if cached:
            product_ids = cached.get("product_ids", [])[:limit]
            return await self._get_products_by_ids(product_ids)
        
        # Get user's purchased products
        user_products = await self._get_user_purchased_products(user_id)
        
        if not user_products:
            # No purchase history - return popular products
            return await self._get_popular_products(limit)
        
        # Build co-occurrence recommendations
        recommendations = await self._get_co_occurrence_recommendations(
            user_products,
            limit
        )
        
        # Cache the results
        await cache.set_json(
            cache_key,
            {"product_ids": [p.id for p in recommendations]},
            self.CACHE_TTL
        )
        
        return recommendations
    
    async def get_similar_products(
        self,
        product_id: int,
        limit: int = 5
    ) -> List[Product]:
        """
        Get products similar to a given product.
        
        Uses co-occurrence in orders; falls back to content-based (same category)
        when no co-occurrence data exists.
        """
        co_occurrence = await self._build_product_co_occurrence(product_id)
        
        if co_occurrence:
            top_k = heapq.nlargest(limit, co_occurrence.items(), key=lambda x: x[1])
            product_ids = [pid for pid, _ in top_k]
            return await self._get_products_by_ids(product_ids)
        
        # Content-based fallback: same category, ordered by popularity
        return await self._get_similar_by_category(product_id, limit)
    
    async def get_frequently_bought_together(
        self,
        product_id: int,
        limit: int = 3
    ) -> List[Product]:
        """
        Get products frequently bought together with a product.
        
        "Customers also bought" feature.
        """
        return await self.get_similar_products(product_id, limit)
    
    async def rebuild_recommendations_matrix(self) -> Dict[int, Dict[int, int]]:
        """
        Rebuild the full co-occurrence matrix.
        
        This is an expensive operation - should be run as a background job.
        
        Returns:
            Co-occurrence matrix: {product_id: {related_product_id: count}}
        """
        # Get all completed orders with items
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.status.in_([
                OrderStatus.CONFIRMED,
                OrderStatus.PROCESSING,
                OrderStatus.SHIPPED,
                OrderStatus.DELIVERED
            ]))
        )
        orders = result.scalars().unique().all()
        
        # Build co-occurrence matrix
        matrix: Dict[int, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
        
        for order in orders:
            product_ids = [item.product_id for item in order.items if item.product_id]
            
            # Count co-occurrences (pairs in same order)
            for i, pid1 in enumerate(product_ids):
                for pid2 in product_ids[i + 1:]:
                    matrix[pid1][pid2] += 1
                    matrix[pid2][pid1] += 1
        
        # Cache the matrix (as individual entries for scalability)
        for product_id, related in matrix.items():
            cache_key = f"cooccurrence:{product_id}"
            await cache.set_json(cache_key, dict(related), self.CACHE_TTL * 24)
        
        return dict(matrix)
    
    async def _get_user_purchased_products(
        self,
        user_id: int
    ) -> List[int]:
        """Get list of product IDs the user has purchased"""
        result = await self.db.execute(
            select(OrderItem.product_id)
            .join(Order)
            .where(
                and_(
                    Order.user_id == user_id,
                    Order.status.in_([
                        OrderStatus.CONFIRMED,
                        OrderStatus.PROCESSING,
                        OrderStatus.SHIPPED,
                        OrderStatus.DELIVERED
                    ]),
                    OrderItem.product_id.isnot(None)
                )
            )
            .distinct()
        )
        return list(result.scalars().all())
    
    async def _get_co_occurrence_recommendations(
        self,
        user_products: List[int],
        limit: int
    ) -> List[Product]:
        """
        Get recommendations based on co-occurrence with user's purchases.
        
        Uses heap for efficient Top-K selection.
        """
        # Aggregate co-occurrence scores
        scores: Dict[int, float] = defaultdict(float)
        
        for product_id in user_products:
            co_occurrence = await self._build_product_co_occurrence(product_id)
            for related_id, count in co_occurrence.items():
                if related_id not in user_products:  # Don't recommend already purchased
                    scores[related_id] += count
        
        if not scores:
            return await self._get_popular_products(limit)
        
        # Get top-K using heap
        top_k = heapq.nlargest(limit, scores.items(), key=lambda x: x[1])
        product_ids = [pid for pid, _ in top_k]
        
        return await self._get_products_by_ids(product_ids)
    
    async def _build_product_co_occurrence(
        self,
        product_id: int
    ) -> Dict[int, int]:
        """
        Build co-occurrence counts for a specific product.
        
        Finds all products that appear in the same orders.
        """
        # Try cache first
        cache_key = f"cooccurrence:{product_id}"
        cached = await cache.get_json(cache_key)
        if cached:
            return cached
        
        # Query orders containing this product
        result = await self.db.execute(
            select(Order.id)
            .join(OrderItem)
            .where(
                and_(
                    OrderItem.product_id == product_id,
                    Order.status.in_([
                        OrderStatus.CONFIRMED,
                        OrderStatus.PROCESSING,
                        OrderStatus.SHIPPED,
                        OrderStatus.DELIVERED
                    ])
                )
            )
        )
        order_ids = list(result.scalars().all())
        
        if not order_ids:
            return {}
        
        # Get other products in these orders
        result = await self.db.execute(
            select(OrderItem.product_id)
            .where(
                and_(
                    OrderItem.order_id.in_(order_ids),
                    OrderItem.product_id != product_id,
                    OrderItem.product_id.isnot(None)
                )
            )
        )
        
        # Count occurrences
        co_occurrence: Dict[int, int] = defaultdict(int)
        for related_id in result.scalars():
            co_occurrence[related_id] += 1
        
        # Cache for future use
        await cache.set_json(cache_key, dict(co_occurrence), self.CACHE_TTL)
        
        return dict(co_occurrence)
    
    async def _get_popular_products(self, limit: int) -> List[Product]:
        """Get popular products as fallback recommendations"""
        result = await self.db.execute(
            select(Product)
            .where(Product.is_active == True)
            .order_by(Product.purchase_count.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def _get_similar_by_category(
        self,
        product_id: int,
        limit: int
    ) -> List[Product]:
        """
        Content-based fallback: products in the same category(ies) as the given product.
        Ordered by purchase_count (popularity).
        """
        # Get category IDs for this product
        result = await self.db.execute(
            select(ProductCategory.category_id).where(
                ProductCategory.product_id == product_id
            )
        )
        category_ids = [row[0] for row in result.all()]
        if not category_ids:
            return await self._get_popular_products(limit)
        # Other products in any of these categories, excluding self
        result = await self.db.execute(
            select(Product)
            .join(ProductCategory, ProductCategory.product_id == Product.id)
            .where(
                and_(
                    Product.is_active == True,
                    Product.id != product_id,
                    ProductCategory.category_id.in_(category_ids),
                )
            )
            .order_by(Product.purchase_count.desc())
            .limit(limit)
        )
        return list(result.scalars().unique().all())
    
    async def _get_products_by_ids(
        self,
        product_ids: List[int]
    ) -> List[Product]:
        """Get products by IDs maintaining order"""
        if not product_ids:
            return []
        
        result = await self.db.execute(
            select(Product)
            .where(
                and_(
                    Product.id.in_(product_ids),
                    Product.is_active == True
                )
            )
        )
        products = {p.id: p for p in result.scalars().all()}
        
        # Maintain original order
        return [products[pid] for pid in product_ids if pid in products]
