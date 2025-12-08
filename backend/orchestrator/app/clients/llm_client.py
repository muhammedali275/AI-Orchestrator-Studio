"""
LLM Client - Generic interface for LLM interactions.

Uses Settings for configuration - no hard-coded endpoints.
"""

import logging
import time
from typing import List, Dict, Any, Optional
import httpx
from ..config import Settings

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Generic LLM client that uses configuration from Settings.
    
    Supports retry logic, fallback models, and timeout handling.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize LLM client with settings.
        
        Args:
            settings: Application settings containing LLM configuration
        """
        self.settings = settings
        self.base_url = settings.llm_base_url
        self.default_model = settings.llm_default_model
        self.timeout = settings.llm_timeout_seconds
        self.max_retries = settings.llm_max_retries
        self.api_key = settings.llm_api_key
        
        # HTTP client for making requests
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            headers=self._get_headers()
        )
    
    def _get_headers(self) -> Dict[str, str]:
        """Build request headers."""
        headers = {
            "Content-Type": "application/json",
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        return headers
    
    async def call(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call LLM with retry logic.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (uses default if not provided)
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            **kwargs: Additional model-specific parameters
            
        Returns:
            Dict containing response and metadata
            
        Raises:
            Exception: If all retries fail
        """
        if not self.base_url:
            raise ValueError("LLM base URL not configured in settings")
        
        model = model or self.default_model
        if not model:
            raise ValueError("No LLM model specified and no default configured")
        
        temperature = temperature if temperature is not None else self.settings.llm_temperature
        max_tokens = max_tokens or self.settings.llm_max_tokens
        
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"[LLM] Attempt {attempt + 1}/{self.max_retries} with model {model}")
                
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                }
                
                if max_tokens:
                    payload["max_tokens"] = max_tokens
                
                # Add any additional kwargs
                payload.update(kwargs)
                
                # Determine the correct endpoint based on the base URL
                # Ollama uses /api/chat for chat completions (supports messages format)
                # OpenAI-compatible uses /chat/completions or /v1/chat/completions
                if self._is_ollama_endpoint():
                    # Ollama endpoint - use /api/chat which supports messages
                    endpoint = f"{self.base_url}/api/chat"
                    payload = {
                        "model": model,
                        "messages": messages,  # Ollama /api/chat supports messages format
                        "temperature": temperature,
                        "stream": False
                    }
                    if max_tokens:
                        payload["options"] = {"num_predict": max_tokens}
                else:
                    # OpenAI-compatible endpoint
                    endpoint = f"{self.base_url}/chat/completions"
                
                response = await self.client.post(
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
                error_detail = {
                    "status_code": e.response.status_code,
                    "url": str(e.request.url),
                    "method": e.request.method,
                    "response": e.response.text[:200]  # First 200 chars
                }
                
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
                        logger.error(f"[LLM] Max retries exceeded. Error details: {error_detail}")
                else:
                    logger.error(f"[LLM] Non-retryable error. Details: {error_detail}")
                    break
            
            except httpx.ConnectError as e:
                last_error = e
                logger.error(f"[LLM] Connection error: {str(e)}. Check if server is running at {self.base_url}")
                if attempt < self.max_retries - 1:
                    backoff_time = 2 ** attempt
                    logger.warning(f"[LLM] Retrying in {backoff_time}s (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(backoff_time)
                    continue
                else:
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
        raise last_error or Exception("LLM call failed after all retries")
    
    def _is_ollama_endpoint(self) -> bool:
        """Detect if endpoint is Ollama-based."""
        ollama_indicators = [
            "11434" in self.base_url,
            "ollama" in self.base_url.lower(),
            "/api/generate" in self.base_url,
            "/api/chat" in self.base_url,
            ":11434" in self.base_url
        ]
        return any(ollama_indicators)
    
    def _is_retryable_error(self, error_msg: str, status_code: int) -> bool:
        """Determine if an error is retryable."""
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
    
    async def validate_connection(self) -> Dict[str, Any]:
        """
        Validate LLM connection before use.
        
        Returns:
            Dict with validation results
        """
        try:
            # Try to get version info
            response = await self.client.get(f"{self.base_url}/api/version")
            version_info = response.json()
            
            return {
                "valid": True,
                "version": version_info.get("version", "unknown"),
                "message": "Connection successful"
            }
        except httpx.HTTPStatusError as e:
            return {
                "valid": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text[:200]}",
                "message": "Server returned an error"
            }
        except httpx.ConnectError as e:
            return {
                "valid": False,
                "error": f"Connection failed: {str(e)}",
                "message": "Cannot connect to server. Check if server is running and URL is correct."
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "message": "Unexpected error during validation"
            }
    
    async def stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """
        Stream LLM response.
        
        Args:
            messages: List of message dicts
            model: Model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            **kwargs: Additional parameters
            
        Yields:
            Response chunks
        """
        if not self.base_url:
            raise ValueError("LLM base URL not configured in settings")
        
        model = model or self.default_model
        if not model:
            raise ValueError("No LLM model specified")
        
        temperature = temperature if temperature is not None else self.settings.llm_temperature
        max_tokens = max_tokens or self.settings.llm_max_tokens
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        payload.update(kwargs)
        
        # Determine the correct endpoint for streaming
        if self._is_ollama_endpoint():
            # Ollama streaming - use /api/chat with stream=true
            endpoint = f"{self.base_url}/api/chat"
            payload = {
                "model": model,
                "messages": messages,  # Ollama /api/chat supports messages
                "temperature": temperature,
                "stream": True
            }
            if max_tokens:
                payload["options"] = {"num_predict": max_tokens}
        else:
            # OpenAI-compatible streaming
            endpoint = f"{self.base_url}/chat/completions"
        
        async with self.client.stream(
            "POST",
            endpoint,
            json=payload
        ) as response:
            response.raise_for_status()
            async for chunk in response.aiter_text():
                if chunk.strip():
                    yield chunk
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
