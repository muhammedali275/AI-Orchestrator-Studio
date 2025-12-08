"""
LLM Client for AIpanel.

Generic client for calling external LLM providers.
"""

import logging
import time
import json
from typing import List, Dict, Any, Optional, Union

import httpx
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db.models import LLMConnection
from ..db.session import get_db

logger = logging.getLogger(__name__)
settings = get_settings()


class LLMClient:
    """
    Generic LLM client for calling external LLM providers.
    
    Supports OpenAI-compatible endpoints, Ollama, and other providers.
    """
    
    def __init__(
        self,
        connection_id: Optional[str] = None,
        connection_config: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None
    ):
        """
        Initialize LLM client.
        
        Args:
            connection_id: ID of LLM connection in database
            connection_config: Direct connection configuration (overrides connection_id)
            db: Database session
        """
        self.connection_id = connection_id
        self.connection_config = connection_config
        self.db = db
        
        # Default configuration
        self.base_url = settings.LLM_BASE_URL
        self.api_key = settings.LLM_API_KEY
        self.default_model = settings.LLM_DEFAULT_MODEL
        self.timeout = settings.LLM_TIMEOUT_SECONDS
        self.max_retries = settings.LLM_MAX_RETRIES
        
        # HTTP client (lazy initialization)
        self._client = None
    
    async def _load_connection_config(self) -> None:
        """
        Load connection configuration from database.
        
        Raises:
            ValueError: If connection not found
        """
        if not self.connection_id:
            return
        
        if not self.db:
            # Create a new session if not provided
            async for db_session in get_db():
                self.db = db_session
                break
        
        connection = self.db.query(LLMConnection).filter(
            LLMConnection.id == self.connection_id
        ).first()
        
        if not connection:
            raise ValueError(f"LLM connection not found: {self.connection_id}")
        
        # Update configuration
        self.connection_config = connection.to_dict()
        self.base_url = connection.base_url or self.base_url
        self.api_key = connection.api_key or self.api_key
        self.default_model = connection.default_model or self.default_model
        
        # Additional configuration
        if connection.config:
            if "timeout" in connection.config:
                self.timeout = connection.config["timeout"]
            if "max_retries" in connection.config:
                self.max_retries = connection.config["max_retries"]
    
    async def _get_client(self) -> httpx.AsyncClient:
        """
        Get or create HTTP client.
        
        Returns:
            HTTP client
        """
        if self._client is None:
            # Load connection configuration if needed
            if self.connection_id and not self.connection_config:
                await self._load_connection_config()
            
            # Override with direct configuration if provided
            if self.connection_config:
                self.base_url = self.connection_config.get("base_url") or self.base_url
                self.api_key = self.connection_config.get("api_key") or self.api_key
                self.default_model = self.connection_config.get("default_model") or self.default_model
                self.timeout = self.connection_config.get("timeout") or self.timeout
                self.max_retries = self.connection_config.get("max_retries") or self.max_retries
            
            # Create HTTP client
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers=self._get_headers()
            )
        
        return self._client
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers for LLM request.
        
        Returns:
            HTTP headers
        """
        headers = {
            "Content-Type": "application/json",
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        return headers
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools_config: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call LLM chat completion API.
        
        Args:
            messages: List of messages with role and content
            model: Model name (uses default if not provided)
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            tools_config: Tool configuration for function calling
            **kwargs: Additional model-specific parameters
            
        Returns:
            LLM response
            
        Raises:
            ValueError: If configuration is invalid
            httpx.HTTPError: If HTTP request fails
        """
        if not self.base_url:
            raise ValueError("LLM base URL not configured")
        
        model = model or self.default_model
        if not model:
            raise ValueError("No LLM model specified and no default configured")
        
        temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE
        max_tokens = max_tokens or settings.LLM_MAX_TOKENS
        
        client = await self._get_client()
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"[LLM] Attempt {attempt + 1}/{self.max_retries} with model {model}")
                
                # Prepare payload
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                }
                
                if max_tokens:
                    payload["max_tokens"] = max_tokens
                
                # Add tools configuration if provided
                if tools_config:
                    payload["tools"] = tools_config.get("tools", [])
                    if "tool_choice" in tools_config:
                        payload["tool_choice"] = tools_config["tool_choice"]
                
                # Add any additional kwargs
                payload.update(kwargs)
                
                # Determine the correct endpoint
                endpoint = self._get_chat_endpoint()
                
                # Make request
                response = await client.post(
                    endpoint,
                    json=payload
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"[LLM] Success with model {model}")
                
                return {
                    "response": result,
                    "model_used": model,
                    "attempts": attempt + 1,
                    "success": True
                }
                
            except httpx.HTTPStatusError as e:
                last_error = e
                error_msg = str(e).lower()
                
                # Check if error is retryable
                if self._is_retryable_error(error_msg, e.response.status_code):
                    if attempt < self.max_retries - 1:
                        backoff_time = 2 ** attempt
                        logger.warning(
                            f"[LLM] Retryable error: {error_msg}. "
                            f"Retrying in {backoff_time}s (attempt {attempt + 1}/{self.max_retries})"
                        )
                        time.sleep(backoff_time)
                        continue
                    else:
                        logger.error(f"[LLM] Max retries exceeded. Final error: {error_msg}")
                else:
                    logger.error(f"[LLM] Non-retryable error: {error_msg}")
                    break
                    
            except httpx.TimeoutException as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    backoff_time = 2 ** attempt
                    logger.warning(
                        f"[LLM] Timeout. Retrying in {backoff_time}s "
                        f"(attempt {attempt + 1}/{self.max_retries})"
                    )
                    time.sleep(backoff_time)
                    continue
                else:
                    logger.error(f"[LLM] Max retries exceeded due to timeout")
                    
            except Exception as e:
                last_error = e
                logger.error(f"[LLM] Unexpected error: {str(e)}")
                break
        
        # All retries exhausted
        raise last_error or ValueError("LLM call failed after all retries")
    
    def _get_chat_endpoint(self) -> str:
        """
        Get chat endpoint URL based on provider.
        
        Returns:
            Chat endpoint URL
        """
        base_url = self.base_url.rstrip("/")
        
        # Ollama uses a different endpoint
        if "11434" in base_url or "ollama" in base_url.lower():
            return f"{base_url}/api/chat"
        
        # OpenAI-compatible endpoint
        if not base_url.endswith("/v1"):
            return f"{base_url}/v1/chat/completions"
        
        return f"{base_url}/chat/completions"
    
    def _is_retryable_error(self, error_msg: str, status_code: int) -> bool:
        """
        Determine if an error is retryable.
        
        Args:
            error_msg: Error message
            status_code: HTTP status code
            
        Returns:
            True if error is retryable, False otherwise
        """
        retryable_status_codes = {429, 500, 502, 503, 504}
        
        if status_code in retryable_status_codes:
            return True
        
        retryable_patterns = [
            "overloaded",
            "rate limit",
            "timeout",
            "connection",
            "server error",
        ]
        
        return any(pattern in error_msg for pattern in retryable_patterns)
    
    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """
        Stream LLM chat completion API.
        
        Args:
            messages: List of messages with role and content
            model: Model name (uses default if not provided)
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            **kwargs: Additional model-specific parameters
            
        Yields:
            Streaming response chunks
            
        Raises:
            ValueError: If configuration is invalid
            httpx.HTTPError: If HTTP request fails
        """
        if not self.base_url:
            raise ValueError("LLM base URL not configured")
        
        model = model or self.default_model
        if not model:
            raise ValueError("No LLM model specified and no default configured")
        
        temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE
        max_tokens = max_tokens or settings.LLM_MAX_TOKENS
        
        client = await self._get_client()
        
        # Prepare payload
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        # Add any additional kwargs
        payload.update(kwargs)
        
        # Determine the correct endpoint
        endpoint = self._get_chat_endpoint()
        
        # Make streaming request
        async with client.stream(
            "POST",
            endpoint,
            json=payload
        ) as response:
            response.raise_for_status()
            async for chunk in response.aiter_text():
                if chunk.strip():
                    # Handle different streaming formats
                    if chunk.startswith("data:"):
                        # SSE format (OpenAI)
                        chunk = chunk.replace("data:", "").strip()
                        if chunk == "[DONE]":
                            break
                    
                    try:
                        yield json.loads(chunk)
                    except json.JSONDecodeError:
                        # If not valid JSON, yield raw chunk
                        yield {"text": chunk}
    
    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


async def get_llm_client(
    connection_id: Optional[str] = None,
    db: Session = None
) -> LLMClient:
    """
    Get LLM client.
    
    Args:
        connection_id: ID of LLM connection in database
        db: Database session
        
    Returns:
        LLM client
    """
    return LLMClient(connection_id=connection_id, db=db)
