"""
LLM Agent Node - Executes an LLM agent to handle the user request.

Uses agent_registry to get the appropriate agent.
"""

import logging
from typing import Dict, Any, Callable, List

from ...agent.agent_registry import AgentRegistry
from ...planner_router.planner_registry import PlannerRegistry
from ...planner_router.router_registry import RouterRegistry
from ...tools.tool_registry import ToolRegistry
from ...memory_cache.memory_service import MemoryService
from ...memory_cache.cache_service import CacheService
from ...config.config_service import ConfigService

logger = logging.getLogger(__name__)


def llm_agent_node(
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
    Create LLM agent node.
    
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
    # Get agent name from config
    agent_name = config.get("agent_name", "default_agent")
    
    # Get intent-to-agent mapping
    intent_agent_map = config.get("intent_agent_map", {})
    
    # Get max iterations
    max_iterations = config.get("max_iterations", 10)
    
    async def node_fn(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        LLM agent node function.
        
        Args:
            state: Current state
            
        Returns:
            Updated state
        """
        try:
            logger.info(f"Executing LLM agent: {state.get('run_id')}")
            
            # Get input
            input_text = state.get("input", "")
            
            # Get intent
            intent = state.get("intent", "unknown")
            
            # Determine agent to use based on intent
            selected_agent_name = intent_agent_map.get(intent, agent_name)
            
            # Get agent
            agent = agent_registry.get_agent(selected_agent_name)
            if not agent:
                logger.error(f"Agent not found: {selected_agent_name}")
                state["error"] = f"Agent not found: {selected_agent_name}"
                return state
            
            # Get conversation history
            conversation_id = state.get("conversation_id")
            messages = []
            
            if conversation_id:
                # Get messages from memory service
                history_messages = await memory_service.get_messages(
                    conversation_id=conversation_id,
                    max_messages=10  # Limit to last 10 messages
                )
                
                # Convert to LangChain format
                for message in history_messages[:-1]:  # Exclude the last message (current input)
                    messages.append({
                        "role": message.role,
                        "content": message.content
                    })
            
            # Prepare agent input
            agent_input = {
                "input": input_text,
                "chat_history": messages
            }
            
            # Add plan if available
            if "plan" in state:
                agent_input["plan"] = state["plan"]
            
            # Execute agent
            result = await agent.ainvoke(agent_input)
            
            # Update state
            state["output"] = result.get("output", "")
            state["intermediate_steps"] = result.get("intermediate_steps", [])
            
            # Add to history
            state["history"].append({
                "node": "llm_agent",
                "agent": selected_agent_name,
                "output": state["output"],
                "intermediate_steps": _format_intermediate_steps(state["intermediate_steps"])
            })
            
            logger.info(f"Agent execution complete")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in LLM agent node: {str(e)}")
            state["error"] = str(e)
            return state
    
    def _format_intermediate_steps(steps: List[Any]) -> List[Dict[str, Any]]:
        """Format intermediate steps for logging."""
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
    
    return node_fn
