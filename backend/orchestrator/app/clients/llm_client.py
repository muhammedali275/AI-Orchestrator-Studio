"""
LLM Client - Generic interface for LLM interactions.

Uses Settings for configuration - no hard-coded endpoints.
Supports authentication for both cloud and on-premise LLM servers.
"""

import json
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import httpx
from ..config import Settings

logger = logging.getLogger(__name__)


class AuthType(Enum):
    """Authentication types supported."""
    NONE = "none"
    BEARER = "bearer"
    API_KEY = "api_key"
    BASIC = "basic"
    CUSTOM = "custom"


class LLMProvider(Enum):
    """Known LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE = "azure"
    COHERE = "cohere"
    HUGGINGFACE = "huggingface"
    OLLAMA = "ollama"
    VLLM = "vllm"
    TEXTGEN_WEBUI = "textgen_webui"
    LLAMACPP = "llamacpp"
    CUSTOM = "custom"


class LLMClient:
    """
    Generic LLM client that uses configuration from Settings.
    
    Supports retry logic, fallback models, timeout handling, and comprehensive authentication.
    Validates authentication requirements for both cloud and on-premise LLM servers.
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
        
        # Detect provider and authentication requirements
        self.provider = self._detect_provider()
        self.auth_type = self._detect_auth_type()
        self.requires_auth = self._check_auth_required()
        
        # HTTP client for making requests
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            headers=self._get_headers()
        )
    
    def _detect_provider(self) -> LLMProvider:
        """
        Detect LLM provider from base URL and API key presence.
        
        Returns:
            LLMProvider enum value
        """
        if not self.base_url:
            return LLMProvider.CUSTOM
        
        url_lower = self.base_url.lower()
        
        # Cloud providers
        if "api.openai.com" in url_lower or "openai.azure.com" in url_lower:
            return LLMProvider.AZURE if "azure" in url_lower else LLMProvider.OPENAI
        elif "api.anthropic.com" in url_lower or "anthropic" in url_lower:
            return LLMProvider.ANTHROPIC
        elif "api.cohere.ai" in url_lower or "cohere" in url_lower:
            return LLMProvider.COHERE
        elif "huggingface" in url_lower or "hf.co" in url_lower:
            return LLMProvider.HUGGINGFACE
        
        # On-premise / Local providers
        # Check Ollama first (specific port and keyword)
        if "11434" in url_lower or "ollama" in url_lower:
            return LLMProvider.OLLAMA
        
        # HTTPS indicates external API server (vLLM/OpenAI-compatible)
        if url_lower.startswith("https://"):
            return LLMProvider.VLLM
        
        # If API key is present, likely vLLM/OpenAI-compatible (not Ollama)
        if self.api_key:
            return LLMProvider.VLLM
            
        # vLLM typically uses port 8000 and OpenAI-compatible endpoints
        # Check for :8000 port OR if URL contains /v1 (OpenAI-compatible indicator)
        if ":8000" in url_lower or "/v1" in url_lower:
            return LLMProvider.VLLM
        
        if "text-generation-webui" in url_lower or ":5000" in url_lower or ":7860" in url_lower:
            return LLMProvider.TEXTGEN_WEBUI
        if "llama.cpp" in url_lower or "llamacpp" in url_lower or ":8080" in url_lower:
            return LLMProvider.LLAMACPP
        
        # Default to VLLM for unknown OpenAI-compatible servers
        return LLMProvider.VLLM
    
    def _detect_auth_type(self) -> AuthType:
        """
        Detect authentication type based on provider and configuration.
        
        Returns:
            AuthType enum value
        """
        if not self.api_key:
            return AuthType.NONE
        
        # Cloud providers typically use Bearer tokens
        if self.provider in [LLMProvider.OPENAI, LLMProvider.ANTHROPIC, 
                            LLMProvider.COHERE, LLMProvider.AZURE]:
            return AuthType.BEARER
        
        # On-premise servers may use various auth methods
        # Default to Bearer for any API key provided
        return AuthType.BEARER
    
    def _check_auth_required(self) -> bool:
        """
        Check if authentication is required for the detected provider.
        
        Returns:
            True if authentication is required, False otherwise
        """
        # Cloud providers ALWAYS require authentication
        cloud_providers = [
            LLMProvider.OPENAI,
            LLMProvider.ANTHROPIC,
            LLMProvider.COHERE,
            LLMProvider.AZURE,
            LLMProvider.HUGGINGFACE
        ]
        
        if self.provider in cloud_providers:
            return True
        
        # Local providers typically don't require auth (but may support it)
        local_providers = [
            LLMProvider.OLLAMA,
            LLMProvider.LLAMACPP
        ]
        
        if self.provider in local_providers:
            # Check if it's actually localhost
            if self.base_url and ("localhost" in self.base_url or "127.0.0.1" in self.base_url):
                return False
            # If it's a remote server, authentication is recommended
            return True
        
        # For vLLM and TextGen WebUI, check if it's remote
        if self.provider in [LLMProvider.VLLM, LLMProvider.TEXTGEN_WEBUI]:
            if self.base_url and ("localhost" in self.base_url or "127.0.0.1" in self.base_url):
                return False
            return True
        
        # For custom providers, assume auth is required if not localhost
        if self.base_url and not ("localhost" in self.base_url or "127.0.0.1" in self.base_url):
            return True
        
        return False
    
    def validate_authentication(self) -> Tuple[bool, str]:
        """
        Validate that authentication is properly configured.
        
        Returns:
            Tuple of (is_valid, message)
        """
        # Check if authentication is required
        if not self.requires_auth:
            return True, "Authentication not required for this provider"
        
        # Check if API key is provided
        if not self.api_key:
            provider_name = self.provider.value.upper()
            if self.provider in [LLMProvider.OPENAI, LLMProvider.ANTHROPIC, 
                                LLMProvider.COHERE, LLMProvider.AZURE]:
                return False, f"API key is REQUIRED for {provider_name}. Please provide a valid API key."
            else:
                return False, f"Authentication is recommended for remote {provider_name} server. Please provide an API key or token."
        
        # Validate API key format for known providers
        if self.provider == LLMProvider.OPENAI:
            if not self.api_key.startswith("sk-"):
                return False, "OpenAI API key should start with 'sk-'"
        elif self.provider == LLMProvider.ANTHROPIC:
            if not self.api_key.startswith("sk-ant-"):
                return False, "Anthropic API key should start with 'sk-ant-'"
        elif self.provider == LLMProvider.COHERE:
            if len(self.api_key) < 20:
                return False, "Cohere API key appears to be invalid (too short)"
        
        return True, "Authentication configured correctly"
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Build request headers with appropriate authentication.
        
        Returns:
            Dictionary of HTTP headers
        """
        headers = {
            "Content-Type": "application/json",
        }
        
        if self.api_key:
            if self.auth_type == AuthType.BEARER:
                headers["Authorization"] = f"Bearer {self.api_key}"
            elif self.auth_type == AuthType.API_KEY:
                # Some providers use X-API-Key header
                headers["X-API-Key"] = self.api_key
            elif self.auth_type == AuthType.CUSTOM:
                # For custom auth, use Bearer as default
                headers["Authorization"] = f"Bearer {self.api_key}"
        
        # Provider-specific headers
        if self.provider == LLMProvider.ANTHROPIC:
            headers["anthropic-version"] = "2023-06-01"
        
        return headers
    
    def _mask_api_key(self, text: str) -> str:
        """
        Mask API key in text for logging.
        
        Args:
            text: Text that may contain API key
            
        Returns:
            Text with API key masked
        """
        if not self.api_key or not text:
            return text
        
        # Mask the API key, showing only first 4 and last 4 characters
        if len(self.api_key) > 8:
            masked = f"{self.api_key[:4]}...{self.api_key[-4:]}"
        else:
            masked = "****"
        
        return text.replace(self.api_key, masked)
    
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

        # Normalize standardized model ids like "ollama:llama2" -> "llama2" for provider endpoints
        def _normalize_model_for_provider(raw: str) -> str:
            try:
                if not raw:
                    return raw
                lowered = raw.lower()
                # Known provider prefixes to strip
                prefixes = [
                    "ollama:", "openai:", "anthropic:", "azure:", "cohere:",
                    "huggingface:", "vllm:", "llamacpp:", "textgen_webui:", "custom:"
                ]
                for p in prefixes:
                    if lowered.startswith(p):
                        return raw.split(":", 1)[1]
                return raw
            except Exception:
                return raw

        model = _normalize_model_for_provider(model)
        
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
                # Ollama 0.13.x uses /api/generate with prompt (not messages)
                # OpenAI-compatible uses /chat/completions or /v1/chat/completions
                if self._is_ollama_endpoint():
                    # Ollama endpoint - use /api/generate (Ollama 0.13.x compatible)
                    endpoint = f"{self.base_url}/api/generate"
                    logger.info(f"[LLM Client] Ollama detected - calling endpoint: {endpoint}")
                    
                    # Convert messages to prompt for Ollama /api/generate
                    prompt_parts = []
                    for msg in messages:
                        role = msg.get("role", "user")
                        content = msg.get("content", "")
                        if role == "system":
                            prompt_parts.append(f"System: {content}")
                        elif role == "user":
                            prompt_parts.append(f"User: {content}")
                        elif role == "assistant":
                            prompt_parts.append(f"Assistant: {content}")
                    prompt_parts.append("Assistant:")
                    prompt = "\n".join(prompt_parts)
                    
                    payload = {
                        "model": model,
                        "prompt": prompt,
                        "stream": False
                    }
                    if temperature is not None:
                        if "options" not in payload:
                            payload["options"] = {}
                        payload["options"]["temperature"] = temperature
                    if max_tokens:
                        if "options" not in payload:
                            payload["options"] = {}
                        payload["options"]["num_predict"] = max_tokens
                else:
                    # OpenAI-compatible endpoint (vLLM, OpenAI, etc.)
                    # Use /v1/chat/completions if base URL doesn't already include /v1
                    if "/v1" in self.base_url:
                        endpoint = f"{self.base_url}/chat/completions"
                    else:
                        endpoint = f"{self.base_url}/v1/chat/completions"
                
                response = await self.client.post(
                    endpoint,
                    json=payload
                )
                
                logger.info(f"[LLM Client] Request sent to: {endpoint}, Status: {response.status_code}")
                logger.info(f"[LLM Client] Response headers: {dict(response.headers)}")
                
                response.raise_for_status()
                result = response.json()
                
                # Extract response based on endpoint type
                if self._is_ollama_endpoint():
                    # Ollama /api/generate returns {"response": "text", "model": "...", "done": true}
                    response_text = result.get("response", "")
                    return {
                        "response": {"choices": [{"message": {"content": response_text}}]},
                        "model_used": model,
                        "attempts": attempt + 1,
                        "success": True
                    }
                
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
        is_ollama = any(ollama_indicators)
        logger.info(f"[LLM Client] Checking if Ollama endpoint - base_url: {self.base_url}, is_ollama: {is_ollama}")
        return is_ollama
    
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
            # Ollama streaming - use /api/generate with stream=true (Ollama 0.13.x)
            endpoint = f"{self.base_url}/api/generate"
            
            # Convert messages to prompt for Ollama /api/generate
            prompt_parts = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "system":
                    prompt_parts.append(f"System: {content}")
                elif role == "user":
                    prompt_parts.append(f"User: {content}")
                elif role == "assistant":
                    prompt_parts.append(f"Assistant: {content}")
            prompt_parts.append("Assistant:")
            prompt = "\n".join(prompt_parts)
            
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": True
            }
            if temperature is not None:
                if "options" not in payload:
                    payload["options"] = {}
                payload["options"]["temperature"] = temperature
            if max_tokens:
                if "options" not in payload:
                    payload["options"] = {}
                payload["options"]["num_predict"] = max_tokens
        else:
            # OpenAI-compatible streaming (vLLM, OpenAI, etc.)
            # Use /v1/chat/completions if base URL doesn't already include /v1
            if "/v1" in self.base_url:
                endpoint = f"{self.base_url}/chat/completions"
            else:
                endpoint = f"{self.base_url}/v1/chat/completions"
        
        async with self.client.stream(
            "POST",
            endpoint,
            json=payload
        ) as response:
            response.raise_for_status()
            
            if self._is_ollama_endpoint():
                # Ollama /api/generate streaming returns JSON lines with "response": "token"
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            data = json.loads(line)
                            # Ollama /api/generate format: {"response": "token", "done": false}
                            token = data.get("response", "")
                            if token:
                                yield token
                        except json.JSONDecodeError:
                            continue
            else:
                # OpenAI-compatible streaming
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
