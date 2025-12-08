import os
import time
import logging
from typing import List, Dict, Any, Optional
from litellm import completion, APIError, Timeout
import yaml

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self, config_path: str = None):
        self.config_path = config_path or os.path.join(
            os.getenv("ORCHESTRATOR_PATH", "/path/to/orchestrator"),
            "etc", "enterprise-agent", "settings.yaml"
        )
        self.models_config = self._load_models_config()
        self.settings = self._load_settings()

    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from YAML"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f) or {}
        return {}

    def _load_models_config(self) -> Dict[str, Any]:
        """Load models configuration"""
        models_path = os.path.join(
            os.path.dirname(self.config_path),
            "models.yaml"
        )
        if os.path.exists(models_path):
            with open(models_path, 'r') as f:
                return yaml.safe_load(f) or {}
        return {"models": [], "routing": {}}

    def call_llm_with_retry(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        max_retries: int = 3,
        backoff_base: float = 2.0,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """
        Call LLM with retry logic, backoff, and fallback models
        """
        if not model:
            model = self.settings.get("llm_model", "openrouter/xai-model-id")

        fallback_models = self._get_fallback_models(model)

        last_error = None

        for attempt in range(max_retries):
            current_model = model if attempt == 0 else fallback_models[attempt % len(fallback_models)]

            try:
                logger.info(f"[LLM] Attempt {attempt + 1}/{max_retries} with model {current_model}")

                response = completion(
                    model=current_model,
                    messages=messages,
                    timeout=timeout,
                    **self._get_model_params(current_model)
                )

                logger.info(f"[LLM] Success with model {current_model}")
                return {
                    "response": response,
                    "model_used": current_model,
                    "attempts": attempt + 1
                }

            except (APIError, Timeout) as e:
                error_msg = str(e).lower()
                last_error = e

                # Check if error is retryable
                if self._is_retryable_error(error_msg):
                    if attempt < max_retries - 1:
                        backoff_time = backoff_base ** attempt
                        logger.warning(f"[LLM] {error_msg}. Retrying in {backoff_time}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(backoff_time)
                        continue
                    else:
                        logger.error(f"[LLM] Max retries exceeded. Final error: {error_msg}")
                else:
                    # Non-retryable error, don't retry
                    logger.error(f"[LLM] Non-retryable error: {error_msg}")
                    break

        # All retries exhausted or non-retryable error
        raise last_error or Exception("LLM call failed after all retries")

    def _get_fallback_models(self, primary_model: str) -> List[str]:
        """Get fallback models for the primary model"""
        routing = self.models_config.get("routing", {})
        fallbacks = routing.get(primary_model, [])

        # Default fallbacks if none configured
        if not fallbacks:
            fallbacks = [
                "openai/gpt-3.5-turbo",
                "anthropic/claude-3-haiku",
                "google/gemini-pro"
            ]

        return fallbacks

    def _get_model_params(self, model: str) -> Dict[str, Any]:
        """Get model-specific parameters"""
        models = self.models_config.get("models", [])
        model_config = next((m for m in models if m.get("id") == model), {})

        params = {}
        if "temperature" in model_config:
            params["temperature"] = model_config["temperature"]
        if "max_tokens" in model_config:
            params["max_tokens"] = model_config["max_tokens"]

        return params

    def _is_retryable_error(self, error_msg: str) -> bool:
        """Determine if an error is retryable"""
        retryable_patterns = [
            "overloaded",
            "rate limit",
            "timeout",
            "connection",
            "server error",
            "502",
            "503",
            "504"
        ]

        return any(pattern in error_msg for pattern in retryable_patterns)

    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models with status"""
        models = self.models_config.get("models", [])
        return [
            {
                "id": model.get("id"),
                "name": model.get("name", model.get("id")),
                "provider": model.get("provider", "unknown"),
                "status": "available"  # In real implementation, check health
            }
            for model in models
        ]

# Convenience function for external use
def call_llm_with_retry(
    messages: List[Dict[str, str]],
    model: str = None,
    max_retries: int = 3,
    backoff_base: float = 2.0,
    timeout: int = 60
) -> Dict[str, Any]:
    """
    Convenience function to call LLM with retry and fallback logic
    """
    client = LLMClient()
    return client.call_llm_with_retry(messages, model, max_retries, backoff_base, timeout)
