"""
Redis cache utilities
- Cache-aside pattern implementation
- Distributed locking
- Rate limiting
"""

import json
from typing import Any, Optional, TypeVar, Callable
from functools import wraps
import asyncio

import redis.asyncio as redis
from redis.asyncio.lock import Lock

from app.core.config import settings

T = TypeVar("T")


class RedisCache:
    """Redis cache manager with cache-aside pattern (optional - degrades gracefully if Redis unavailable)"""
    
    def __init__(self):
        self._client: Optional[redis.Redis] = None
        self._connected: bool = False
    
    async def connect(self) -> None:
        """Initialize Redis connection"""
        try:
            self._client = redis.from_url(
                settings.REDIS_URL,
                password=settings.REDIS_PASSWORD,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self._client.ping()
            self._connected = True
        except Exception:
            self._connected = False
            self._client = None
    
    async def disconnect(self) -> None:
        """Close Redis connection"""
        if self._client:
            await self._client.close()
            self._connected = False
    
    @property
    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        return self._connected and self._client is not None
    
    @property
    def client(self) -> redis.Redis:
        """Get Redis client"""
        if not self.is_connected:
            raise RuntimeError("Redis not connected")
        return self._client
    
    # ==================== Basic Operations ====================
    
    async def get(self, key: str) -> Optional[str]:
        """Get a value from cache"""
        if not self.is_connected:
            return None
        try:
            return await self.client.get(key)
        except Exception:
            return None
    
    async def set(
        self,
        key: str,
        value: str,
        ttl: int = 600  # 10 minutes default
    ) -> bool:
        """Set a value in cache with TTL"""
        if not self.is_connected:
            return False
        try:
            return await self.client.set(key, value, ex=ttl)
        except Exception:
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete a key from cache"""
        if not self.is_connected:
            return False
        try:
            return await self.client.delete(key) > 0
        except Exception:
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.is_connected:
            return False
        try:
            return await self.client.exists(key) > 0
        except Exception:
            return False
    
    # ==================== JSON Operations ====================
    
    async def get_json(self, key: str) -> Optional[Any]:
        """Get and deserialize JSON from cache"""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except Exception:
                return None
        return None
    
    async def set_json(
        self,
        key: str,
        value: Any,
        ttl: int = 600
    ) -> bool:
        """Serialize and set JSON in cache"""
        if not self.is_connected:
            return False
        return await self.set(key, json.dumps(value, default=str), ttl)
    
    # ==================== Hash Operations ====================
    
    async def hget(self, name: str, key: str) -> Optional[str]:
        """Get a field from a hash"""
        if not self.is_connected:
            return None
        try:
            return await self.client.hget(name, key)
        except Exception:
            return None
    
    async def hset(self, name: str, key: str, value: str) -> int:
        """Set a field in a hash"""
        if not self.is_connected:
            return 0
        try:
            return await self.client.hset(name, key, value)
        except Exception:
            return 0
    
    async def hgetall(self, name: str) -> dict:
        """Get all fields from a hash"""
        if not self.is_connected:
            return {}
        try:
            return await self.client.hgetall(name)
        except Exception:
            return {}
    
    async def hdel(self, name: str, *keys: str) -> int:
        """Delete fields from a hash"""
        if not self.is_connected:
            return 0
        try:
            return await self.client.hdel(name, *keys)
        except Exception:
            return 0
    
    # ==================== Distributed Locking ====================
    
    def lock(
        self,
        name: str,
        timeout: float = 10.0,
        blocking_timeout: float = 5.0
    ) -> Optional[Lock]:
        """
        Get a distributed lock.
        
        Usage:
            async with cache.lock("lock:inventory:123"):
                # Critical section
        """
        if not self.is_connected:
            return None
        return self.client.lock(
            f"lock:{name}",
            timeout=timeout,
            blocking_timeout=blocking_timeout
        )
    
    async def acquire_lock(
        self,
        name: str,
        timeout: int = 10
    ) -> bool:
        """
        Acquire a distributed lock using SETNX pattern.
        Returns True if lock acquired, False otherwise.
        """
        if not self.is_connected:
            return True  # Allow operation to proceed without locking
        try:
            key = f"lock:{name}"
            return await self.client.set(key, "1", nx=True, ex=timeout)
        except Exception:
            return True
    
    async def release_lock(self, name: str) -> bool:
        """Release a distributed lock"""
        return await self.delete(f"lock:{name}")
    
    # ==================== Rate Limiting ====================
    
    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window: int = 60  # seconds
    ) -> tuple[bool, int]:
        """
        Check if rate limit is exceeded using sliding window.
        
        Returns:
            (is_allowed, remaining_requests)
        """
        if not self.is_connected:
            return True, limit  # No rate limiting without Redis
        try:
            current = await self.client.incr(key)
            
            if current == 1:
                await self.client.expire(key, window)
            
            remaining = max(0, limit - current)
            is_allowed = current <= limit
            
            return is_allowed, remaining
        except Exception:
            return True, limit
    
    # ==================== Cart/Session Storage ====================
    
    async def get_cart(self, user_id: str) -> dict:
        """Get user's shopping cart"""
        cart_key = f"cart:{user_id}"
        return await self.hgetall(cart_key)
    
    async def add_to_cart(
        self,
        user_id: str,
        product_id: int,
        quantity: int
    ) -> dict:
        """Add or update item in cart"""
        if not self.is_connected:
            return {}
        try:
            cart_key = f"cart:{user_id}"
            await self.hset(cart_key, str(product_id), str(quantity))
            await self.client.expire(cart_key, 86400)  # 24 hours
            return await self.get_cart(user_id)
        except Exception:
            return {}
    
    async def remove_from_cart(
        self,
        user_id: str,
        product_id: int
    ) -> dict:
        """Remove item from cart"""
        cart_key = f"cart:{user_id}"
        await self.hdel(cart_key, str(product_id))
        return await self.get_cart(user_id)
    
    async def clear_cart(self, user_id: str) -> bool:
        """Clear user's cart"""
        return await self.delete(f"cart:{user_id}")
    
    # ==================== Cache Keys ====================
    
    @staticmethod
    def product_key(product_id: int) -> str:
        """Generate cache key for a product"""
        return f"product:{product_id}"
    
    @staticmethod
    def product_list_key(page: int, per_page: int) -> str:
        """Generate cache key for product list"""
        return f"products:list:page:{page}:per_page:{per_page}"
    
    @staticmethod
    def user_key(user_id: int) -> str:
        """Generate cache key for a user"""
        return f"user:{user_id}"
    
    @staticmethod
    def recommendations_key(user_id: int) -> str:
        """Generate cache key for user recommendations"""
        return f"recommendations:{user_id}"


# Global cache instance
cache = RedisCache()


def cached(
    key_prefix: str,
    ttl: int = 600,
    key_builder: Optional[Callable[..., str]] = None
):
    """
    Decorator for caching function results.
    Falls back to direct function call if Redis unavailable.
    
    Usage:
        @cached("products", ttl=300)
        async def get_product(product_id: int):
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # If Redis not connected, just call the function
            if not cache.is_connected:
                return await func(*args, **kwargs)
            
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Default key from args
                key_parts = [key_prefix] + [str(a) for a in args]
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_value = await cache.get_json(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = await func(*args, **kwargs)
            await cache.set_json(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator
