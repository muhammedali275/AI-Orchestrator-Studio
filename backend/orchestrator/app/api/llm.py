"""
LLM API - Endpoints for LLM configuration and testing.

Provides CRUD operations for LLM settings and connectivity testing.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from ..config import get_settings, Settings, clear_settings_cache
from ..clients.llm_client import LLMClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/llm", tags=["llm"])


class LLMConfigModel(BaseModel):
    """LLM configuration model."""
    base_url: Optional[str] = Field(None, description="LLM server base URL")
    default_model: Optional[str] = Field(None, description="Default model name")
    api_key: Optional[str] = Field(None, description="API key")
    timeout_seconds: int = Field(default=60, description="Request timeout")
    max_retries: int = Field(default=3, description="Maximum retries")
    temperature: float = Field(default=0.7, description="Default temperature")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens")


class LLMTestRequest(BaseModel):
    """LLM test request model."""
    prompt: str = Field(default="Hello, how are you?", description="Test prompt")
    model: Optional[str] = Field(None, description="Model to test (uses default if not provided)")


class LLMTestResponse(BaseModel):
    """LLM test response model."""
    success: bool
    message: str
    response: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    response_time_ms: Optional[float] = None


@router.get("/config", response_model=LLMConfigModel)
async def get_llm_config(settings: Settings = Depends(get_settings)) -> LLMConfigModel:
    """
    Get current LLM configuration.
    
    Returns:
        Current LLM configuration
    """
    return LLMConfigModel(
        base_url=settings.llm_base_url,
        default_model=settings.llm_default_model,
        api_key=settings.llm_api_key,
        timeout_seconds=settings.llm_timeout_seconds,
        max_retries=settings.llm_max_retries,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens
    )


@router.put("/config")
async def update_llm_config(
    config: LLMConfigModel,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Update LLM configuration.
    
    Args:
        config: New LLM configuration
        
    Returns:
        Success message and updated configuration
    """
    try:
        # Update settings
        if config.base_url is not None:
            settings.llm_base_url = config.base_url
        if config.default_model is not None:
            settings.llm_default_model = config.default_model
        if config.api_key is not None:
            settings.llm_api_key = config.api_key
        if config.timeout_seconds is not None:
            settings.llm_timeout_seconds = config.timeout_seconds
        if config.max_retries is not None:
            settings.llm_max_retries = config.max_retries
        if config.temperature is not None:
            settings.llm_temperature = config.temperature
        if config.max_tokens is not None:
            settings.llm_max_tokens = config.max_tokens
        
        # Clear cache to reload settings
        clear_settings_cache()
        
        logger.info("[LLM API] Configuration updated successfully")
        
        return {
            "success": True,
            "message": "LLM configuration updated successfully",
            "config": config.dict()
        }
        
    except Exception as e:
        logger.error(f"[LLM API] Error updating configuration: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update LLM configuration: {str(e)}"
        )


@router.post("/test", response_model=LLMTestResponse)
async def test_llm_connection(
    request: LLMTestRequest,
    settings: Settings = Depends(get_settings)
) -> LLMTestResponse:
    """
    Test LLM connectivity and functionality.
    
    Args:
        request: Test request with prompt and optional model
        
    Returns:
        Test result with success status and response
    """
    if not settings.llm_base_url:
        return LLMTestResponse(
            success=False,
            message="LLM base URL not configured",
            error="LLM base URL is required"
        )
    
    if not settings.llm_default_model and not request.model:
        return LLMTestResponse(
            success=False,
            message="No LLM model specified",
            error="Either configure a default model or specify one in the request"
        )
    
    try:
        import time
        start_time = time.time()
        
        # Create LLM client and test
        async with LLMClient(settings) as client:
            messages = [
                {"role": "user", "content": request.prompt}
            ]
            
            result = await client.call(
                messages=messages,
                model=request.model
            )
            
            response_time = (time.time() - start_time) * 1000
            
            logger.info(f"[LLM API] Test successful in {response_time:.2f}ms")
            
            return LLMTestResponse(
                success=True,
                message="LLM connection successful",
                response=result,
                response_time_ms=response_time
            )
            
    except Exception as e:
        logger.error(f"[LLM API] Test failed: {str(e)}")
        return LLMTestResponse(
            success=False,
            message="LLM connection failed",
            error=str(e)
        )


@router.get("/models")
async def list_models(settings: Settings = Depends(get_settings)) -> Dict[str, Any]:
    """
    List available LLM models.
    
    Returns:
        List of available models (if supported by the LLM provider)
    """
    if not settings.llm_base_url:
        raise HTTPException(
            status_code=400,
            detail="LLM base URL not configured"
        )
    
    try:
        # Try to fetch models from the LLM provider
        import httpx
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Try Ollama API first (/api/tags)
            try:
                response = await client.get(f"{settings.llm_base_url}/api/tags")
                
                if response.status_code == 200:
                    data = response.json()
                    models = data.get("models", [])
                    # Extract model names from Ollama format
                    model_list = [{"id": m["name"], "name": m["name"]} for m in models]
                    return {
                        "success": True,
                        "models": model_list,
                        "default_model": settings.llm_default_model
                    }
            except:
                pass
            
            # Try OpenAI-compatible API (/v1/models)
            try:
                response = await client.get(f"{settings.llm_base_url}/v1/models")
                
                if response.status_code == 200:
                    models = response.json()
                    return {
                        "success": True,
                        "models": models.get("data", []) if isinstance(models, dict) else models,
                        "default_model": settings.llm_default_model
                    }
            except:
                pass
            
            # Fallback to default model
            return {
                "success": True,
                "models": [{"id": settings.llm_default_model, "name": settings.llm_default_model}] if settings.llm_default_model else [],
                "default_model": settings.llm_default_model,
                "message": "Using configured default model"
            }
                
    except Exception as e:
        logger.warning(f"[LLM API] Could not fetch models: {str(e)}")
        return {
            "success": True,
            "models": [{"id": settings.llm_default_model, "name": settings.llm_default_model}] if settings.llm_default_model else [],
            "default_model": settings.llm_default_model,
            "message": "Using configured default model"
        }


@router.get("/health")
async def llm_health(settings: Settings = Depends(get_settings)) -> Dict[str, Any]:
    """
    Check LLM service health.
    
    Returns:
        Health status
    """
    if not settings.llm_base_url:
        return {
            "healthy": False,
            "message": "LLM not configured"
        }
    
    try:
        import httpx
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.llm_base_url}/health")
            
            return {
                "healthy": response.status_code == 200,
                "status_code": response.status_code,
                "base_url": settings.llm_base_url,
                "default_model": settings.llm_default_model
            }
            
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e),
            "base_url": settings.llm_base_url
        }
