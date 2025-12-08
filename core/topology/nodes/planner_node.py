"""
Planner Node - Creates a plan for handling the user request.

Uses planner_registry to create a plan based on intent.
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


def planner_node(
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
    Create planner node.
    
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
    # Get planner name from config
    planner_name = config.get("planner_name", "default_planner")
    
    # Get intent-to-planner mapping
    intent_planner_map = config.get("intent_planner_map", {})
    
    async def node_fn(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Planner node function.
        
        Args:
            state: Current state
            
        Returns:
            Updated state
        """
        try:
            logger.info(f"Planning: {state.get('run_id')}")
            
            # Get input
            input_text = state.get("input", "")
            
            # Get intent
            intent = state.get("intent", "unknown")
            
            # Determine planner to use based on intent
            selected_planner_name = intent_planner_map.get(intent, planner_name)
            
            # Get planner
            planner = planner_registry.get_planner(selected_planner_name)
            if not planner:
                logger.error(f"Planner not found: {selected_planner_name}")
                state["error"] = f"Planner not found: {selected_planner_name}"
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
            
            # Create plan
            plan = await planner(input_text, intent, metadata)
            
            # Update state
            state["plan"] = plan.to_dict()
            
            # Add to history
            state["history"].append({
                "node": "planner",
                "planner": selected_planner_name,
                "plan": state["plan"]
            })
            
            logger.info(f"Created plan with {len(plan.tasks)} tasks")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in planner node: {str(e)}")
            state["error"] = str(e)
            return state
    
    return node_fn
