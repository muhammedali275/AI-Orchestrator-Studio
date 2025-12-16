"""
Frontend Configuration API - Exposes system configuration for frontend consumption.

Provides endpoints for frontend to read configuration values that need to be
synchronized between backend and frontend (e.g., timeouts).
"""

import logging
from fastapi import APIRouter, Depends
from typing import Dict, Any
from pydantic import BaseModel

from ..config import get_settings, Settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/config", tags=["config"])


class FrontendConfigResponse(BaseModel):
    """Frontend configuration model."""
    backend_api_url: str
    llm_timeout_seconds: int
    request_timeout_seconds: int
    streaming_enabled: bool
    max_message_length: int
    features: Dict[str, bool]


@router.get("/frontend", response_model=FrontendConfigResponse)
async def get_frontend_config(settings: Settings = Depends(get_settings)) -> FrontendConfigResponse:
    """
    Get configuration for frontend consumption.
    
    Frontend should call this endpoint on startup and use the returned values
    for request timeouts, feature flags, etc. This ensures frontend and backend
    timeouts are always synchronized.
    
    Returns:
        Frontend configuration with timeout and feature flags
    """
    return FrontendConfigResponse(
        backend_api_url=f"http://localhost:{settings.api_port}",
        llm_timeout_seconds=settings.llm_timeout_seconds,
        request_timeout_seconds=settings.llm_timeout_seconds + 10,  # Add buffer for backend processing
        streaming_enabled=False,  # TODO: Enable after implementing streaming
        max_message_length=4000,
        features={
            "streaming": False,  # Server-sent events for streaming responses
            "memory_management": True,  # Conversation memory endpoints
            "tool_execution": True,  # Tool execution and debugging
            "execution_debugging": True,  # Show execution steps
            "conversation_export": False,  # TODO: Export conversations
            "prompt_templates": True,  # Saved prompt templates
            "routing_profiles": True,  # Multiple routing options
        }
    )


@router.get("/timeout")
async def get_timeout_config(settings: Settings = Depends(get_settings)) -> Dict[str, int]:
    """
    Get timeout configuration.
    
    Frontend should use these values for axios timeouts to ensure
    frontend and backend timeouts are synchronized.
    
    Returns:
        Timeout configuration in milliseconds
    """
    llm_timeout_ms = settings.llm_timeout_seconds * 1000
    return {
        "llm_timeout_ms": llm_timeout_ms,
        "llm_timeout_seconds": settings.llm_timeout_seconds,
        "frontend_timeout_ms": llm_timeout_ms + 5000,  # 5s buffer for network latency
        "message: _comment": "Frontend should use frontend_timeout_ms for axios calls"
    }


@router.get("/status")
async def get_system_status(settings: Settings = Depends(get_settings)) -> Dict[str, Any]:
    """
    Get system status including LLM configuration status.
    
    Returns:
        System status information
    """
    return {
        "status": "operational",
        "llm_configured": bool(settings.llm_base_url),
        "llm_server": settings.llm_base_url,
        "llm_default_model": settings.llm_default_model,
        "llm_timeout_seconds": settings.llm_timeout_seconds,
        "backend_port": settings.api_port,
        "frontend_endpoints_available": [
            "/api/config/frontend",
            "/api/config/timeout",
            "/api/config/status",
        ]
    }
