"""
LLM API - Endpoints for LLM configuration and testing.

Provides CRUD operations for LLM settings and connectivity testing.
"""

import logging
from urllib.parse import urlsplit, urlunsplit
import httpx
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Tuple

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
        # Normalize base URL (strip paths like /api/chat, drop trailing slash)
        def normalize_base_url(raw_url: Optional[str]) -> Optional[str]:
            if not raw_url:
                return raw_url
            raw_url = raw_url.strip()
            parts = urlsplit(raw_url)
            if not parts.scheme or not parts.netloc:
                raise HTTPException(status_code=400, detail="Base URL must include scheme and host, e.g., http://10.99.70.200:4000")
            # Keep only scheme + host:port
            return urlunsplit((parts.scheme, parts.netloc, '', '', ''))

        async def probe_models(base_url: str, api_key: Optional[str], timeout_seconds: int) -> Tuple[bool, Optional[List[Dict[str, str]]], str]:
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            async with httpx.AsyncClient(timeout=timeout_seconds, headers=headers) as client:
                # Try Ollama /api/tags
                try:
                    resp = await client.get(f"{base_url}/api/tags")
                    if resp.status_code == 200:
                        data = resp.json()
                        models = data.get("models", [])
                        model_list = [{"id": m.get("name"), "name": m.get("name")} for m in models if m.get("name")]
                        if model_list:
                            return True, model_list, "ollama"
                except Exception:
                    pass
                # Try OpenAI-style /v1/models
                try:
                    resp = await client.get(f"{base_url}/v1/models")
                    if resp.status_code == 200:
                        data = resp.json()
                        models = data.get("data", [])
                        model_list = []
                        for m in models:
                            mid = m.get("id") or m.get("name")
                            if mid:
                                model_list.append({"id": mid, "name": mid})
                        if model_list:
                            return True, model_list, "openai"
                except Exception:
                    pass
            return False, None, ""

        normalized_base = normalize_base_url(config.base_url)

        # Probe connectivity before persisting
        if normalized_base:
            ok, models_found, provider = await probe_models(normalized_base, config.api_key, config.timeout_seconds or 10)
            
            # If primary fails, try fallback ports: 9000, 4000, 8000, 3000
            if not ok:
                fallback_ports = [9000, 4000, 8000, 3000]
                parts = urlsplit(normalized_base)
                host = parts.hostname or parts.netloc.split(':')[0]
                scheme = parts.scheme or "http"
                
                for port in fallback_ports:
                    fallback_url = f"{scheme}://{host}:{port}"
                    ok, models_found, provider = await probe_models(fallback_url, config.api_key, config.timeout_seconds or 10)
                    if ok:
                        normalized_base = fallback_url
                        logger.info(f"[LLM API] Auto-detected working URL: {fallback_url}")
                        break
            
            # If still not ok, raise error
            if not ok:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Cannot reach LLM server at {config.base_url}. "
                        "Tried fallback ports 9000, 4000, 8000, 3000 as well. "
                        "Ensure the host is reachable and use format: http://host:port (no paths like /api/chat)"
                    )
                )
            
            # Auto-select default model if missing
            if not config.default_model and models_found:
                config.default_model = models_found[0]["id"]

        # Update settings
        if normalized_base is not None:
            settings.llm_base_url = normalized_base
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
        
        # Persist to .env file
        try:
            import os
            env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
            
            # Read current .env file
            env_content = ""
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    env_content = f.read()
            
            # Update or add environment variables
            lines = env_content.split('\n')
            updated_lines = []
            keys_updated = set()
            
            for line in lines:
                if line.startswith('LLM_BASE_URL='):
                    updated_lines.append(f'LLM_BASE_URL={normalized_base}')
                    keys_updated.add('LLM_BASE_URL')
                elif line.startswith('LLM_DEFAULT_MODEL='):
                    updated_lines.append(f'LLM_DEFAULT_MODEL={config.default_model}')
                    keys_updated.add('LLM_DEFAULT_MODEL')
                elif line.startswith('LLM_API_KEY='):
                    if config.api_key:
                        updated_lines.append(f'LLM_API_KEY={config.api_key}')
                    keys_updated.add('LLM_API_KEY')
                elif line.startswith('LLM_TIMEOUT_SECONDS='):
                    updated_lines.append(f'LLM_TIMEOUT_SECONDS={config.timeout_seconds}')
                    keys_updated.add('LLM_TIMEOUT_SECONDS')
                elif line.startswith('LLM_TEMPERATURE='):
                    updated_lines.append(f'LLM_TEMPERATURE={config.temperature}')
                    keys_updated.add('LLM_TEMPERATURE')
                elif line.startswith('LLM_MAX_TOKENS='):
                    updated_lines.append(f'LLM_MAX_TOKENS={config.max_tokens}')
                    keys_updated.add('LLM_MAX_TOKENS')
                else:
                    updated_lines.append(line)
            
            # Add missing keys
            if 'LLM_BASE_URL' not in keys_updated and normalized_base:
                updated_lines.append(f'LLM_BASE_URL={normalized_base}')
            if 'LLM_DEFAULT_MODEL' not in keys_updated and config.default_model:
                updated_lines.append(f'LLM_DEFAULT_MODEL={config.default_model}')
            
            # Write back to .env
            with open(env_path, 'w') as f:
                f.write('\n'.join(updated_lines))
            
            logger.info("[LLM API] Configuration persisted to .env file")
        except Exception as e:
            logger.warning(f"[LLM API] Could not persist to .env file: {str(e)}")
        
        # Clear cache to reload settings
        clear_settings_cache()
        
        logger.info("[LLM API] Configuration updated successfully")
        
        return {
            "success": True,
            "message": "LLM configuration updated successfully",
            "config": config.dict()
        }
        
    except HTTPException:
        raise
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


