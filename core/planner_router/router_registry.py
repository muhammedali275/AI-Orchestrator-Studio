"""
Router Registry - Factory for routers.

Builds routers using config from config_service.
Supports LLM-based, rules-based, and semantic-layer routers.
"""

import logging
from typing import Dict, Any, Optional, List, Callable, Union

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

from ..config.config_service import ConfigService, RouterConfig
from ..llm.llm_registry import LLMRegistry

logger = logging.getLogger(__name__)


class RouterRegistry:
    """
    Factory for routers.
    
    Builds routers using config from config_service.
    """
    
    def __init__(
        self, 
        config_service: ConfigService,
        llm_registry: LLMRegistry
    ):
        """
        Initialize router registry.
        
        Args:
            config_service: Configuration service
            llm_registry: LLM registry
        """
        self.config_service = config_service
        self.llm_registry = llm_registry
        self._router_instances: Dict[str, Callable] = {}
    
    def get_router(self, name: str) -> Optional[Callable]:
        """
        Get router instance by name.
        
        Args:
            name: Router name/identifier
            
        Returns:
            Router function or None if not found/configured
        """
        # Return cached instance if available
        if name in self._router_instances:
            return self._router_instances[name]
        
        # Get configuration
        config = self.config_service.get_router_config(name)
        if not config:
            logger.error(f"Router configuration not found: {name}")
            return None
        
        if not config.enabled:
            logger.warning(f"Router is disabled: {name}")
            return None
        
        # Create router instance
        try:
            router = self._create_router_instance(config)
            if router:
                self._router_instances[name] = router
                return router
            else:
                logger.error(f"Failed to create router instance: {name}")
                return None
        except Exception as e:
            logger.error(f"Error creating router instance {name}: {str(e)}")
            return None
    
    def _create_router_instance(self, config: RouterConfig) -> Optional[Callable]:
        """
        Create router instance based on configuration.
        
        Args:
            config: Router configuration
            
        Returns:
            Router function or None if creation fails
        """
        router_type = config.type.lower()
        
        if router_type == "llm":
            return self._create_llm_router(config)
        elif router_type == "rules":
            return self._create_rules_router(config)
        elif router_type == "semantic":
            return self._create_semantic_router(config)
        else:
            logger.error(f"Unsupported router type: {router_type}")
            return None
    
    def _create_llm_router(self, config: RouterConfig) -> Optional[Callable]:
        """
        Create LLM-based router.
        
        Args:
            config: Router configuration
            
        Returns:
            Router function or None if creation fails
        """
        try:
            # Get LLM
            llm = self.llm_registry.get_llm(config.llm_name)
            if not llm:
                logger.error(f"LLM not found for router {config.name}: {config.llm_name}")
                return None
            
            # Get system prompt
            system_prompt = config.parameters.get("system_prompt", """
            You are an intent classifier. Your job is to determine the user's intent from their message.
            
            Available intents:
            - general_llm: General conversation or question answering
            - web_search: Request for information that requires web search
            - tool_execution: Request to use a specific tool or perform a specific action
            - data_query: Request for data or analytics
            - code_generation: Request to generate or modify code
            - external_agent: Request that should be handled by a specialized agent
            - unknown: Intent cannot be determined
            
            Respond with a JSON object containing:
            - intent: The detected intent (one of the above)
            - confidence: A number between 0 and 1 indicating your confidence
            - reasoning: A brief explanation of your reasoning
            """)
            
            # Get available intents
            available_intents = config.parameters.get("available_intents", [
                "general_llm",
                "web_search",
                "tool_execution",
                "data_query",
                "code_generation",
                "external_agent",
                "unknown"
            ])
            
            # Update system prompt with available intents if needed
            if "Available intents:" in system_prompt:
                intent_list = "\n".join([f"- {intent}" for intent in available_intents])
                system_prompt = system_prompt.replace(
                    "Available intents:\n- general_llm: General conversation or question answering\n- web_search: Request for information that requires web search\n- tool_execution: Request to use a specific tool or perform a specific action\n- data_query: Request for data or analytics\n- code_generation: Request to generate or modify code\n- external_agent: Request that should be handled by a specialized agent\n- unknown: Intent cannot be determined",
                    f"Available intents:\n{intent_list}"
                )
            
            # Create prompt template
            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=system_prompt),
                HumanMessage(content="{input}")
            ])
            
            # Create chain
            chain = prompt | llm
            
            # Create router function
            def llm_router(input_text: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
                """
                LLM-based router function.
                
                Args:
                    input_text: User input
                    metadata: Additional metadata
                    
                Returns:
                    Dictionary with intent, confidence, and reasoning
                """
                try:
                    # Add metadata to input if provided
                    if metadata:
                        metadata_str = "\n".join([f"{k}: {v}" for k, v in metadata.items()])
                        input_text = f"{input_text}\nContext:\n{metadata_str}"
                    
                    # Invoke chain
                    result = chain.invoke({"input": input_text})
                    
                    # Parse result
                    import json
                    
                    # Extract JSON from result
                    if isinstance(result, str):
                        # Try to find JSON object in the string
                        import re
                        json_match = re.search(r'\{.*\}', result, re.DOTALL)
                        if json_match:
                            classification = json.loads(json_match.group(0))
                        else:
                            # Try to parse the whole string as JSON
                            classification = json.loads(result)
                    else:
                        # If result is already a structured object
                        classification = result
                    
                    # Ensure required fields are present
                    if "intent" not in classification:
                        classification["intent"] = "unknown"
                    if "confidence" not in classification:
                        classification["confidence"] = 0.0
                    if "reasoning" not in classification:
                        classification["reasoning"] = "No reasoning provided"
                    
                    # Ensure intent is one of the available intents
                    if classification["intent"] not in available_intents:
                        classification["intent"] = "unknown"
                        classification["confidence"] = 0.0
                        classification["reasoning"] = f"Intent '{classification['intent']}' is not one of the available intents"
                    
                    # Add router name to result
                    classification["router"] = config.name
                    
                    return classification
                    
                except Exception as e:
                    logger.error(f"Error in LLM router: {str(e)}")
                    # Return default classification
                    return {
                        "intent": "unknown",
                        "confidence": 0.0,
                        "reasoning": f"Error in router: {str(e)}",
                        "router": config.name
                    }
            
            return llm_router
            
        except Exception as e:
            logger.error(f"Error creating LLM router: {str(e)}")
            return None
    
    def _create_rules_router(self, config: RouterConfig) -> Optional[Callable]:
        """
        Create rules-based router.
        
        Args:
            config: Router configuration
            
        Returns:
            Router function or None if creation fails
        """
        try:
            # Get rules from configuration
            rules = config.parameters.get("rules", [])
            
            # Get default intent
            default_intent = config.parameters.get("default_intent", "general_llm")
            
            # Create router function
            def rules_router(input_text: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
                """
                Rules-based router function.
                
                Args:
                    input_text: User input
                    metadata: Additional metadata
                    
                Returns:
                    Dictionary with intent, confidence, and reasoning
                """
                try:
                    # Default classification
                    classification = {
                        "intent": default_intent,
                        "confidence": 1.0,
                        "reasoning": "Default intent"
                    }
                    
                    # Apply rules
                    for rule in rules:
                        pattern = rule.get("pattern")
                        if pattern and pattern.lower() in input_text.lower():
                            classification = {
                                "intent": rule.get("intent", default_intent),
                                "confidence": rule.get("confidence", 1.0),
                                "reasoning": rule.get("reasoning", f"Matched pattern: {pattern}")
                            }
                            break
                    
                    # Add router name to result
                    classification["router"] = config.name
                    
                    return classification
                    
                except Exception as e:
                    logger.error(f"Error in rules router: {str(e)}")
                    # Return default classification
                    return {
                        "intent": default_intent,
                        "confidence": 0.0,
                        "reasoning": f"Error in router: {str(e)}",
                        "router": config.name
                    }
            
            return rules_router
            
        except Exception as e:
            logger.error(f"Error creating rules router: {str(e)}")
            return None
    
    def _create_semantic_router(self, config: RouterConfig) -> Optional[Callable]:
        """
        Create semantic-layer router.
        
        Args:
            config: Router configuration
            
        Returns:
            Router function or None if creation fails
        """
        try:
            # Get API endpoint from configuration
            api_endpoint = config.parameters.get("api_endpoint")
            if not api_endpoint:
                logger.error(f"API endpoint not configured for semantic router: {config.name}")
                return None
            
            # Create router function
            def semantic_router(input_text: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
                """
                Semantic-layer router function.
                
                Args:
                    input_text: User input
                    metadata: Additional metadata
                    
                Returns:
                    Dictionary with intent, confidence, and reasoning
                """
                try:
                    import httpx
                    
                    # Prepare request payload
                    payload = {
                        "input": input_text,
                        "metadata": metadata
                    }
                    
                    # Make request to semantic API
                    response = httpx.post(
                        api_endpoint,
                        json=payload,
                        timeout=30
                    )
                    
                    # Parse response
                    classification = response.json()
                    
                    # Ensure required fields are present
                    if "intent" not in classification:
                        classification["intent"] = "unknown"
                    if "confidence" not in classification:
                        classification["confidence"] = 0.0
                    if "reasoning" not in classification:
                        classification["reasoning"] = "No reasoning provided"
                    
                    # Add router name to result
                    classification["router"] = config.name
                    
                    return classification
                    
                except Exception as e:
                    logger.error(f"Error in semantic router: {str(e)}")
                    # Return default classification
                    return {
                        "intent": "unknown",
                        "confidence": 0.0,
                        "reasoning": f"Error in router: {str(e)}",
                        "router": config.name
                    }
            
            return semantic_router
            
        except Exception as e:
            logger.error(f"Error creating semantic router: {str(e)}")
            return None
    
    def list_available_routers(self) -> List[str]:
        """
        List names of all available routers.
        
        Returns:
            List of router names
        """
        configs = self.config_service.list_routers()
        return [config.name for config in configs if config.enabled]
    
    def refresh_router(self, name: str) -> bool:
        """
        Refresh router instance by name.
        
        Args:
            name: Router name/identifier
            
        Returns:
            True if successful, False otherwise
        """
        if name in self._router_instances:
            del self._router_instances[name]
        
        return self.get_router(name) is not None
    
    def refresh_all_routers(self) -> None:
        """Refresh all router instances."""
        self._router_instances.clear()
