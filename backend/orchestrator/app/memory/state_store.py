"""
State Store - Persists graph execution state.

Uses Redis/DB from Settings - no hard-coded DSNs.
"""

import logging
import json
from typing import Any, Optional, Dict
from datetime import datetime
from ..config import Settings

logger = logging.getLogger(__name__)


class StateStore:
    """
    Manages graph execution state persistence.
    
    Stores intermediate states for resumption and debugging.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize state store with settings.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.redis_url = settings.get_redis_url()
        
        # Redis client (lazy initialization)
        self._redis_client = None
        
        # In-memory fallback
        self._memory_store: Dict[str, Dict[str, Any]] = {}
    
    async def _get_redis_client(self):
        """Get or create Redis client."""
        if self._redis_client is None and self.redis_url:
            try:
                import redis.asyncio as redis
                self._redis_client = redis.from_url(
                    self.redis_url,
                    decode_responses=True
                )
                logger.info("[StateStore] Connected to Redis")
            except ImportError:
                logger.warning("[StateStore] redis package not installed, using in-memory storage")
            except Exception as e:
                logger.warning(f"[StateStore] Redis connection failed: {str(e)}, using in-memory storage")
        
        return self._redis_client
    
    async def save_state(
        self,
        execution_id: str,
        state: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> None:
        """
        Save execution state.
        
        Args:
            execution_id: Unique execution identifier
            state: State data to save
            ttl: Time to live in seconds (uses default if not provided)
        """
        ttl = ttl or self.settings.redis_ttl_seconds
        
        state_data = {
            "state": state,
            "timestamp": datetime.utcnow().isoformat(),
            "execution_id": execution_id
        }
        
        redis_client = await self._get_redis_client()
        
        if redis_client:
            try:
                key = f"state:{execution_id}"
                await redis_client.set(key, json.dumps(state_data), ex=ttl)
                logger.debug(f"[StateStore] Saved state for execution {execution_id}")
            except Exception as e:
                logger.error(f"[StateStore] Redis error: {str(e)}, falling back to in-memory")
                self._memory_store[execution_id] = state_data
        else:
            self._memory_store[execution_id] = state_data
    
    async def load_state(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Load execution state.
        
        Args:
            execution_id: Unique execution identifier
            
        Returns:
            State data or None if not found
        """
        redis_client = await self._get_redis_client()
        
        if redis_client:
            try:
                key = f"state:{execution_id}"
                state_str = await redis_client.get(key)
                if state_str:
                    state_data = json.loads(state_str)
                    logger.debug(f"[StateStore] Loaded state for execution {execution_id}")
                    return state_data.get("state")
                else:
                    logger.debug(f"[StateStore] No state found for execution {execution_id}")
                    return None
            except Exception as e:
                logger.error(f"[StateStore] Redis error: {str(e)}, checking in-memory")
                state_data = self._memory_store.get(execution_id)
                return state_data.get("state") if state_data else None
        else:
            state_data = self._memory_store.get(execution_id)
            return state_data.get("state") if state_data else None
    
    async def delete_state(self, execution_id: str) -> None:
        """
        Delete execution state.
        
        Args:
            execution_id: Unique execution identifier
        """
        redis_client = await self._get_redis_client()
        
        if redis_client:
            try:
                key = f"state:{execution_id}"
                await redis_client.delete(key)
                logger.debug(f"[StateStore] Deleted state for execution {execution_id}")
            except Exception as e:
                logger.error(f"[StateStore] Redis error: {str(e)}")
        
        # Also delete from in-memory
        if execution_id in self._memory_store:
            del self._memory_store[execution_id]
    
    async def list_states(self, pattern: str = "*") -> list[str]:
        """
        List execution IDs matching pattern.
        
        Args:
            pattern: Pattern to match (e.g., "user_123_*")
            
        Returns:
            List of execution IDs
        """
        redis_client = await self._get_redis_client()
        
        if redis_client:
            try:
                keys = []
                cursor = 0
                while True:
                    cursor, batch = await redis_client.scan(
                        cursor=cursor,
                        match=f"state:{pattern}",
                        count=100
                    )
                    keys.extend([k.replace("state:", "") for k in batch])
                    if cursor == 0:
                        break
                return keys
            except Exception as e:
                logger.error(f"[StateStore] Redis error: {str(e)}")
                return list(self._memory_store.keys())
        else:
            return list(self._memory_store.keys())
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get state store statistics.
        
        Returns:
            Statistics dictionary
        """
        redis_client = await self._get_redis_client()
        
        if redis_client:
            try:
                # Count state keys
                count = 0
                cursor = 0
                while True:
                    cursor, keys = await redis_client.scan(
                        cursor=cursor,
                        match="state:*",
                        count=100
                    )
                    count += len(keys)
                    if cursor == 0:
                        break
                
                return {
                    "backend": "redis",
                    "total_states": count
                }
            except Exception as e:
                logger.error(f"[StateStore] Redis error: {str(e)}")
        
        return {
            "backend": "in-memory",
            "total_states": len(self._memory_store)
        }
    
    async def close(self):
        """Close Redis connection."""
        if self._redis_client:
            await self._redis_client.close()
