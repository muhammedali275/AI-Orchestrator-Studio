"""
Chat API - Main orchestration endpoint.

Handles /v1/chat requests and executes the orchestration graph.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from ..config import get_settings, Settings
from ..graph import OrchestrationGraph, GraphState

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["chat"])


class ChatRequest(BaseModel):
    """Chat request model."""
    prompt: str = Field(..., description="User prompt/question")
    user_id: Optional[str] = Field(None, description="User identifier")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class ChatResponse(BaseModel):
    """Chat response model."""
    answer: str = Field(..., description="Generated answer")
    metadata: Dict[str, Any] = Field(..., description="Response metadata")
    execution_id: str = Field(..., description="Execution identifier")
    error: Optional[str] = Field(None, description="Error message if failed")


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    settings: Settings = Depends(get_settings)
) -> ChatResponse:
    """
    Main chat endpoint for orchestration.
    
    Accepts user prompts and returns orchestrated responses.
    
    Args:
        request: Chat request with prompt and metadata
        settings: Application settings (injected)
        
    Returns:
        ChatResponse with answer and metadata
    """
    logger.info(f"[Chat] Received request from user: {request.user_id or 'anonymous'}")
    
    try:
        # Create initial state
        state = GraphState(
            user_input=request.prompt,
            user_id=request.user_id,
            metadata=request.metadata or {}
        )
        
        # Initialize and execute graph
        graph = OrchestrationGraph(settings)
        
        try:
            final_state = await graph.execute(state)
        finally:
            # Always close graph resources
            await graph.close()
        
        # Build response
        response = ChatResponse(
            answer=final_state.answer or "No response generated",
            metadata=final_state.final_metadata,
            execution_id=final_state.execution_id,
            error=final_state.error
        )
        
        logger.info(f"[Chat] Completed request {final_state.execution_id}")
        
        return response
        
    except Exception as e:
        logger.error(f"[Chat] Error processing request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat request: {str(e)}"
        )


@router.get("/chat/health")
async def chat_health():
    """Health check for chat endpoint."""
    return {
        "status": "healthy",
        "service": "chat",
        "version": "1.0.0"
    }
