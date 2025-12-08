"""
Chat API routes for AIpanel.

Implements chat endpoints for orchestration.
"""

import logging
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db.session import get_db
from ..security import get_current_user, User
from ..orchestrator.executor import run_flow

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    """Chat request model."""
    prompt: str = Field(..., description="User prompt/question")
    agent: str = Field(default=settings.DEFAULT_AGENT_NAME, description="Agent name")
    user_id: Optional[str] = Field(None, description="User identifier")
    session_id: Optional[str] = Field(None, description="Chat session identifier")


class ChatResponse(BaseModel):
    """Chat response model."""
    answer: str = Field(..., description="Generated answer")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Sources used")
    trace_id: str = Field(..., description="Trace identifier")
    error: Optional[str] = Field(None, description="Error message if failed")


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ChatResponse:
    """
    Chat endpoint.
    
    Processes user prompt through orchestration flow.
    
    Args:
        request: Chat request
        user: Authenticated user
        db: Database session
        
    Returns:
        Chat response
    """
    logger.info(f"[API:Chat] Request from user {user.username}: {request.prompt[:50]}...")
    
    try:
        # Use authenticated user ID if not provided
        user_id = request.user_id or user.username
        
        # Run flow
        result = await run_flow(
            user_input=request.prompt,
            agent_name=request.agent,
            user_id=user_id,
            session_id=request.session_id,
            db=db
        )
        
        # Build response
        response = ChatResponse(
            answer=result["answer"],
            sources=result.get("sources", []),
            trace_id=result["execution_id"],
            error=result.get("error")
        )
        
        return response
        
    except Exception as e:
        logger.error(f"[API:Chat] Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat request: {str(e)}"
        )


@router.post("/chat/test", response_model=ChatResponse)
async def chat_test(
    request: ChatRequest,
    db: Session = Depends(get_db)
) -> ChatResponse:
    """
    Test chat endpoint.
    
    Same as /chat but without authentication for internal testing.
    
    Args:
        request: Chat request
        db: Database session
        
    Returns:
        Chat response
    """
    logger.info(f"[API:ChatTest] Test request: {request.prompt[:50]}...")
    
    try:
        # Run flow
        result = await run_flow(
            user_input=request.prompt,
            agent_name=request.agent,
            user_id=request.user_id,
            session_id=request.session_id,
            db=db
        )
        
        # Build response
        response = ChatResponse(
            answer=result["answer"],
            sources=result.get("sources", []),
            trace_id=result["execution_id"],
            error=result.get("error")
        )
        
        return response
        
    except Exception as e:
        logger.error(f"[API:ChatTest] Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat request: {str(e)}"
        )


@router.get("/chat/sessions")
async def get_chat_sessions(
    user_id: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get chat sessions.
    
    Args:
        user_id: Filter by user ID
        limit: Maximum number of sessions to return
        user: Authenticated user
        db: Database session
        
    Returns:
        List of chat sessions
    """
    from ..db.models import ChatSession
    
    # Use authenticated user ID if not provided
    user_id = user_id or user.username
    
    # Query sessions
    query = db.query(ChatSession).filter(
        ChatSession.user_id == user_id,
        ChatSession.is_deleted == False
    ).order_by(ChatSession.updated_at.desc()).limit(limit)
    
    sessions = query.all()
    
    return {
        "sessions": [session.to_dict() for session in sessions]
    }


@router.get("/chat/messages/{session_id}")
async def get_chat_messages(
    session_id: str,
    limit: int = Query(50, ge=1, le=1000),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get chat messages for a session.
    
    Args:
        session_id: Chat session ID
        limit: Maximum number of messages to return
        user: Authenticated user
        db: Database session
        
    Returns:
        List of chat messages
    """
    from ..db.models import ChatSession, Message
    
    # Check session exists and belongs to user
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Chat session not found: {session_id}"
        )
    
    # Query messages
    query = db.query(Message).filter(
        Message.chat_session_id == session_id
    ).order_by(Message.created_at.desc()).limit(limit)
    
    messages = query.all()
    
    return {
        "session": session.to_dict(),
        "messages": [message.to_dict() for message in messages]
    }
