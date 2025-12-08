"""
Cache Service - Abstraction for external caching.

Provides a unified interface for caching with different backends.
"""

import logging
import json
import time
from typing import Dict, Any, Optional, Union, List

from ..config.config_service import ConfigService

logger = logging.getLogger(__name__)


class CacheService:
    """
    Cache service for AIPanel.
    
    Abstracts external caching (Redis/Postgres/etc).
    """
    
    def __init__(self, config_service: ConfigService):
        """
        Initialize cache service.
        
        Args:
            config_service: Configuration service
        """
        self.config_service = config_service
        self._cache_client = None
        self._cache_type = None
        self._initialize_cache()
    
    def _initialize_cache(self) -> None:
        """Initialize cache client based on configuration."""
        # Get cache configuration
        cache_enabled = self.config_service.cache_enabled
        if not cache_enabled:
            logger.info("Cache is disabled in configuration")
            return
        
        # Determine cache type
        if self.config_service.get_redis_url():
            self._initialize_redis_cache()
            self._cache_type = "redis"
        elif self.config_service.get_postgres_dsn():
            self._initialize_postgres_cache()
            self._cache_type = "postgres"
        else:
            self._initialize_memory_cache()
            self._cache_type = "memory"
    
    def _initialize_redis_cache(self) -> None:
        """Initialize Redis cache client."""
        try:
            import redis
            
            redis_url = self.config_service.get_redis_url()
            if not redis_url:
                logger.warning("Redis URL not configured, falling back to in-memory cache")
                self._initialize_memory_cache()
                return
            
            self._cache_client = redis.from_url(redis_url)
            logger.info("Initialized Redis cache client")
            
        except ImportError:
            logger.warning("Redis package not installed, falling back to in-memory cache")
            self._initialize_memory_cache()
        except Exception as e:
            logger.error(f"Error initializing Redis cache: {str(e)}")
            self._initialize_memory_cache()
    
    def _initialize_postgres_cache(self) -> None:
        """Initialize PostgreSQL cache client."""
        try:
            import psycopg2
            import psycopg2.extras
            
            postgres_dsn = self.config_service.get_postgres_dsn()
            if not postgres_dsn:
                logger.warning("PostgreSQL DSN not configured, falling back to in-memory cache")
                self._initialize_memory_cache()
                return
            
            # Connect to PostgreSQL
            conn = psycopg2.connect(postgres_dsn)
            
            # Create cache table if it doesn't exist
            with conn.cursor() as cur:
                cur.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value JSONB,
                    expires_at TIMESTAMP WITH TIME ZONE
                )
                """)
                conn.commit()
            
            self._cache_client = conn
            logger.info("Initialized PostgreSQL cache client")
            
        except ImportError:
            logger.warning("psycopg2 package not installed, falling back to in-memory cache")
            self._initialize_memory_cache()
        except Exception as e:
            logger.error(f"Error initializing PostgreSQL cache: {str(e)}")
            self._initialize_memory_cache()
    
    def _initialize_memory_cache(self) -> None:
        """Initialize in-memory cache."""
        self._cache_client = {}
        self._cache_type = "memory"
        logger.info("Initialized in-memory cache")
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        if not self._cache_client:
            return None
        
        try:
            if self._cache_type == "redis":
                return await self._get_from_redis(key)
            elif self._cache_type == "postgres":
                return await self._get_from_postgres(key)
            else:
                return self._get_from_memory(key)
        except Exception as e:
            logger.error(f"Error getting from cache: {str(e)}")
            return None
    
    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds (None for default)
            
        Returns:
            True if successful, False otherwise
        """
        if not self._cache_client:
            return False
        
        # Use default TTL if not provided
        if ttl_seconds is None:
            ttl_seconds = self.config_service.cache_ttl_seconds
        
        try:
            if self._cache_type == "redis":
                return await self._set_in_redis(key, value, ttl_seconds)
            elif self._cache_type == "postgres":
                return await self._set_in_postgres(key, value, ttl_seconds)
            else:
                return self._set_in_memory(key, value, ttl_seconds)
        except Exception as e:
            logger.error(f"Error setting in cache: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        if not self._cache_client:
            return False
        
        try:
            if self._cache_type == "redis":
                return await self._delete_from_redis(key)
            elif self._cache_type == "postgres":
                return await self._delete_from_postgres(key)
            else:
                return self._delete_from_memory(key)
        except Exception as e:
            logger.error(f"Error deleting from cache: {str(e)}")
            return False
    
    async def clear(self) -> bool:
        """
        Clear all values from cache.
        
        Returns:
            True if successful, False otherwise
        """
        if not self._cache_client:
            return False
        
        try:
            if self._cache_type == "redis":
                return await self._clear_redis()
            elif self._cache_type == "postgres":
                return await self._clear_postgres()
            else:
                return self._clear_memory()
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False
    
    async def close(self) -> None:
        """Close cache client."""
        if not self._cache_client:
            return
        
        try:
            if self._cache_type == "redis":
                await self._close_redis()
            elif self._cache_type == "postgres":
                await self._close_postgres()
        except Exception as e:
            logger.error(f"Error closing cache client: {str(e)}")
    
    # Redis implementation
    
    async def _get_from_redis(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        try:
            # Use aioredis if available
            if hasattr(self._cache_client, "get"):
                value = await self._cache_client.get(key)
            else:
                # Fall back to synchronous Redis
                value = self._cache_client.get(key)
            
            if value is None:
                return None
            
            # Deserialize JSON
            return json.loads(value)
        except Exception as e:
            logger.error(f"Error getting from Redis cache: {str(e)}")
            return None
    
    async def _set_in_redis(self, key: str, value: Any, ttl_seconds: int) -> bool:
        """Set value in Redis cache."""
        try:
            # Serialize value to JSON
            serialized = json.dumps(value)
            
            # Use aioredis if available
            if hasattr(self._cache_client, "setex"):
                await self._cache_client.setex(key, ttl_seconds, serialized)
            else:
                # Fall back to synchronous Redis
                self._cache_client.setex(key, ttl_seconds, serialized)
            
            return True
        except Exception as e:
            logger.error(f"Error setting in Redis cache: {str(e)}")
            return False
    
    async def _delete_from_redis(self, key: str) -> bool:
        """Delete value from Redis cache."""
        try:
            # Use aioredis if available
            if hasattr(self._cache_client, "delete"):
                await self._cache_client.delete(key)
            else:
                # Fall back to synchronous Redis
                self._cache_client.delete(key)
            
            return True
        except Exception as e:
            logger.error(f"Error deleting from Redis cache: {str(e)}")
            return False
    
    async def _clear_redis(self) -> bool:
        """Clear all values from Redis cache."""
        try:
            # Use aioredis if available
            if hasattr(self._cache_client, "flushdb"):
                await self._cache_client.flushdb()
            else:
                # Fall back to synchronous Redis
                self._cache_client.flushdb()
            
            return True
        except Exception as e:
            logger.error(f"Error clearing Redis cache: {str(e)}")
            return False
    
    async def _close_redis(self) -> None:
        """Close Redis client."""
        try:
            # Use aioredis if available
            if hasattr(self._cache_client, "close"):
                await self._cache_client.close()
            elif hasattr(self._cache_client, "connection_pool"):
                self._cache_client.connection_pool.disconnect()
        except Exception as e:
            logger.error(f"Error closing Redis client: {str(e)}")
    
    # PostgreSQL implementation
    
    async def _get_from_postgres(self, key: str) -> Optional[Any]:
        """Get value from PostgreSQL cache."""
        try:
            # Get connection
            conn = self._cache_client
            
            # Execute query
            with conn.cursor() as cur:
                cur.execute("""
                SELECT value FROM cache
                WHERE key = %s AND (expires_at IS NULL OR expires_at > NOW())
                """, (key,))
                
                result = cur.fetchone()
                
                if result is None:
                    return None
                
                return result[0]
        except Exception as e:
            logger.error(f"Error getting from PostgreSQL cache: {str(e)}")
            return None
    
    async def _set_in_postgres(self, key: str, value: Any, ttl_seconds: int) -> bool:
        """Set value in PostgreSQL cache."""
        try:
            # Get connection
            conn = self._cache_client
            
            # Execute query
            with conn.cursor() as cur:
                cur.execute("""
                INSERT INTO cache (key, value, expires_at)
                VALUES (%s, %s, NOW() + INTERVAL '%s SECONDS')
                ON CONFLICT (key) DO UPDATE
                SET value = EXCLUDED.value, expires_at = EXCLUDED.expires_at
                """, (key, json.dumps(value), ttl_seconds))
                
                conn.commit()
            
            return True
        except Exception as e:
            logger.error(f"Error setting in PostgreSQL cache: {str(e)}")
            return False
    
    async def _delete_from_postgres(self, key: str) -> bool:
        """Delete value from PostgreSQL cache."""
        try:
            # Get connection
            conn = self._cache_client
            
            # Execute query
            with conn.cursor() as cur:
                cur.execute("DELETE FROM cache WHERE key = %s", (key,))
                conn.commit()
            
            return True
        except Exception as e:
            logger.error(f"Error deleting from PostgreSQL cache: {str(e)}")
            return False
    
    async def _clear_postgres(self) -> bool:
        """Clear all values from PostgreSQL cache."""
        try:
            # Get connection
            conn = self._cache_client
            
            # Execute query
            with conn.cursor() as cur:
                cur.execute("DELETE FROM cache")
                conn.commit()
            
            return True
        except Exception as e:
            logger.error(f"Error clearing PostgreSQL cache: {str(e)}")
            return False
    
    async def _close_postgres(self) -> None:
        """Close PostgreSQL client."""
        try:
            if self._cache_client:
                self._cache_client.close()
        except Exception as e:
            logger.error(f"Error closing PostgreSQL client: {str(e)}")
    
    # In-memory implementation
    
    def _get_from_memory(self, key: str) -> Optional[Any]:
        """Get value from in-memory cache."""
        try:
            # Check if key exists
            if key not in self._cache_client:
                return None
            
            # Get value and expiration time
            value, expires_at = self._cache_client[key]
            
            # Check if expired
            if expires_at is not None and time.time() > expires_at:
                # Remove expired value
                del self._cache_client[key]
                return None
            
            return value
        except Exception as e:
            logger.error(f"Error getting from in-memory cache: {str(e)}")
            return None
    
    def _set_in_memory(self, key: str, value: Any, ttl_seconds: int) -> bool:
        """Set value in in-memory cache."""
        try:
            # Calculate expiration time
            expires_at = time.time() + ttl_seconds if ttl_seconds > 0 else None
            
            # Store value and expiration time
            self._cache_client[key] = (value, expires_at)
            
            return True
        except Exception as e:
            logger.error(f"Error setting in in-memory cache: {str(e)}")
            return False
    
    def _delete_from_memory(self, key: str) -> bool:
        """Delete value from in-memory cache."""
        try:
            # Check if key exists
            if key in self._cache_client:
                del self._cache_client[key]
            
            return True
        except Exception as e:
            logger.error(f"Error deleting from in-memory cache: {str(e)}")
            return False
    
    def _clear_memory(self) -> bool:
        """Clear all values from in-memory cache."""
        try:
            self._cache_client.clear()
            return True
        except Exception as e:
            logger.error(f"Error clearing in-memory cache: {str(e)}")
            return False
