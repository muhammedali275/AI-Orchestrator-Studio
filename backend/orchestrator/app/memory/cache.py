"""
Cache Manager - Response caching for performance optimization.

Uses Redis from Settings - no hard-coded DSNs.
"""

import logging
import json
import hashlib
from typing import Any, Optional
from ..config import Settings

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Manages response caching using Redis or in-memory fallback.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize cache manager with settings.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.enabled = settings.cache_enabled
        self.ttl = settings.cache_ttl_seconds
        self.redis_url = settings.get_redis_url()
        
        # Redis client (lazy initialization)
        self._redis_client = None
        
        # In-memory fallback
        self._memory_cache: dict[str, Any] = {}
    
    async def _get_redis_client(self):
        """Get or create Redis client."""
        if self._redis_client is None and self.redis_url:
            try:
                import redis.asyncio as redis
                self._redis_client = redis.from_url(
                    self.redis_url,
                    decode_responses=True
                )
                logger.info("[Cache] Connected to Redis")
            except ImportError:
                logger.warning("[Cache] redis package not installed, using in-memory cache")
            except Exception as e:
                logger.warning(f"[Cache] Redis connection failed: {str(e)}, using in-memory cache")
        
        return self._redis_client
    
    def _generate_key(self, prefix: str, data: Any) -> str:
        """
        Generate cache key from data.
        
        Args:
            prefix: Key prefix
            data: Data to hash
            
        Returns:
            Cache key
        """
        # Convert data to JSON string and hash it
        data_str = json.dumps(data, sort_keys=True)
        data_hash = hashlib.sha256(data_str.encode()).hexdigest()
        return f"{prefix}:{data_hash}"
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if not self.enabled:
            return None
        
        redis_client = await self._get_redis_client()
        
        if redis_client:
            try:
                value = await redis_client.get(key)
                if value:
                    logger.debug(f"[Cache] Hit: {key}")
                    return json.loads(value)
                else:
                    logger.debug(f"[Cache] Miss: {key}")
                    return None
            except Exception as e:
                logger.error(f"[Cache] Redis error: {str(e)}, checking in-memory")
                return self._memory_cache.get(key)
        else:
            return self._memory_cache.get(key)
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if not provided)
        """
        if not self.enabled:
            return
        
        ttl = ttl or self.ttl
        
        redis_client = await self._get_redis_client()
        
        if redis_client:
            try:
                value_str = json.dumps(value)
                await redis_client.set(key, value_str, ex=ttl)
                logger.debug(f"[Cache] Set: {key} (TTL: {ttl}s)")
            except Exception as e:
                logger.error(f"[Cache] Redis error: {str(e)}, falling back to in-memory")
                self._memory_cache[key] = value
        else:
            self._memory_cache[key] = value
    
    async def delete(self, key: str) -> None:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
        """
        redis_client = await self._get_redis_client()
        
        if redis_client:
            try:
                await redis_client.delete(key)
                logger.debug(f"[Cache] Deleted: {key}")
            except Exception as e:
                logger.error(f"[Cache] Redis error: {str(e)}")
        
        # Also delete from in-memory
        if key in self._memory_cache:
            del self._memory_cache[key]
    
    async def clear(self, pattern: Optional[str] = None) -> None:
        """
        Clear cache entries.
        
        Args:
            pattern: Key pattern to match (e.g., "llm:*")
                    If None, clears all cache
        """
        redis_client = await self._get_redis_client()
        
        if redis_client:
            try:
                if pattern:
                    # Delete keys matching pattern
                    cursor = 0
                    while True:
                        cursor, keys = await redis_client.scan(
                            cursor=cursor,
                            match=pattern,
                            count=100
                        )
                        if keys:
                            await redis_client.delete(*keys)
                        if cursor == 0:
                            break
                else:
                    # Clear all cache
                    await redis_client.flushdb()
                
                logger.info(f"[Cache] Cleared: {pattern or 'all'}")
            except Exception as e:
                logger.error(f"[Cache] Redis error: {str(e)}")
        
        # Clear in-memory cache
        if pattern:
            keys_to_delete = [k for k in self._memory_cache.keys() if pattern.replace("*", "") in k]
            for key in keys_to_delete:
                del self._memory_cache[key]
        else:
            self._memory_cache.clear()
    
    async def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Cache statistics
        """
        redis_client = await self._get_redis_client()
        
        if redis_client:
            try:
                info = await redis_client.info("stats")
                return {
                    "backend": "redis",
                    "hits": info.get("keyspace_hits", 0),
                    "misses": info.get("keyspace_misses", 0),
                    "hit_rate": self._calculate_hit_rate(
                        info.get("keyspace_hits", 0),
                        info.get("keyspace_misses", 0)
                    ),
                    "keys": await redis_client.dbsize()
                }
            except Exception as e:
                logger.error(f"[Cache] Redis error: {str(e)}")
        
        return {
            "backend": "in-memory",
            "keys": len(self._memory_cache),
            "hits": 0,
            "misses": 0,
            "hit_rate": 0.0
        }
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate."""
        total = hits + misses
        if total == 0:
            return 0.0
        return round(hits / total, 3)
    
    async def close(self):
        """Close Redis connection."""
        if self._redis_client:
            await self._redis_client.close()
