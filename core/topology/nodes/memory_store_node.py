"""
Memory Store Node - Stores conversation and results in memory.

Uses memory_service to store conversation history.
"""

import logging
import time
from typing import Dict, Any, Callable, List, Optional

from ...agent.agent_registry import AgentRegistry
from ...planner_router.planner_registry import PlannerRegistry
from ...planner_router.router_registry import RouterRegistry
from ...tools.tool_registry import ToolRegistry
from ...memory_cache.memory_service import MemoryService
from ...memory_cache.cache_service import CacheService
from ...config.config_service import ConfigService

logger = logging.getLogger(__name__)


def memory_store_node(
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
    Create memory store node.
    
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
    # Get memory configuration
    store_input = config.get("store_input", True)
    store_output = config.get("store_output", True)
    store_intermediate_steps = config.get("store_intermediate_steps", False)
    store_sources = config.get("store_sources", True)
    
    # Get cache configuration
    cache_enabled = config.get("cache_enabled", True)
    cache_ttl_seconds = config.get("cache_ttl_seconds", 3600)  # Default: 1 hour
    
    async def node_fn(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Memory store node function.
        
        Args:
            state: Current state
            
        Returns:
            Updated state
        """
        try:
            logger.info(f"Storing in memory: {state.get('run_id')}")
            
            # Get conversation ID
            conversation_id = state.get("conversation_id")
            if not conversation_id:
                logger.warning("No conversation ID in state")
                return state
            
            # Get user ID
            user_id = state.get("user_id")
            if not user_id:
                logger.warning("No user ID in state")
                return state
            
            # Get input and output
            input_text = state.get("input", "")
            output_text = state.get("output", "")
            
            # Get or create conversation
            conversation = await memory_service.get_conversation(conversation_id)
            if not conversation:
                # Create conversation
                conversation = await memory_service.create_conversation(
                    user_id=user_id,
                    metadata={
                        "client_id": state.get("client_id"),
                        "run_id": state.get("run_id"),
                        "timestamp": state.get("timestamp")
                    }
                )
            
            # Store input if enabled
            if store_input and input_text:
                await memory_service.add_message(
                    conversation_id=conversation_id,
                    content=input_text,
                    role="user",
                    metadata={
                        "timestamp": state.get("timestamp"),
                        "run_id": state.get("run_id")
                    }
                )
            
            # Store output if enabled
            if store_output and output_text:
                # Prepare metadata
                metadata = {
                    "timestamp": time.time(),
                    "run_id": state.get("run_id"),
                    "execution_time": state.get("execution_time")
                }
                
                # Add sources if available and enabled
                if store_sources and "sources" in state:
                    metadata["sources"] = state["sources"]
                
                # Add intermediate steps if enabled
                if store_intermediate_steps and "intermediate_steps" in state:
                    metadata["intermediate_steps"] = _format_intermediate_steps(state["intermediate_steps"])
                
                # Add tool results if available
                if "tool_results" in state:
                    metadata["tool_results"] = state["tool_results"]
                
                # Store message
                await memory_service.add_message(
                    conversation_id=conversation_id,
                    content=output_text,
                    role="assistant",
                    metadata=metadata
                )
            
            # Cache result if enabled
            if cache_enabled:
                # Create cache key
                cache_key = f"response:{_normalize_input(input_text)}"
                
                # Create cache value
                cache_value = {
                    "output": output_text,
                    "run_id": state.get("run_id"),
                    "timestamp": time.time(),
                    "execution_time": state.get("execution_time")
                }
                
                # Add sources if available
                if "sources" in state:
                    cache_value["sources"] = state["sources"]
                
                # Store in cache
                await cache_service.set(
                    key=cache_key,
                    value=cache_value,
                    ttl_seconds=cache_ttl_seconds
                )
            
            # Add to history
            state["history"].append({
                "node": "memory_store",
                "conversation_id": conversation_id,
                "timestamp": time.time()
            })
            
            logger.info(f"Memory storage complete")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in memory store node: {str(e)}")
            state["error"] = str(e)
            return state
    
    def _format_intermediate_steps(steps: List[Any]) -> List[Dict[str, Any]]:
        """Format intermediate steps for storage."""
        formatted_steps = []
        
        for step in steps:
            if isinstance(step, tuple) and len(step) == 2:
                action, observation = step
                
                formatted_step = {
                    "action": str(action),
                    "observation": str(observation)
                }
                
                # Try to extract more details if available
                if hasattr(action, "tool"):
                    formatted_step["tool"] = action.tool
                
                if hasattr(action, "tool_input"):
                    formatted_step["tool_input"] = action.tool_input
                
                formatted_steps.append(formatted_step)
            else:
                formatted_steps.append({"step": str(step)})
        
        return formatted_steps
    
    def _normalize_input(input_text: str) -> str:
        """
        Normalize input text for caching.
        
        Args:
            input_text: Input text
            
        Returns:
            Normalized input text
        """
        import re
        
        # Convert to lowercase
        normalized = input_text.lower()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # Remove punctuation
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        return normalized
    
    return node_fn
