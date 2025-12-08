"""
Start Node - Entry point for topology execution.

Initializes state and performs any necessary setup.
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


def start_node(
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
    Create start node.
    
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
    async def node_fn(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start node function.
        
        Args:
            state: Current state
            
        Returns:
            Updated state
        """
        try:
            logger.info(f"Starting execution: {state.get('run_id')}")
            
            # Initialize state if needed
            if "history" not in state:
                state["history"] = []
            
            if "intermediate_steps" not in state:
                state["intermediate_steps"] = []
            
            # Add start step to history
            state["history"].append({
                "node": "start",
                "timestamp": state.get("timestamp"),
                "input": state.get("input")
            })
            
            # Get client configuration if available
            client_id = state.get("client_id")
            if client_id:
                client_config = config_service.get_client_config(client_id)
                if client_config:
                    state["client_config"] = client_config
            
            # Set default output
            if "output" not in state:
                state["output"] = ""
            
            return state
            
        except Exception as e:
            logger.error(f"Error in start node: {str(e)}")
            state["error"] = str(e)
            return state
    
    return node_fn
