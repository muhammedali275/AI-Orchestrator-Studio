"""
Intent Router Node - Routes input to appropriate handler based on intent.

Uses router_registry to determine intent.
"""

import logging
from typing import Dict, Any, Callable

from ...agent.agent_registry import AgentRegistry
from ...planner_router.planner_registry import PlannerRegistry
from ...planner_router.router_registry import RouterRegistry
from ...tools.tool_registry import ToolRegistry
from ...memory_cache.memory_service import MemoryService
from ...memory_cache.cache_service import CacheService
from ...config.config_service import ConfigService

logger = logging.getLogger(__name__)


def intent_router_node(
    config: Dict[str, Any],
    agent_registry: AgentRegistry,
    planner_registry: PlannerRegistry,
    router_registry: RouterRegistry,
    tool_registry: ToolRegistry,
    memory_service: MemoryService,
    cache_service: CacheService,
    config_service: ConfigService
) -> Callable:
    """
    Create intent router node.
    
    Args:
        config: Node configuration
        agent_registry: Agent registry
        planner_registry: Planner registry
        router_registry: Router registry
        tool_registry: Tool registry
        memory_service: Memory service
        cache_service: Cache service
        config_service: Configuration service
        
    Returns:
        Node function
    """
    # Get router name from config
    router_name = config.get("router_name", "default_router")
    
    async def node_fn(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Intent router node function.
        
        Args:
            state: Current state
            
        Returns:
            Updated state
        """
        try:
            logger.info(f"Routing intent: {state.get('run_id')}")
            
            # Get input
            input_text = state.get("input", "")
            
            # Get router
            router = router_registry.get_router(router_name)
            if not router:
                logger.error(f"Router not found: {router_name}")
                state["error"] = f"Router not found: {router_name}"
                return state
            
            # Get metadata
            metadata = {
                "user_id": state.get("user_id"),
                "conversation_id": state.get("conversation_id"),
                "client_id": state.get("client_id"),
                "run_id": state.get("run_id")
            }
            
            # Get client configuration if available
            if "client_config" in state:
                metadata["client_config"] = state["client_config"]
            
            # Route intent
            result = await router(input_text, metadata)
            
            # Update state
            state["intent"] = result.get("intent")
            state["intent_confidence"] = result.get("confidence")
            state["intent_reasoning"] = result.get("reasoning")
            
            # Add to history
            state["history"].append({
                "node": "intent_router",
                "intent": state["intent"],
                "confidence": state["intent_confidence"],
                "reasoning": state["intent_reasoning"]
            })
            
            logger.info(f"Detected intent: {state['intent']} (confidence: {state['intent_confidence']})")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in intent router node: {str(e)}")
            state["error"] = str(e)
            return state
    
    return node_fn