@router.get("/auth-requirements")
async def get_auth_requirements(settings: Settings = Depends(get_settings)) -> Dict[str, Any]:
    """
    Get authentication requirements for the configured LLM provider.
    
    Returns:
        Authentication requirements and recommendations
    """
    if not settings.llm_base_url:
        return {
            "requires_auth": False,
            "provider": "none",
            "message": "LLM base URL not configured"
        }
    
    try:
        async with LLMClient(settings) as client:
            is_valid, message = client.validate_authentication()
            
            return {
                "requires_auth": client.requires_auth,
                "provider": client.provider.value,
                "auth_type": client.auth_type.value,
                "has_api_key": bool(settings.llm_api_key),
                "is_valid": is_valid,
                "message": message,
                "recommendations": _get_auth_recommendations(client.provider.value, client.requires_auth, bool(settings.llm_api_key))
            }
    except Exception as e:
        logger.error(f"[LLM API] Error checking auth requirements: {str(e)}")
        return {
            "requires_auth": False,
            "provider": "unknown",
            "error": str(e)
        }


@router.post("/validate-auth")
async def validate_authentication(settings: Settings = Depends(get_settings)) -> Dict[str, Any]:
    """
    Validate authentication configuration.
    
    Returns:
        Validation result with detailed feedback
    """
    if not settings.llm_base_url:
        return {
            "valid": False,
            "message": "LLM base URL not configured"
        }
    
    try:
        async with LLMClient(settings) as client:
            is_valid, message = client.validate_authentication()
            
            # Try a simple test request if validation passes
            test_result = None
            if is_valid and settings.llm_api_key:
                try:
                    test_messages = [{"role": "user", "content": "test"}]
                    result = await client.call(messages=test_messages)
                    test_result = {
                        "success": True,
                        "message": "Authentication test successful"
                    }
                except Exception as e:
                    error_str = str(e)
                    # Check for authentication-related errors
                    if any(keyword in error_str.lower() for keyword in ["unauthorized", "401", "403", "invalid api key", "authentication"]):
                        test_result = {
                            "success": False,
                            "message": "Authentication failed - API key may be invalid",
                            "error": error_str
                        }
                    else:
                        test_result = {
                            "success": False,
                            "message": "Test request failed (not auth-related)",
                            "error": error_str
                        }
            
            return {
                "valid": is_valid,
                "message": message,
                "provider": client.provider.value,
                "auth_type": client.auth_type.value,
                "requires_auth": client.requires_auth,
                "test_result": test_result
            }
            
    except Exception as e:
        logger.error(f"[LLM API] Error validating authentication: {str(e)}")
        return {
            "valid": False,
            "message": f"Validation error: {str(e)}"
        }


def _get_auth_recommendations(provider: str, requires_auth: bool, has_api_key: bool) -> List[str]:
    """
    Get authentication recommendations based on provider and configuration.
    
    Args:
        provider: Provider name
        requires_auth: Whether authentication is required
        has_api_key: Whether API key is configured
        
    Returns:
        List of recommendation strings
    """
    recommendations = []
    
    # Cloud provider recommendations
    if provider in ["openai", "anthropic", "cohere", "azure", "huggingface"]:
        if not has_api_key:
            recommendations.append(f"⚠️ CRITICAL: {provider.upper()} requires an API key for production use")
            recommendations.append(f"📝 Obtain an API key from {provider.upper()} dashboard")
            recommendations.append("🔒 Store API key securely using credential management")
        else:
            recommendations.append(f"✅ API key configured for {provider.upper()}")
            recommendations.append("🔒 Ensure API key is kept secure and not exposed in logs")
            
        if provider == "openai":
            recommendations.append("💡 OpenAI API keys start with 'sk-'")
            recommendations.append("📊 Monitor usage at https://platform.openai.com/usage")
        elif provider == "anthropic":
            recommendations.append("💡 Anthropic API keys start with 'sk-ant-'")
            recommendations.append("📊 Monitor usage at https://console.anthropic.com")
        elif provider == "azure":
            recommendations.append("💡 Azure OpenAI uses endpoint-specific keys")
            recommendations.append("🔧 Configure both endpoint and API key")
    
    # On-premise recommendations
    elif provider in ["ollama", "llamacpp"]:
        if "localhost" in provider or "127.0.0.1" in provider:
            recommendations.append("✅ Local server detected - authentication optional")
        else:
            if not has_api_key:
                recommendations.append("⚠️ WARNING: Remote server without authentication")
                recommendations.append("🔒 Consider adding authentication for production")
            else:
                recommendations.append("✅ Authentication configured for remote server")
    
    elif provider in ["vllm", "textgen_webui", "custom"]:
        if not has_api_key and requires_auth:
            recommendations.append("⚠️ WARNING: Authentication recommended for production")
            recommendations.append("🔒 Configure API key or token for secure access")
            recommendations.append("🛡️ Use reverse proxy with authentication if needed")
        elif has_api_key:
            recommendations.append("✅ Authentication configured")
    
    # General recommendations
    if has_api_key:
        recommendations.append("🔄 Test authentication before deploying to production")
        recommendations.append("📝 Document API key rotation procedures")
    
    return recommendations
