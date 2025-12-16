"""
Memory Management API - Endpoints for viewing and managing conversation memory.

Provides inspection and clearing of conversation memory used for multi-turn interactions.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from ..config import get_settings, Settings
from ..db.database import get_db
from ..db.models import Conversation
from ..memory import ConversationMemory
from .error_handling import create_error_response, ErrorCode

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/memory", tags=["memory"])


class MemoryEntry(BaseModel):
    """A single memory entry."""
    role: str
    content: str
    tokens: Optional[int] = None


class ConversationMemoryInfo(BaseModel):
    """Information about conversation memory."""
    conversation_id: str
    message_count: int
    total_tokens: int
    memory_entries: List[MemoryEntry]
    size_bytes: int


@router.get("/conversations/{conversation_id}", response_model=ConversationMemoryInfo)
async def get_conversation_memory(
    conversation_id: str,
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db)
) -> ConversationMemoryInfo:
    """
    Get memory for a specific conversation.
    
    Shows all messages stored in conversation memory for multi-turn context.
    
    Args:
        conversation_id: Conversation ID
        settings: Application settings
        db: Database session
        
    Returns:
        Conversation memory information
    """
    try:
        # Verify conversation exists
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.is_deleted == False
        ).first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Get memory for this conversation
        memory_manager = ConversationMemory(settings)
        memory_data = memory_manager.get_conversation_context(conversation_id)
        
        # Count tokens and calculate size
        total_tokens = 0
        total_size = 0
        memory_entries = []
        
        if memory_data and "messages" in memory_data:
            for msg in memory_data["messages"]:
                tokens = msg.get("tokens", 0)
                content = msg.get("content", "")
                total_tokens += tokens
                total_size += len(content.encode("utf-8"))
                
                memory_entries.append(MemoryEntry(
                    role=msg.get("role", "unknown"),
                    content=content,
                    tokens=tokens if tokens > 0 else None
                ))
        
        return ConversationMemoryInfo(
            conversation_id=conversation_id,
            message_count=len(memory_entries),
            total_tokens=total_tokens,
            memory_entries=memory_entries,
            size_bytes=total_size
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Memory API] Error getting conversation memory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conversations/{conversation_id}")
async def clear_conversation_memory(
    conversation_id: str,
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Clear memory for a specific conversation.
    
    Removes all stored messages from conversation memory. Does not delete actual messages.
    
    Args:
        conversation_id: Conversation ID
        settings: Application settings
        db: Database session
        
    Returns:
        Success response
    """
    try:
        # Verify conversation exists
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.is_deleted == False
        ).first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Clear memory
        memory_manager = ConversationMemory(settings)
        memory_manager.clear_conversation(conversation_id)
        
        logger.info(f"[Memory API] Cleared memory for conversation {conversation_id}")
        
        return {
            "success": True,
            "message": f"Memory cleared for conversation {conversation_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Memory API] Error clearing conversation memory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("")
async def clear_all_memory(
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Clear all conversation memory.
    
    WARNING: This removes memory for ALL conversations. Use with caution.
    Does not delete actual messages from database.
    
    Args:
        settings: Application settings
        
    Returns:
        Success response
    """
    try:
        memory_manager = ConversationMemory(settings)
        memory_manager.clear_all()
        
        logger.warning("[Memory API] Cleared all conversation memory")
        
        return {
            "success": True,
            "message": "All conversation memory cleared",
            "warning": "This removes memory for all conversations. Message history is preserved."
        }
        
    except Exception as e:
        logger.error(f"[Memory API] Error clearing all memory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_memory_stats(
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Get memory usage statistics.
    
    Returns information about how much memory is being used across all conversations.
    
    Args:
        settings: Application settings
        
    Returns:
        Memory statistics
    """
    try:
        memory_manager = ConversationMemory(settings)
        stats = memory_manager.get_stats()
        
        return {
            "total_conversations": stats.get("total_conversations", 0),
            "total_messages_in_memory": stats.get("total_messages", 0),
            "total_tokens": stats.get("total_tokens", 0),
            "total_size_mb": stats.get("total_size_bytes", 0) / (1024 * 1024),
            "largest_conversation": stats.get("largest_conversation", None),
            "timestamp": stats.get("timestamp", None)
        }
        
    except Exception as e:
        logger.error(f"[Memory API] Error getting memory stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
