"""
End Node - Final node in the topology execution.

Finalizes state and returns the result.
"""

import logging
import time
from typing import Dict, Any, Callable

from ...agent.agent_registry import AgentRegistry
from ...planner_router.planner_registry import PlannerRegistry
from ...planner_router.router_registry import RouterRegistry
from ...tools.tool_registry import ToolRegistry
from ...memory_cache.memory_service import MemoryService
from ...memory_cache.cache_service import CacheService
from ...config.config_service import ConfigService

logger = logging.getLogger(__name__)


def end_node(
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
    Create end node.
    
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
        End node function.
        
        Args:
            state: Current state
            
        Returns:
            Updated state
        """
        try:
            logger.info(f"Ending execution: {state.get('run_id')}")
            
            # Add end step to history
            state["history"].append({
                "node": "end",
                "timestamp": time.time(),
                "output": state.get("output", "")
            })
            
            # Calculate execution time
            start_time = state.get("timestamp", 0)
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Add execution time to state
            state["execution_time"] = execution_time
            
            # Add metadata
            state["metadata"] = state.get("metadata", {})
            state["metadata"]["execution_time"] = execution_time
            
            # Log execution time
            logger.info(f"Execution completed in {execution_time:.2f} seconds")
            
            # Cache result if needed
            if config.get("cache_results", False):
                cache_key = f"result:{state.get('run_id')}"
                await cache_service.set(
                    key=cache_key,
                    value={
                        "output": state.get("output", ""),
                        "execution_time": execution_time,
                        "history": state.get("history", [])
                    },
                    ttl_seconds=config.get("cache_ttl_seconds", 3600)  # Default: 1 hour
                )
            
            return state
            
        except Exception as e:
            logger.error(f"Error in end node: {str(e)}")
            state["error"] = str(e)
            return state
    
    return node_fn
