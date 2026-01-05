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
from .model_standardization import ModelParser, ModelValidator, ModelProvider
from ..db.database import get_db
from ..db.models import Conversation, Message, PromptProfile, ChatMetric
from ..services.chat_router import ChatRouter
from .error_handling import (
    ErrorCode, ErrorResponse, create_error_response,
    handle_conversation_not_found_error, handle_internal_server_error,
    HTTPExceptionWithErrorCode
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat/ui", tags=["chat-ui"])


# Request/Response Models
class SendMessageRequest(BaseModel):
    """Request model for sending a message."""
    conversation_id: Optional[str] = Field(None, description="Conversation ID (creates new if not provided)")
    message: str = Field(..., description="User message")
    model_id: Optional[str] = Field(None, description="Model to use")
    connection_id: Optional[str] = Field(None, description="LLM connection ID to use")
    routing_profile: str = Field(default="direct_llm", description="Routing profile")
    use_memory: bool = Field(default=True, description="Use conversation memory")
    use_tools: bool = Field(default=False, description="Enable tools")
    stream: bool = Field(default=False, description="Stream response")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class ResponseMetadata(BaseModel):
    """Standardized response metadata."""
    processing_time_ms: Optional[float] = None
    tokens_used: Optional[int] = None
    model_id: Optional[str] = None
    routing_profile: Optional[str] = None
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None
    error_code: Optional[str] = None
    suggestions: Optional[List[str]] = None


class SendMessageResponse(BaseModel):
    """Response model for sending a message."""
    conversation_id: str
    message_id: str
    answer: str
    metadata: ResponseMetadata
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


# Routing profile validation constants
VALID_ROUTING_PROFILES = {"direct_llm", "zain_agent", "tools_data"}
ROUTING_PROFILE_INFO = {
    "direct_llm": {
        "id": "direct_llm",
        "name": "Direct LLM",
        "description": "Direct connection to LLM server without additional processing"
    },
    "zain_agent": {
        "id": "zain_agent",
        "name": "Zain Agent",
        "description": "Route through Zain orchestrator agent with data access"
    },
    "tools_data": {
        "id": "tools_data",
        "name": "Tools + Data",
        "description": "Full orchestration with tools, data sources, and reasoning"
    }
}


def validate_routing_profile(profile_id: str) -> bool:
    """Validate that routing profile exists."""
    return profile_id in VALID_ROUTING_PROFILES


def get_routing_profile_suggestions() -> List[str]:
    """Get suggestions for routing profile validation errors."""
    return [
        f"Use one of: {', '.join(VALID_ROUTING_PROFILES)}",
        "Default value 'direct_llm' is used if not specified",
        "View available profiles with GET /api/chat/ui/profiles"
    ]


# Endpoints
@router.post("/send", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db)
) -> SendMessageResponse:
    """
    Send a message and get response.
    
    Validates routing profile before processing message.
    
    Args:
        request: Message request
        settings: Application settings
        db: Database session
        
    Returns:
        Message response with answer
    """
    try:
        # Validate routing profile
        if not validate_routing_profile(request.routing_profile):
            logger.warning(f"[Chat UI] Invalid routing profile: {request.routing_profile}")
            raise HTTPExceptionWithErrorCode(
                status_code=400,
                detail=f"Invalid routing profile: {request.routing_profile}",
                error_code=ErrorCode.VALIDATION_ERROR,
                suggestions=get_routing_profile_suggestions()
            )
        
        # Get or create conversation
        if request.conversation_id:
            conversation = db.query(Conversation).filter(
                Conversation.id == request.conversation_id,
                Conversation.is_deleted == False
            ).first()
            if not conversation:
                logger.error(f"[Chat UI] Conversation not found: {request.conversation_id}")
                raise HTTPExceptionWithErrorCode(
                    status_code=404,
                    detail="Conversation not found",
                    error_code=ErrorCode.CONVERSATION_NOT_FOUND
                )
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
            import time
            start_time = time.time()
            
            # Standardize model ID before routing
            standardized_model_id = None
            if request.model_id or conversation.model_id:
                try:
                    raw_model = request.model_id or conversation.model_id
                    standardized_model_id = ModelParser.standardize(raw_model, use_full=True)
                except Exception:
                    standardized_model_id = request.model_id or conversation.model_id

            result = await router_service.route_message(
                message=request.message,
                conversation_id=conversation.id,
                model_id=standardized_model_id,
                routing_profile=request.routing_profile,
                use_memory=request.use_memory,
                use_tools=request.use_tools,
                user_id=conversation.user_id,
                metadata=request.metadata
            )
            
            processing_time_ms = (time.time() - start_time) * 1000
            
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
            
            # Build standardized response metadata
            response_metadata = ResponseMetadata(
                processing_time_ms=processing_time_ms,
                tokens_used=result.get("tokens_used"),
                model_id=standardized_model_id,
                routing_profile=request.routing_profile,
                conversation_id=conversation.id,
                message_id=assistant_message.id
            )
            
            return SendMessageResponse(
                conversation_id=conversation.id,
                message_id=assistant_message.id,
                answer=result.get("answer", ""),
                metadata=response_metadata,
                error=result.get("error")
            )
            
        finally:
            await router_service.close()
            
    except HTTPExceptionWithErrorCode:
        raise
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
    
    Validates routing profile before streaming response.
    
    Args:
        request: Message request
        settings: Application settings
        db: Database session
        
    Returns:
        Streaming response
    """
    try:
        # Validate routing profile
        if not validate_routing_profile(request.routing_profile):
            logger.warning(f"[Chat UI] Invalid routing profile in stream: {request.routing_profile}")
            raise HTTPExceptionWithErrorCode(
                status_code=400,
                detail=f"Invalid routing profile: {request.routing_profile}",
                error_code=ErrorCode.VALIDATION_ERROR,
                suggestions=get_routing_profile_suggestions()
            )
        
        # Get or create conversation
        conversation_id = None
        user_id = "default"
        model_id_to_use = request.model_id
        
        if request.conversation_id:
            conversation = db.query(Conversation).filter(
                Conversation.id == request.conversation_id,
                Conversation.is_deleted == False
            ).first()
            if not conversation:
                logger.error(f"[Chat UI] Conversation not found in stream: {request.conversation_id}")
                raise HTTPExceptionWithErrorCode(
                    status_code=404,
                    detail="Conversation not found",
                    error_code=ErrorCode.CONVERSATION_NOT_FOUND
                )
            conversation_id = conversation.id
            user_id = conversation.user_id
            if not model_id_to_use:
                model_id_to_use = conversation.model_id
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
            conversation_id = conversation.id
            user_id = conversation.user_id
        
        # Store user message
        user_message = Message(
            conversation_id=conversation_id,
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
                # Standardize model ID before streaming
                standardized_model_id = None
                if model_id_to_use:
                    try:
                        standardized_model_id = ModelParser.standardize(model_id_to_use, use_full=True)
                    except Exception:
                        standardized_model_id = model_id_to_use

                # Stream tokens from router and emit SSE frames
                async for chunk in router_service.stream_message(
                    message=request.message,
                    conversation_id=conversation_id,
                    model_id=standardized_model_id,
                    connection_id=request.connection_id,
                    routing_profile=request.routing_profile,
                    use_memory=request.use_memory,
                    user_id=user_id,
                    metadata=request.metadata
                ):
                    # Normalize chunk to string
                    token = chunk if isinstance(chunk, str) else chunk.get("token") or chunk.get("data") or ""
                    if token:
                        yield f"data: {token}\n\n"
                
                # Final event to signal completion
                yield "event: done\n"
                yield f"data: {{\"conversation_id\": \"{conversation_id}\", \"model_id\": \"{standardized_model_id}\"}}\n\n"
            finally:
                await router_service.close()
        
        return StreamingResponse(generate(), media_type="text/event-stream")
        
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
        
        # Filter messages to exclude soft-deleted ones
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.is_deleted == False
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
        List of available models with detailed status information
    """
    try:
        # Try to fetch models from LLM server
        import httpx
        
        logger.info(f"[Chat UI] Fetching models from LLM server: {settings.llm_base_url}")
        
        # Check if LLM is configured; if not, try local Ollama fallback first
        if not settings.llm_base_url:
            logger.warning("[Chat UI] LLM base URL not configured; attempting local Ollama fallback")
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    local_url = "http://localhost:11434/api/tags"
                    logger.info(f"[Chat UI] Trying local Ollama at: {local_url}")
                    local_resp = await client.get(local_url)
                    if local_resp.status_code == 200:
                        data = local_resp.json()
                        models = data.get("models", [])
                        formatted_models = []
                        for m in models:
                            raw_name = m.get("name", m.get("model", "unknown"))
                            std = ModelParser.parse(f"{ModelProvider.OLLAMA.value}:{raw_name}")
                            formatted_models.append({
                                "id": std.full_id,
                                "name": std.short_id,
                                "provider": std.provider.value,
                                "size": m.get("size", 0),
                                "modified_at": m.get("modified_at", "")
                            })
                        if formatted_models:
                            logger.info(f"[Chat UI] Loaded {len(formatted_models)} model(s) from local Ollama")
                            return {
                                "success": True,
                                "models": formatted_models,
                                "default_model": formatted_models[0]["id"],
                                "source": "ollama-local",
                                "server_url": "http://localhost:11434",
                                "message": f"Loaded {len(formatted_models)} model(s) from local Ollama"
                            }
            except Exception as le:
                logger.info(f"[Chat UI] Local Ollama not detected: {le}")

            return {
                "success": False,
                "models": [],
                "default_model": None,
                "error": "not_configured",
                "message": "LLM server not configured. You can configure a server in Settings, or install and start Ollama locally to auto-detect models.",
                "config_url": "/llm-config"
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
                            return {
                                "success": False,
                                "models": [],
                                "default_model": None,
                                "error": "no_models",
                                "message": "Ollama server is running but no models are installed. Please pull a model using 'ollama pull <model-name>'.",
                                "server_url": settings.llm_base_url
                            }
                        
                        # Standardize model identifiers
                        formatted_models = []
                        for m in models:
                            raw_name = m.get("name", m.get("model", "unknown"))
                            std = ModelParser.parse(f"{ModelProvider.OLLAMA.value}:{raw_name}")
                            formatted_models.append({
                                "id": std.full_id,
                                "name": std.short_id,
                                "provider": std.provider.value,
                                "size": m.get("size", 0),
                                "modified_at": m.get("modified_at", "")
                            })
                        
                        logger.info(f"[Chat UI] Formatted {len(formatted_models)} models from Ollama")
                        
                        return {
                            "success": True,
                            "models": formatted_models,
                            "default_model": settings.llm_default_model or formatted_models[0]["id"],
                            "source": "ollama",
                            "server_url": settings.llm_base_url,
                            "message": f"Successfully loaded {len(formatted_models)} model(s) from Ollama"
                        }
                    else:
                        logger.error(f"[Chat UI] Ollama returned status {response.status_code}")
                        return {
                            "success": False,
                            "models": [],
                            "default_model": None,
                            "error": "server_error",
                            "message": f"Ollama server returned error (status {response.status_code}). Please check if Ollama is running.",
                            "server_url": settings.llm_base_url
                        }
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
                        
                        if not models:
                            return {
                                "success": False,
                                "models": [],
                                "default_model": None,
                                "error": "no_models",
                                "message": "LLM server is running but no models are available.",
                                "server_url": settings.llm_base_url
                            }
                        
                        # Standardize model identifiers from OpenAI-compatible response
                        formatted_models = []
                        for m in models:
                            raw_id = m.get("id") or m.get("name") or "unknown"
                            std = ModelParser.parse(f"{ModelProvider.OPENAI.value}:{raw_id}")
                            formatted_models.append({
                                "id": std.full_id,
                                "name": std.short_id,
                                "provider": std.provider.value,
                                "created": m.get("created"),
                                "object": m.get("object")
                            })
                        
                        return {
                            "success": True,
                            "models": formatted_models,
                            "default_model": settings.llm_default_model or (formatted_models[0].get("id") if formatted_models else None),
                            "source": "openai-compatible",
                            "server_url": settings.llm_base_url,
                            "message": f"Successfully loaded {len(formatted_models)} model(s) from LLM server"
                        }
                    else:
                        logger.error(f"[Chat UI] OpenAI endpoint returned status {response.status_code}")
                        return {
                            "success": False,
                            "models": [],
                            "default_model": None,
                            "error": "server_error",
                            "message": f"LLM server returned error (status {response.status_code}). Please check server configuration.",
                            "server_url": settings.llm_base_url
                        }
                        
            except httpx.ConnectError as e:
                logger.error(f"[Chat UI] Connection error to LLM server: {str(e)}")
                # Attempt local Ollama fallback for testing by default
                try:
                    local_url = "http://localhost:11434/api/tags"
                    logger.info(f"[Chat UI] Trying local Ollama fallback at: {local_url}")
                    local_resp = await client.get(local_url)
                    if local_resp.status_code == 200:
                        data = local_resp.json()
                        models = data.get("models", [])
                        formatted_models = []
                        for m in models:
                            raw_name = m.get("name", m.get("model", "unknown"))
                            std = ModelParser.parse(f"{ModelProvider.OLLAMA.value}:{raw_name}")
                            formatted_models.append({
                                "id": std.full_id,
                                "name": std.short_id,
                                "provider": std.provider.value,
                                "size": m.get("size", 0),
                                "modified_at": m.get("modified_at", "")
                            })
                        if formatted_models:
                            return {
                                "success": True,
                                "models": formatted_models,
                                "default_model": formatted_models[0]["id"],
                                "source": "ollama-local",
                                "server_url": "http://localhost:11434",
                                "message": f"Loaded {len(formatted_models)} model(s) from local Ollama fallback"
                            }
                except Exception as le:
                    logger.warning(f"[Chat UI] Local Ollama fallback failed: {le}")
                
                return {
                    "success": False,
                    "models": [],
                    "default_model": None,
                    "error": "connection_error",
                    "message": f"Cannot connect to LLM server at {settings.llm_base_url}. Please check if the server is running and the URL is correct.",
                    "server_url": settings.llm_base_url,
                    "config_url": "/llm-config"
                }
            except httpx.TimeoutException as e:
                logger.error(f"[Chat UI] Timeout connecting to LLM server: {str(e)}")
                return {
                    "success": False,
                    "models": [],
                    "default_model": None,
                    "error": "timeout",
                    "message": f"Connection to LLM server at {settings.llm_base_url} timed out. Please check if the server is responding.",
                    "server_url": settings.llm_base_url,
                    "config_url": "/llm-config"
                }
            except Exception as e:
                logger.error(f"[Chat UI] Error fetching models: {str(e)}", exc_info=True)
                return {
                    "success": False,
                    "models": [],
                    "default_model": None,
                    "error": "fetch_error",
                    "message": f"Error fetching models: {str(e)}",
                    "server_url": settings.llm_base_url
                }
        
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
                "source": "config",
                "warning": "Could not fetch models from server, using configured default"
            }
        
        # No models available
        return {
            "success": False,
            "models": [],
            "default_model": None,
            "error": "no_models",
            "message": "No models available. Please configure an LLM connection.",
            "config_url": "/llm-config"
        }
        
    except Exception as e:
        logger.error(f"[Chat UI] Error listing models: {str(e)}", exc_info=True)
        return {
            "success": False,
            "models": [],
            "default_model": None,
            "error": "unexpected_error",
            "message": f"Unexpected error: {str(e)}",
            "config_url": "/llm-config"
        }


@router.get("/profiles")
async def list_routing_profiles() -> Dict[str, Any]:
    """
    List available routing profiles.
    
    Returns information about all valid routing profiles that can be used for message routing.
    
    Returns:
        List of routing profiles with metadata
    """
    profiles = [ROUTING_PROFILE_INFO[profile_id] for profile_id in VALID_ROUTING_PROFILES]
    
    return {
        "profiles": profiles,
        "default": "direct_llm",
        "count": len(profiles)
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
