"""
Memory API - Endpoints for conversation memory management.

Provides operations for managing conversation history and cache.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional

from ..config import get_settings, Settings
from ..memory.conversation_memory import ConversationMemory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/memory", tags=["memory"])


@router.get("/{user_id}/history")
async def get_conversation_history(
    user_id: str,
    limit: Optional[int] = None,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Get conversation history for a user.
    
    Args:
        user_id: User identifier
        limit: Maximum number of messages to return
        
    Returns:
        Conversation history
    """
    try:
        memory = ConversationMemory(settings)
        history = await memory.get_history(user_id, limit)
        await memory.close()
        
        return {
            "success": True,
            "user_id": user_id,
            "messages": history,
            "count": len(history)
        }
        
    except Exception as e:
        logger.error(f"[Memory API] Error getting history for {user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get conversation history: {str(e)}"
        )


@router.get("/{user_id}/context")
async def get_conversation_context(
    user_id: str,
    max_tokens: int = 2000,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Get conversation context formatted for LLM.
    
    Args:
        user_id: User identifier
        max_tokens: Maximum tokens to include
        
    Returns:
        Formatted conversation context
    """
    try:
        memory = ConversationMemory(settings)
        context = await memory.get_context(user_id, max_tokens)
        await memory.close()
        
        return {
            "success": True,
            "user_id": user_id,
            "context": context,
            "message_count": len(context)
        }
        
    except Exception as e:
        logger.error(f"[Memory API] Error getting context for {user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get conversation context: {str(e)}"
        )


@router.get("/{user_id}/summary")
async def get_conversation_summary(
    user_id: str,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Get conversation summary for a user.
    
    Args:
        user_id: User identifier
        
    Returns:
        Conversation summary
    """
    try:
        memory = ConversationMemory(settings)
        summary = await memory.get_summary(user_id)
        await memory.close()
        
        return {
            "success": True,
            "user_id": user_id,
            "summary": summary,
            "has_summary": summary is not None
        }
        
    except Exception as e:
        logger.error(f"[Memory API] Error getting summary for {user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get conversation summary: {str(e)}"
        )


@router.get("/{user_id}/stats")
async def get_memory_stats(
    user_id: str,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Get memory statistics for a user.
    
    Args:
        user_id: User identifier
        
    Returns:
        Memory statistics
    """
    try:
        memory = ConversationMemory(settings)
        history = await memory.get_history(user_id)
        summary = await memory.get_summary(user_id)
        await memory.close()
        
        # Calculate stats
        total_messages = len(history)
        user_messages = sum(1 for msg in history if msg.get("role") == "user")
        assistant_messages = sum(1 for msg in history if msg.get("role") == "assistant")
        system_messages = sum(1 for msg in history if msg.get("role") == "system")
        
        # Calculate total characters
        total_chars = sum(len(msg.get("content", "")) for msg in history)
        
        return {
            "success": True,
            "user_id": user_id,
            "stats": {
                "total_messages": total_messages,
                "user_messages": user_messages,
                "assistant_messages": assistant_messages,
                "system_messages": system_messages,
                "total_characters": total_chars,
                "has_summary": summary is not None,
                "memory_enabled": settings.memory_enabled,
                "max_messages": settings.memory_max_messages
            }
        }
        
    except Exception as e:
        logger.error(f"[Memory API] Error getting stats for {user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get memory stats: {str(e)}"
        )


@router.delete("/{user_id}")
async def clear_conversation_memory(
    user_id: str,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Clear conversation memory for a user.
    
    Args:
        user_id: User identifier
        
    Returns:
        Success message
    """
    try:
        memory = ConversationMemory(settings)
        await memory.clear_history(user_id)
        await memory.close()
        
        logger.info(f"[Memory API] Cleared memory for user: {user_id}")
        
        return {
            "success": True,
            "message": f"Conversation memory cleared for user {user_id}"
        }
        
    except Exception as e:
        logger.error(f"[Memory API] Error clearing memory for {user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear conversation memory: {str(e)}"
        )


@router.post("/{user_id}/message")
async def add_message(
    user_id: str,
    role: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Add a message to conversation history.
    
    Args:
        user_id: User identifier
        role: Message role (user, assistant, system)
        content: Message content
        metadata: Optional metadata
        
    Returns:
        Success message
    """
    if role not in ["user", "assistant", "system"]:
        raise HTTPException(
            status_code=400,
            detail="Role must be one of: user, assistant, system"
        )
    
    try:
        memory = ConversationMemory(settings)
        await memory.add_message(user_id, role, content, metadata)
        await memory.close()
        
        return {
            "success": True,
            "message": "Message added to conversation history",
            "user_id": user_id,
            "role": role
        }
        
    except Exception as e:
        logger.error(f"[Memory API] Error adding message for {user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add message: {str(e)}"
        )


@router.get("/config")
async def get_memory_config(settings: Settings = Depends(get_settings)) -> Dict[str, Any]:
    """
    Get current memory configuration.
    
    Returns:
        Memory configuration
    """
    return {
        "enabled": settings.memory_enabled,
        "max_messages": settings.memory_max_messages,
        "summary_enabled": settings.memory_summary_enabled,
        "redis_configured": settings.get_redis_url() is not None,
        "postgres_configured": settings.get_postgres_dsn() is not None
    }


@router.get("/health")
async def memory_health(settings: Settings = Depends(get_settings)) -> Dict[str, Any]:
    """
    Check memory system health.
    
    Returns:
        Health status
    """
    health = {
        "healthy": True,
        "enabled": settings.memory_enabled,
        "storage": []
    }
    
    # Check Redis
    redis_url = settings.get_redis_url()
    if redis_url:
        try:
            import redis.asyncio as redis
            client = redis.from_url(redis_url, decode_responses=True)
            await client.ping()
            await client.close()
            health["storage"].append({
                "type": "redis",
                "status": "healthy",
                "url": redis_url
            })
        except Exception as e:
            health["healthy"] = False
            health["storage"].append({
                "type": "redis",
                "status": "unhealthy",
                "error": str(e)
            })
    else:
        health["storage"].append({
            "type": "redis",
            "status": "not_configured"
        })
    
    # Check Postgres
    postgres_dsn = settings.get_postgres_dsn()
    if postgres_dsn:
        health["storage"].append({
            "type": "postgres",
            "status": "configured"
        })
    else:
        health["storage"].append({
            "type": "postgres",
            "status": "not_configured"
        })
    
    return health
