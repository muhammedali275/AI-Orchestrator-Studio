"""
LLM Registry - Factory for LLM clients.

Builds LangChain-compatible LLMs using config from config_service.
NO hard-coded IPs/ports/keys.
"""

import logging
from typing import Dict, Any, Optional, List, Union

from langchain.llms.base import LLM
from langchain.chat_models.base import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI, OpenAI
from langchain_community.llms import Ollama
from langchain_community.chat_models import ChatOllama

from ..config.config_service import ConfigService, LLMConfig

logger = logging.getLogger(__name__)


class LLMRegistry:
    """
    Factory for LLM clients.
    
    Builds LangChain-compatible LLMs using config from config_service.
    """
    
    def __init__(self, config_service: ConfigService):
        """
        Initialize LLM registry.
        
        Args:
            config_service: Configuration service
        """
        self.config_service = config_service
        self._llm_instances: Dict[str, Union[LLM, BaseChatModel]] = {}
    
    def get_llm(self, name: str) -> Optional[Union[LLM, BaseChatModel]]:
        """
        Get LLM instance by name.
        
        Args:
            name: LLM name/identifier
            
        Returns:
            LangChain LLM instance or None if not found/configured
        """
        # Return cached instance if available
        if name in self._llm_instances:
            return self._llm_instances[name]
        
        # Get configuration
        config = self.config_service.get_llm_config(name)
        if not config:
            logger.error(f"LLM configuration not found: {name}")
            return None
        
        if not config.enabled:
            logger.warning(f"LLM is disabled: {name}")
            return None
        
        # Create LLM instance based on provider
        try:
            llm = self._create_llm_instance(config)
            if llm:
                self._llm_instances[name] = llm
                return llm
            else:
                logger.error(f"Failed to create LLM instance: {name}")
                return None
        except Exception as e:
            logger.error(f"Error creating LLM instance {name}: {str(e)}")
            return None
    
    def _create_llm_instance(self, config: LLMConfig) -> Optional[Union[LLM, BaseChatModel]]:
        """
        Create LLM instance based on configuration.
        
        Args:
            config: LLM configuration
            
        Returns:
            LangChain LLM instance or None if creation fails
        """
        provider = config.provider.lower()
        
        # Common parameters
        params = {
            "temperature": config.temperature,
            "verbose": True,
        }
        
        if config.max_tokens:
            params["max_tokens"] = config.max_tokens
        
        # OpenAI
        if provider == "openai":
            return self._create_openai_instance(config, params)
        
        # Azure OpenAI
        elif provider == "azure":
            return self._create_azure_instance(config, params)
        
        # Ollama
        elif provider == "ollama":
            return self._create_ollama_instance(config, params)
        
        # vLLM
        elif provider == "vllm":
            return self._create_vllm_instance(config, params)
        
        # Anthropic
        elif provider == "anthropic":
            return self._create_anthropic_instance(config, params)
        
        # Hugging Face
        elif provider == "huggingface":
            return self._create_huggingface_instance(config, params)
        
        # Unknown provider
        else:
            logger.error(f"Unsupported LLM provider: {provider}")
            return None
    
    def _create_openai_instance(self, config: LLMConfig, params: Dict[str, Any]) -> Optional[Union[LLM, BaseChatModel]]:
        """Create OpenAI LLM instance."""
        try:
            # Set API key and base URL if provided
            if config.api_key:
                params["api_key"] = config.api_key
            
            if config.base_url:
                params["base_url"] = config.base_url
            
            # Set timeout
            params["request_timeout"] = config.timeout_seconds
            
            # Create chat model for chat-capable models
            if "gpt" in config.model.lower() or config.model.lower().startswith("ft:gpt"):
                return ChatOpenAI(
                    model=config.model,
                    **params
                )
            # Create completion model for other models
            else:
                return OpenAI(
                    model=config.model,
                    **params
                )
        except Exception as e:
            logger.error(f"Error creating OpenAI instance: {str(e)}")
            return None
    
    def _create_azure_instance(self, config: LLMConfig, params: Dict[str, Any]) -> Optional[Union[LLM, BaseChatModel]]:
        """Create Azure OpenAI LLM instance."""
        try:
            # Azure-specific parameters
            azure_params = {
                "azure_deployment": config.metadata.get("deployment_name"),
                "azure_endpoint": config.base_url,
                "api_key": config.api_key,
                "api_version": config.metadata.get("api_version", "2023-05-15"),
            }
            
            # Merge with common parameters
            params.update(azure_params)
            
            # Create chat model for chat-capable models
            if "gpt" in config.model.lower():
                return ChatOpenAI(
                    model=config.model,
                    **params
                )
            # Create completion model for other models
            else:
                return OpenAI(
                    model=config.model,
                    **params
                )
        except Exception as e:
            logger.error(f"Error creating Azure OpenAI instance: {str(e)}")
            return None
    
    def _create_ollama_instance(self, config: LLMConfig, params: Dict[str, Any]) -> Optional[Union[LLM, BaseChatModel]]:
        """Create Ollama LLM instance."""
        try:
            # Ollama-specific parameters
            ollama_params = {
                "base_url": config.base_url or "http://localhost:11434",
                "model": config.model,
            }
            
            # Merge with common parameters
            params.update(ollama_params)
            
            # Check if model supports chat interface
            chat_capable_models = ["llama", "mistral", "mixtral", "phi", "gemma", "qwen"]
            is_chat_capable = any(model in config.model.lower() for model in chat_capable_models)
            
            if is_chat_capable:
                return ChatOllama(**params)
            else:
                return Ollama(**params)
        except Exception as e:
            logger.error(f"Error creating Ollama instance: {str(e)}")
            return None
    
    def _create_vllm_instance(self, config: LLMConfig, params: Dict[str, Any]) -> Optional[Union[LLM, BaseChatModel]]:
        """Create vLLM instance."""
        try:
            from langchain_community.llms import VLLM
            
            # vLLM-specific parameters
            vllm_params = {
                "model": config.model,
                "trust_remote_code": True,
                "max_new_tokens": config.max_tokens or 512,
            }
            
            # Add base URL if provided
            if config.base_url:
                vllm_params["openai_api_base"] = config.base_url
            
            # Merge with common parameters
            params.update(vllm_params)
            
            return VLLM(**params)
        except ImportError:
            logger.error("vLLM not installed. Install with 'pip install vllm'")
            return None
        except Exception as e:
            logger.error(f"Error creating vLLM instance: {str(e)}")
            return None
    
    def _create_anthropic_instance(self, config: LLMConfig, params: Dict[str, Any]) -> Optional[Union[LLM, BaseChatModel]]:
        """Create Anthropic LLM instance."""
        try:
            from langchain_anthropic import ChatAnthropic
            
            # Anthropic-specific parameters
            anthropic_params = {
                "model": config.model,
                "anthropic_api_key": config.api_key,
                "max_tokens": config.max_tokens or 1024,
            }
            
            # Merge with common parameters
            params.update(anthropic_params)
            
            return ChatAnthropic(**params)
        except ImportError:
            logger.error("Anthropic package not installed. Install with 'pip install langchain-anthropic'")
            return None
        except Exception as e:
            logger.error(f"Error creating Anthropic instance: {str(e)}")
            return None
    
    def _create_huggingface_instance(self, config: LLMConfig, params: Dict[str, Any]) -> Optional[Union[LLM, BaseChatModel]]:
        """Create Hugging Face LLM instance."""
        try:
            from langchain_huggingface import HuggingFaceEndpoint
            
            # HuggingFace-specific parameters
            hf_params = {
                "repo_id": config.model,
                "huggingfacehub_api_token": config.api_key,
                "task": config.metadata.get("task", "text-generation"),
            }
            
            # Add endpoint URL if provided
            if config.base_url:
                hf_params["endpoint_url"] = config.base_url
            
            # Merge with common parameters
            params.update(hf_params)
            
            return HuggingFaceEndpoint(**params)
        except ImportError:
            logger.error("HuggingFace package not installed. Install with 'pip install langchain-huggingface'")
            return None
        except Exception as e:
            logger.error(f"Error creating HuggingFace instance: {str(e)}")
            return None
    
    def list_available_llms(self) -> List[str]:
        """
        List names of all available LLMs.
        
        Returns:
            List of LLM names
        """
        configs = self.config_service.list_llms()
        return [config.name for config in configs if config.enabled]
    
    def refresh_llm(self, name: str) -> bool:
        """
        Refresh LLM instance by name.
        
        Args:
            name: LLM name/identifier
            
        Returns:
            True if successful, False otherwise
        """
        if name in self._llm_instances:
            del self._llm_instances[name]
        
        return self.get_llm(name) is not None
    
    def refresh_all_llms(self) -> None:
        """Refresh all LLM instances."""
        self._llm_instances.clear()
