"""
Error Handler Node - Handles errors that occur during topology execution.

Provides error handling and recovery mechanisms.
"""

import logging
import traceback
from typing import Dict, Any, Callable

from ...agent.agent_registry import AgentRegistry
from ...planner_router.planner_registry import PlannerRegistry
from ...planner_router.router_registry import RouterRegistry
from ...tools.tool_registry import ToolRegistry
from ...memory_cache.memory_service import MemoryService
from ...memory_cache.cache_service import CacheService
from ...config.config_service import ConfigService

logger = logging.getLogger(__name__)


def error_handler_node(
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
    Create error handler node.
    
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
    # Get error messages
    error_messages = config.get("error_messages", {})
    default_error_message = config.get(
        "default_error_message", 
        "I'm sorry, but I encountered an error while processing your request. Please try again later."
    )
    
    async def node_fn(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Error handler node function.
        
        Args:
            state: Current state
            
        Returns:
            Updated state
        """
        try:
            logger.error(f"Error handler triggered: {state.get('run_id')}")
            
            # Get error
            error = state.get("error", "Unknown error")
            
            # Log error
            logger.error(f"Error: {error}")
            if "traceback" in state:
                logger.error(f"Traceback: {state['traceback']}")
            
            # Add error step to history
            state["history"].append({
                "node": "error_handler",
                "error": error
            })
            
            # Determine error message
            error_message = default_error_message
            
            # Check for specific error types
            for error_type, message in error_messages.items():
                if error_type.lower() in str(error).lower():
                    error_message = message
                    break
            
            # Set output
            state["output"] = error_message
            
            # Add error details to metadata
            if "metadata" not in state:
                state["metadata"] = {}
            
            state["metadata"]["error"] = error
            
            # Get stack trace if available
            if "traceback" not in state:
                state["traceback"] = traceback.format_exc()
            
            state["metadata"]["traceback"] = state["traceback"]
            
            # Log error to monitoring service if configured
            if config.get("log_errors_to_monitoring", True):
                # This would typically call a monitoring service
                # For now, we'll just log it
                logger.error(f"Error in topology execution: {error}")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in error handler node: {str(e)}")
            
            # If the error handler itself fails, we need a fallback
            state["output"] = "An unexpected error occurred. Please try again later."
            state["error"] = f"Error handler failed: {str(e)}"
            
            return state
    
    return node_fn
