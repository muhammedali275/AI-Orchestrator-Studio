"""
Chat UI API - Endpoints for Chat Studio interface.

Provides conversation management, message sending, and metrics.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from ..config import get_settings, Settings
from ..db.database import get_db
from ..db.models import Conversation, Message, PromptProfile, ChatMetric
from ..services.chat_router import ChatRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat/ui", tags=["chat-ui"])


# Request/Response Models
class SendMessageRequest(BaseModel):
    """Request model for sending a message."""
    conversation_id: Optional[str] = Field(None, description="Conversation ID (creates new if not provided)")
    message: str = Field(..., description="User message")
    model_id: Optional[str] = Field(None, description="Model to use")
    routing_profile: str = Field(default="direct_llm", description="Routing profile")
    use_memory: bool = Field(default=True, description="Use conversation memory")
    use_tools: bool = Field(default=False, description="Enable tools")
    stream: bool = Field(default=False, description="Stream response")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class SendMessageResponse(BaseModel):
    """Response model for sending a message."""
    conversation_id: str
    message_id: str
    answer: str
    metadata: Dict[str, Any]
    error: Optional[str] = None


class ConversationCreate(BaseModel):
    """Request model for creating a conversation."""
    title: Optional[str] = Field(default="New Conversation", description="Conversation title")
    model_id: Optional[str] = Field(None, description="Model ID")
    routing_profile: str = Field(default="direct_llm", description="Routing profile")
    user_id: Optional[str] = Field(None, description="User ID")


class PromptProfileCreate(BaseModel):
    """Request model for creating/updating a prompt profile."""
    name: str = Field(..., description="Profile name")
    description: Optional[str] = Field(None, description="Profile description")
    system_prompt: str = Field(..., description="System prompt text")
    is_active: bool = Field(default=True, description="Active status")


# Endpoints
@router.post("/send", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db)
) -> SendMessageResponse:
    """
    Send a message and get response.
    
    Args:
        request: Message request
        settings: Application settings
        db: Database session
        
    Returns:
        Message response with answer
    """
    try:
        # Get or create conversation
        if request.conversation_id:
            conversation = db.query(Conversation).filter(
                Conversation.id == request.conversation_id,
                Conversation.is_deleted == False
            ).first()
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
        else:
            # Create new conversation
            conversation = Conversation(
                title=f"Chat {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
                model_id=request.model_id,
                routing_profile=request.routing_profile,
                user_id="default"
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
        
        # Store user message
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=request.message,
            metadata=request.metadata or {}
        )
        db.add(user_message)
        db.commit()
        
        # Route message
        router_service = ChatRouter(settings)
        try:
            result = await router_service.route_message(
                message=request.message,
                conversation_id=conversation.id,
                model_id=request.model_id or conversation.model_id,
                routing_profile=request.routing_profile,
                use_memory=request.use_memory,
                use_tools=request.use_tools,
                user_id=conversation.user_id,
                metadata=request.metadata
            )
            
            # Store assistant message
            assistant_message = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=result.get("answer", ""),
                metadata=result.get("metadata", {})
            )
            db.add(assistant_message)
            
            # Update conversation
            conversation.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(assistant_message)
            
            return SendMessageResponse(
                conversation_id=conversation.id,
                message_id=assistant_message.id,
                answer=result.get("answer", ""),
                metadata=result.get("metadata", {}),
                error=result.get("error")
            )
            
        finally:
            await router_service.close()
            
    except Exception as e:
        logger.error(f"[Chat UI] Error sending message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send/stream")
async def send_message_stream(
    request: SendMessageRequest,
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db)
):
    """
    Send a message and stream response.
    
    Args:
        request: Message request
        settings: Application settings
        db: Database session
        
    Returns:
        Streaming response
    """
    try:
        # Get or create conversation
        if request.conversation_id:
            conversation = db.query(Conversation).filter(
                Conversation.id == request.conversation_id,
                Conversation.is_deleted == False
            ).first()
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
        else:
            conversation = Conversation(
                title=f"Chat {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
                model_id=request.model_id,
                routing_profile=request.routing_profile,
                user_id="default"
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
        
        # Store user message
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=request.message,
            metadata=request.metadata or {}
        )
        db.add(user_message)
        db.commit()
        
        # Stream response
        router_service = ChatRouter(settings)
        
        async def generate():
            try:
                async for chunk in router_service.stream_message(
                    message=request.message,
                    conversation_id=conversation.id,
                    model_id=request.model_id or conversation.model_id,
                    routing_profile=request.routing_profile,
                    use_memory=request.use_memory,
                    user_id=conversation.user_id,
                    metadata=request.metadata
                ):
                    yield chunk
            finally:
                await router_service.close()
        
        return StreamingResponse(generate(), media_type="text/plain")
        
    except Exception as e:
        logger.error(f"[Chat UI] Error streaming message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations")
async def list_conversations(
    user_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    List conversations.
    
    Args:
        user_id: Filter by user ID
        limit: Maximum number of conversations
        offset: Offset for pagination
        db: Database session
        
    Returns:
        List of conversations
    """
    try:
        query = db.query(Conversation).filter(Conversation.is_deleted == False)
        
        if user_id:
            query = query.filter(Conversation.user_id == user_id)
        
        total = query.count()
        conversations = query.order_by(
            Conversation.updated_at.desc()
        ).limit(limit).offset(offset).all()
        
        return {
            "conversations": [conv.to_dict() for conv in conversations],
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"[Chat UI] Error listing conversations: {str(e)}")
        # Return empty list as fallback
        return {
            "conversations": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
            "error": str(e)
        }


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get conversation details with messages.
    
    Args:
        conversation_id: Conversation ID
        db: Database session
        
    Returns:
        Conversation with messages
    """
    try:
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.is_deleted == False
        ).first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.asc()).all()
        
        return {
            "conversation": conversation.to_dict(),
            "messages": [msg.to_dict() for msg in messages]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Chat UI] Error getting conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversations", response_model=Dict[str, Any])
async def create_conversation(
    request: ConversationCreate,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Create a new conversation.
    
    Args:
        request: Conversation creation request
        db: Database session
        
    Returns:
        Created conversation
    """
    try:
        conversation = Conversation(
            title=request.title,
            model_id=request.model_id,
            routing_profile=request.routing_profile,
            user_id=request.user_id or "default"
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        
        return {
            "success": True,
            "conversation": conversation.to_dict()
        }
        
    except Exception as e:
        logger.error(f"[Chat UI] Error creating conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Delete (soft delete) a conversation.
    
    Args:
        conversation_id: Conversation ID
        db: Database session
        
    Returns:
        Success message
    """
    try:
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        conversation.is_deleted = True
        db.commit()
        
        return {
            "success": True,
            "message": f"Conversation {conversation_id} deleted"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Chat UI] Error deleting conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def list_models(
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    List available models from LLM configuration.
    
    Args:
        settings: Application settings
        
    Returns:
        List of available models
    """
    try:
        # Try to fetch models from LLM server
        import httpx
        
        logger.info(f"[Chat UI] Fetching models from LLM server: {settings.llm_base_url}")
        
        if not settings.llm_base_url:
            logger.warning("[Chat UI] LLM base URL not configured, using default models")
            # Fallback if LLM not configured
            return {
                "success": True,
                "models": [
                    {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo"},
                    {"id": "gpt-4", "name": "GPT-4"},
                    {"id": "claude-3-opus", "name": "Claude 3 Opus"},
                    {"id": "claude-3-sonnet", "name": "Claude 3 Sonnet"},
                    {"id": "llama2-70b", "name": "Llama 2 70B"}
                ],
                "default_model": "gpt-3.5-turbo",
                "message": "Using default models (LLM not configured)"
            }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                # Detect if this is an Ollama server
                is_ollama = "11434" in settings.llm_base_url or "ollama" in settings.llm_base_url.lower()
                
                if is_ollama:
                    logger.info("[Chat UI] Detected Ollama server, using /api/tags endpoint")
                    # Try Ollama endpoint
                    ollama_url = f"{settings.llm_base_url}/api/tags"
                    logger.info(f"[Chat UI] Fetching from: {ollama_url}")
                    
                    response = await client.get(ollama_url)
                    logger.info(f"[Chat UI] Ollama response status: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        logger.info(f"[Chat UI] Ollama response data: {data}")
                        
                        models = data.get("models", [])
                        if not models:
                            logger.warning("[Chat UI] No models found in Ollama response")
                        
                        # Format for frontend - Ollama returns models with 'name' field
                        formatted_models = []
                        for m in models:
                            model_name = m.get("name", m.get("model", "unknown"))
                            formatted_models.append({
                                "id": model_name,
                                "name": model_name
                            })
                        
                        logger.info(f"[Chat UI] Formatted {len(formatted_models)} models from Ollama")
                        
                        if formatted_models:
                            return {
                                "success": True,
                                "models": formatted_models,
                                "default_model": settings.llm_default_model or formatted_models[0]["id"],
                                "source": "ollama"
                            }
                    else:
                        logger.error(f"[Chat UI] Ollama returned status {response.status_code}")
                else:
                    logger.info("[Chat UI] Using OpenAI-compatible endpoint")
                    # Try OpenAI-compatible endpoint
                    openai_url = f"{settings.llm_base_url}/v1/models"
                    logger.info(f"[Chat UI] Fetching from: {openai_url}")
                    
                    response = await client.get(openai_url)
                    logger.info(f"[Chat UI] OpenAI response status: {response.status_code}")
                    
                    if response.status_code == 200:
                        models_data = response.json()
                        models = models_data.get("data", []) if isinstance(models_data, dict) else models_data
                        
                        logger.info(f"[Chat UI] Found {len(models)} models from OpenAI-compatible endpoint")
                        
                        if models:
                            return {
                                "success": True,
                                "models": models,
                                "default_model": settings.llm_default_model or (models[0].get("id") if models else None),
                                "source": "openai-compatible"
                            }
                    else:
                        logger.error(f"[Chat UI] OpenAI endpoint returned status {response.status_code}")
                        
            except httpx.ConnectError as e:
                logger.error(f"[Chat UI] Connection error to LLM server: {str(e)}")
            except httpx.TimeoutException as e:
                logger.error(f"[Chat UI] Timeout connecting to LLM server: {str(e)}")
            except Exception as e:
                logger.error(f"[Chat UI] Error fetching models: {str(e)}", exc_info=True)
        
        # Fallback to configured default model if available
        if settings.llm_default_model:
            logger.info(f"[Chat UI] Using configured default model: {settings.llm_default_model}")
            return {
                "success": True,
                "models": [
                    {"id": settings.llm_default_model, "name": settings.llm_default_model}
                ],
                "default_model": settings.llm_default_model,
                "message": "Using configured default model (could not fetch from server)",
                "source": "config"
            }
        
        # Final fallback to generic models
        logger.warning("[Chat UI] Using fallback models")
        return {
            "success": True,
            "models": [
                {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo"},
                {"id": "gpt-4", "name": "GPT-4"},
                {"id": "claude-3-opus", "name": "Claude 3 Opus"},
                {"id": "claude-3-sonnet", "name": "Claude 3 Sonnet"},
                {"id": "llama2-70b", "name": "Llama 2 70B"}
            ],
            "default_model": "gpt-3.5-turbo",
            "message": "Using fallback models (could not connect to LLM server)",
            "source": "fallback"
        }
        
    except Exception as e:
        logger.error(f"[Chat UI] Error listing models: {str(e)}", exc_info=True)
        # Return fallback models
        return {
            "success": True,
            "models": [
                {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo"},
                {"id": "gpt-4", "name": "GPT-4"},
                {"id": "claude-3-opus", "name": "Claude 3 Opus"},
                {"id": "claude-3-sonnet", "name": "Claude 3 Sonnet"},
                {"id": "llama2-70b", "name": "Llama 2 70B"}
            ],
            "default_model": "gpt-3.5-turbo",
            "message": "Using fallback models due to error",
            "source": "fallback"
        }


@router.get("/profiles")
async def list_routing_profiles() -> Dict[str, Any]:
    """
    List available routing profiles.
    
    Returns:
        List of routing profiles
    """
    profiles = [
        {
            "id": "direct_llm",
            "name": "Direct LLM",
            "description": "Direct connection to LLM server without additional processing"
        },
        {
            "id": "zain_agent",
            "name": "Zain Agent",
            "description": "Route through Zain orchestrator agent with data access"
        },
        {
            "id": "tools_data",
            "name": "Tools + Data",
            "description": "Full orchestration with tools, data sources, and reasoning"
        }
    ]
    
    return {
        "profiles": profiles
    }


@router.get("/prompt-profiles")
async def list_prompt_profiles(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    List prompt profiles.
    
    Args:
        db: Database session
        
    Returns:
        List of prompt profiles
    """
    try:
        profiles = db.query(PromptProfile).filter(
            PromptProfile.is_active == True
        ).all()
        
        return {
            "profiles": [profile.to_dict() for profile in profiles]
        }
        
    except Exception as e:
        logger.error(f"[Chat UI] Error listing prompt profiles: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prompt-profiles")
async def create_prompt_profile(
    request: PromptProfileCreate,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Create or update a prompt profile.
    
    Args:
        request: Prompt profile data
        db: Database session
        
    Returns:
        Created/updated profile
    """
    try:
        # Check if profile exists
        existing = db.query(PromptProfile).filter(
            PromptProfile.name == request.name
        ).first()
        
        if existing:
            # Update existing
            existing.description = request.description
            existing.system_prompt = request.system_prompt
            existing.is_active = request.is_active
            existing.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing)
            profile = existing
        else:
            # Create new
            profile = PromptProfile(
                name=request.name,
                description=request.description,
                system_prompt=request.system_prompt,
                is_active=request.is_active
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)
        
        return {
            "success": True,
            "profile": profile.to_dict()
        }
        
    except Exception as e:
        logger.error(f"[Chat UI] Error creating prompt profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_metrics(
    hours: int = 24,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get aggregated chat metrics.
    
    Args:
        hours: Number of hours to look back
        db: Database session
        
    Returns:
        Aggregated metrics
    """
    try:
        since = datetime.utcnow() - timedelta(hours=hours)
        
        metrics = db.query(ChatMetric).filter(
            ChatMetric.request_timestamp >= since
        ).all()
        
        if not metrics:
            return {
                "total_requests": 0,
                "success_rate": 0,
                "avg_latency_ms": 0,
                "requests_per_hour": 0,
                "top_models": [],
                "top_profiles": []
            }
        
        # Calculate aggregates
        total = len(metrics)
        successful = sum(1 for m in metrics if m.success)
        latencies = [m.latency_ms for m in metrics if m.latency_ms]
        
        # Count by model and profile
        model_counts = {}
        profile_counts = {}
        for m in metrics:
            if m.model_id:
                model_counts[m.model_id] = model_counts.get(m.model_id, 0) + 1
            if m.routing_profile:
                profile_counts[m.routing_profile] = profile_counts.get(m.routing_profile, 0) + 1
        
        return {
            "total_requests": total,
            "success_rate": successful / total if total > 0 else 0,
            "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0,
            "requests_per_hour": total / hours,
            "top_models": sorted(model_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            "top_profiles": sorted(profile_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            "time_range_hours": hours
        }
        
    except Exception as e:
        logger.error(f"[Chat UI] Error getting metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
