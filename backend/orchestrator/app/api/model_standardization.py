"""
Model ID Standardization - Consistent model identifier handling.

Standardizes model identifiers across all LLM integrations to ensure consistent format:
- Model name (short identifier like 'llama2-7b')
- Model provider ('ollama', 'openai', 'claude')
- Full qualified name ('ollama:llama2-7b')
"""

import logging
import re
from typing import Dict, Any, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class ModelProvider(str, Enum):
    """Supported model providers."""
    OLLAMA = "ollama"
    OPENAI = "openai"
    CLAUDE = "claude"
    HUGGINGFACE = "huggingface"
    LOCAL = "local"
    UNKNOWN = "unknown"


class StandardizedModel:
    """Standardized model identifier."""
    
    def __init__(
        self,
        name: str,
        provider: ModelProvider = ModelProvider.UNKNOWN,
        variant: Optional[str] = None
    ):
        """
        Initialize standardized model.
        
        Args:
            name: Model name (e.g., 'llama2-7b')
            provider: Model provider
            variant: Optional model variant (e.g., 'q4', 'q8')
        """
        self.name = name.lower().strip()
        self.provider = provider
        self.variant = variant.lower() if variant else None
    
    @property
    def full_id(self) -> str:
        """Get full qualified model ID."""
        if self.variant:
            return f"{self.provider.value}:{self.name}-{self.variant}"
        return f"{self.provider.value}:{self.name}"
    
    @property
    def short_id(self) -> str:
        """Get short model ID (name only)."""
        if self.variant:
            return f"{self.name}-{self.variant}"
        return self.name
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return {
            "id": self.full_id,
            "name": self.short_id,
            "provider": self.provider.value,
            "variant": self.variant
        }
    
    def __str__(self) -> str:
        return self.full_id
    
    def __repr__(self) -> str:
        return f"StandardizedModel({self.full_id})"


class ModelParser:
    """Parse and standardize model identifiers."""
    
    # Patterns for different model identifier formats
    PATTERNS = {
        # Full format: "ollama:llama2-7b" or "ollama:llama2-7b-q4"
        "full_qualified": r"^([^:]+):([a-z0-9\-]+)(?:-([a-z0-9]+))?$",
        # Variant format: "llama2-7b-q4"
        "variant": r"^([a-z0-9\-]+)-(q[0-9]|fp[0-9]+|int[0-9]+)$",
        # Simple name: "llama2" or "llama2-7b"
        "simple": r"^([a-z0-9\-]+)$"
    }
    
    @staticmethod
    def detect_provider(model_id: str) -> ModelProvider:
        """
        Detect model provider from model ID.
        
        Args:
            model_id: Model identifier
            
        Returns:
            Detected provider
        """
        model_lower = model_id.lower()
        
        # Check for explicit provider prefix
        if ":" in model_id:
            provider_str = model_id.split(":")[0].lower()
            try:
                return ModelProvider(provider_str)
            except ValueError:
                pass
        
        # Infer from model name patterns
        if any(x in model_lower for x in ["gpt-", "gpt3", "gpt4", "claude"]):
            return ModelProvider.OPENAI
        elif any(x in model_lower for x in ["claude-", "claude3"]):
            return ModelProvider.CLAUDE
        elif any(x in model_lower for x in ["mistral", "neural-", "zephyr", "dolphin"]):
            return ModelProvider.OLLAMA
        elif any(x in model_lower for x in ["meta-llama", "llama2", "llama-70b"]):
            return ModelProvider.OLLAMA
        elif "hugging" in model_lower:
            return ModelProvider.HUGGINGFACE
        
        # Default to unknown if cannot determine
        return ModelProvider.UNKNOWN
    
    @staticmethod
    def parse(model_id: str) -> StandardizedModel:
        """
        Parse model identifier and return standardized form.
        
        Args:
            model_id: Model identifier in any format
            
        Returns:
            StandardizedModel instance
            
        Examples:
            "ollama:llama2-7b" → StandardizedModel("llama2-7b", ModelProvider.OLLAMA)
            "gpt-4" → StandardizedModel("gpt-4", ModelProvider.OPENAI)
            "llama2:7b" → StandardizedModel("llama2-7b", ModelProvider.OLLAMA)
        """
        model_id = model_id.strip()
        
        # Try full qualified format first
        match = re.match(ModelParser.PATTERNS["full_qualified"], model_id)
        if match:
            provider_str, name, variant = match.groups()
            try:
                provider = ModelProvider(provider_str.lower())
            except ValueError:
                provider = ModelParser.detect_provider(model_id)
            
            return StandardizedModel(name, provider, variant)
        
        # Detect provider and parse
        provider = ModelParser.detect_provider(model_id)
        
        # Clean up model name
        name = model_id.split(":")[-1] if ":" in model_id else model_id
        
        # Extract variant if present
        variant = None
        variant_match = re.match(ModelParser.PATTERNS["variant"], name)
        if variant_match:
            name, variant = variant_match.groups()
        
        return StandardizedModel(name, provider, variant)
    
    @staticmethod
    def standardize(model_id: str, use_full: bool = True) -> str:
        """
        Standardize model ID to consistent format.
        
        Args:
            model_id: Model ID to standardize
            use_full: Return full qualified ID or short ID
            
        Returns:
            Standardized model ID
        """
        model = ModelParser.parse(model_id)
        return model.full_id if use_full else model.short_id


