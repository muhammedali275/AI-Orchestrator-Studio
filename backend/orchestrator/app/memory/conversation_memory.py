"""
Conversation Memory - Manages conversation history and context.

Uses Redis/DB from Settings - no hard-coded DSNs.
"""

import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..config import Settings

logger = logging.getLogger(__name__)


class ConversationMemory:
    """
    Manages conversation history and context.
    
    Stores messages in Redis or in-memory fallback.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize conversation memory with settings.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.enabled = settings.memory_enabled
        self.max_messages = settings.memory_max_messages
        self.redis_url = settings.get_redis_url()
        
        # Redis client (lazy initialization)
        self._redis_client = None
        
        # In-memory fallback
        self._memory_store: Dict[str, List[Dict[str, Any]]] = {}
    
    async def _get_redis_client(self):
        """Get or create Redis client."""
        if self._redis_client is None and self.redis_url:
            try:
                import redis.asyncio as redis
                self._redis_client = redis.from_url(
                    self.redis_url,
                    decode_responses=True
                )
                logger.info("[Memory] Connected to Redis")
            except ImportError:
                logger.warning("[Memory] redis package not installed, using in-memory storage")
            except Exception as e:
                logger.warning(f"[Memory] Redis connection failed: {str(e)}, using in-memory storage")
        
        return self._redis_client
    
    async def add_message(
        self,
        user_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a message to conversation history.
        
        Args:
            user_id: User identifier
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Additional metadata
        """
        if not self.enabled:
            return
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        redis_client = await self._get_redis_client()
        
        if redis_client:
            try:
                key = f"conversation:{user_id}"
                await redis_client.lpush(key, json.dumps(message))
                await redis_client.ltrim(key, 0, self.max_messages - 1)
                await redis_client.expire(key, self.settings.redis_ttl_seconds)
                logger.debug(f"[Memory] Added message to Redis for user {user_id}")
            except Exception as e:
                logger.error(f"[Memory] Redis error: {str(e)}, falling back to in-memory")
                self._add_to_memory(user_id, message)
        else:
            self._add_to_memory(user_id, message)
    
    def _add_to_memory(self, user_id: str, message: Dict[str, Any]) -> None:
        """Add message to in-memory store."""
        if user_id not in self._memory_store:
            self._memory_store[user_id] = []
        
        self._memory_store[user_id].insert(0, message)
        
        # Trim to max messages
        if len(self._memory_store[user_id]) > self.max_messages:
            self._memory_store[user_id] = self._memory_store[user_id][:self.max_messages]
    
    async def get_history(
        self,
        user_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of messages to return
            
        Returns:
            List of messages (newest first)
        """
        if not self.enabled:
            return []
        
        limit = limit or self.max_messages
        
        redis_client = await self._get_redis_client()
        
        if redis_client:
            try:
                key = f"conversation:{user_id}"
                messages = await redis_client.lrange(key, 0, limit - 1)
                return [json.loads(msg) for msg in messages]
            except Exception as e:
                logger.error(f"[Memory] Redis error: {str(e)}, falling back to in-memory")
                return self._memory_store.get(user_id, [])[:limit]
        else:
            return self._memory_store.get(user_id, [])[:limit]
    
    async def get_context(
        self,
        user_id: str,
        max_tokens: int = 2000
    ) -> List[Dict[str, str]]:
        """
        Get conversation context formatted for LLM.
        
        Args:
            user_id: User identifier
            max_tokens: Approximate maximum tokens (rough estimate)
            
        Returns:
            List of messages formatted for LLM
        """
        history = await self.get_history(user_id)
        
        # Reverse to get chronological order
        history = list(reversed(history))
        
        # Simple token estimation (4 chars ≈ 1 token)
        context = []
        total_chars = 0
        max_chars = max_tokens * 4
        
        for msg in history:
            msg_chars = len(msg["content"])
            if total_chars + msg_chars > max_chars:
                break
            
            context.append({
                "role": msg["role"],
                "content": msg["content"]
            })
            total_chars += msg_chars
        
        return context
    
    async def clear_history(self, user_id: str) -> None:
        """
        Clear conversation history for a user.
        
        Args:
            user_id: User identifier
        """
        redis_client = await self._get_redis_client()
        
        if redis_client:
            try:
                key = f"conversation:{user_id}"
                await redis_client.delete(key)
                logger.info(f"[Memory] Cleared Redis history for user {user_id}")
            except Exception as e:
                logger.error(f"[Memory] Redis error: {str(e)}")
        
        # Also clear in-memory
        if user_id in self._memory_store:
            del self._memory_store[user_id]
    
    async def get_summary(self, user_id: str) -> Optional[str]:
        """
        Get conversation summary (if enabled).
        
        Args:
            user_id: User identifier
            
        Returns:
            Summary text or None
        """
        if not self.settings.memory_summary_enabled:
            return None
        
        redis_client = await self._get_redis_client()
        
        if redis_client:
            try:
                key = f"conversation_summary:{user_id}"
                summary = await redis_client.get(key)
                return summary
            except Exception as e:
                logger.error(f"[Memory] Redis error: {str(e)}")
        
        return None
    
    async def save_summary(self, user_id: str, summary: str) -> None:
        """
        Save conversation summary.
        
        Args:
            user_id: User identifier
            summary: Summary text
        """
        if not self.settings.memory_summary_enabled:
            return
        
        redis_client = await self._get_redis_client()
        
        if redis_client:
            try:
                key = f"conversation_summary:{user_id}"
                await redis_client.set(key, summary, ex=self.settings.redis_ttl_seconds)
                logger.info(f"[Memory] Saved summary for user {user_id}")
            except Exception as e:
                logger.error(f"[Memory] Redis error: {str(e)}")
    
    async def close(self):
        """Close Redis connection."""
        if self._redis_client:
            await self._redis_client.close()