class ModelValidator:
    """Validate model identifiers and configurations."""
    
    # Known models for validation
    KNOWN_OLLAMA_MODELS = {
        "llama2", "llama2-7b", "llama2-13b", "llama2-70b",
        "mistral", "neural-chat", "zephyr", "dolphin-mixtral",
        "neural-chat-7b", "starling-lm", "orca-mini",
        "openchat", "sqlcoder", "phind-codellama",
        "llama4-scout"  # Custom model
    }
    
    KNOWN_OPENAI_MODELS = {
        "gpt-4", "gpt-4-turbo", "gpt-4-vision",
        "gpt-3.5-turbo", "gpt-3.5-turbo-16k",
        "text-davinci-003", "text-davinci-002"
    }
    
    KNOWN_CLAUDE_MODELS = {
        "claude-3-opus", "claude-3-sonnet", "claude-3-haiku",
        "claude-2", "claude-instant"
    }
    
    @staticmethod
    def validate(model_id: str, provider: Optional[ModelProvider] = None) -> Tuple[bool, str]:
        """
        Validate model identifier.
        
        Args:
            model_id: Model ID to validate
            provider: Optional provider to validate against
            
        Returns:
            Tuple of (is_valid, message)
        """
        if not model_id or not model_id.strip():
            return False, "Model ID cannot be empty"
        
        parsed = ModelParser.parse(model_id)
        
        # Check against known models
        if provider or parsed.provider != ModelProvider.UNKNOWN:
            check_provider = provider or parsed.provider
            
            if check_provider == ModelProvider.OLLAMA:
                if parsed.name not in ModelValidator.KNOWN_OLLAMA_MODELS:
                    return False, f"Unknown Ollama model: {parsed.name}. Known: {', '.join(sorted(ModelValidator.KNOWN_OLLAMA_MODELS))}"
            
            elif check_provider == ModelProvider.OPENAI:
                if parsed.name not in ModelValidator.KNOWN_OPENAI_MODELS:
                    return False, f"Unknown OpenAI model: {parsed.name}. Known: {', '.join(sorted(ModelValidator.KNOWN_OPENAI_MODELS))}"
            
            elif check_provider == ModelProvider.CLAUDE:
                if parsed.name not in ModelValidator.KNOWN_CLAUDE_MODELS:
                    return False, f"Unknown Claude model: {parsed.name}. Known: {', '.join(sorted(ModelValidator.KNOWN_CLAUDE_MODELS))}"
        
        return True, "Valid model ID"
    
    @staticmethod
    def suggest_models(provider: ModelProvider) -> list:
        """
        Get list of suggested models for provider.
        
        Args:
            provider: Model provider
            
        Returns:
            List of known models for provider
        """
        if provider == ModelProvider.OLLAMA:
            return sorted(list(ModelValidator.KNOWN_OLLAMA_MODELS))
        elif provider == ModelProvider.OPENAI:
            return sorted(list(ModelValidator.KNOWN_OPENAI_MODELS))
        elif provider == ModelProvider.CLAUDE:
            return sorted(list(ModelValidator.KNOWN_CLAUDE_MODELS))
        return []


def get_standardized_model(model_id: Optional[str], default: str = "ollama:llama2-7b") -> StandardizedModel:
    """
    Get standardized model, with fallback to default.
    
    Args:
        model_id: Model ID to standardize
        default: Default model if ID is None or invalid
        
    Returns:
        StandardizedModel instance
    """
    if not model_id:
        return ModelParser.parse(default)
    
    try:
        return ModelParser.parse(model_id)
    except Exception as e:
        logger.warning(f"Failed to parse model {model_id}, using default: {e}")
        return ModelParser.parse(default)
