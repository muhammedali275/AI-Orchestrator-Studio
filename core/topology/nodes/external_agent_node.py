"""
External Agent Node - Calls external agent APIs.

Uses external_agent_client to call external agents.
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


def external_agent_node(
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
    Create external agent node.
    
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
    # Get external agent name from config
    agent_name = config.get("agent_name", "default_external_agent")
    
    # Get intent-to-agent mapping
    intent_agent_map = config.get("intent_agent_map", {})
    
    # Get timeout
    timeout_seconds = config.get("timeout_seconds", 30)
    
    # Get retry configuration
    max_retries = config.get("max_retries", 3)
    retry_delay_seconds = config.get("retry_delay_seconds", 1)
    
    async def node_fn(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        External agent node function.
        
        Args:
            state: Current state
            
        Returns:
            Updated state
        """
        try:
            logger.info(f"Executing external agent: {state.get('run_id')}")
            
            # Get input
            input_text = state.get("input", "")
            
            # Get intent
            intent = state.get("intent", "unknown")
            
            # Determine agent to use based on intent
            selected_agent_name = intent_agent_map.get(intent, agent_name)
            
            # Get external agent configuration
            agent_config = config_service.get_external_agent_config(selected_agent_name)
            if not agent_config:
                logger.error(f"External agent not found: {selected_agent_name}")
                state["error"] = f"External agent not found: {selected_agent_name}"
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
                
                # Convert to format expected by external agent
                for message in history_messages[:-1]:  # Exclude the last message (current input)
                    messages.append({
                        "role": message.role,
                        "content": message.content
                    })
            
            # Prepare request payload
            payload = {
                "input": input_text,
                "conversation_history": messages,
                "metadata": state.get("metadata", {})
            }
            
            # Add plan if available
            if "plan" in state:
                payload["plan"] = state["plan"]
            
            # Call external agent
            import httpx
            import asyncio
            import json
            
            # Get endpoint and API key
            endpoint = agent_config.get("endpoint")
            api_key = agent_config.get("api_key")
            
            # Prepare headers
            headers = {
                "Content-Type": "application/json"
            }
            
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            # Initialize result
            result = None
            
            # Try to call external agent with retries
            for retry in range(max_retries):
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.post(
                            endpoint,
                            json=payload,
                            headers=headers,
                            timeout=timeout_seconds
                        )
                        
                        # Check response
                        if response.status_code == 200:
                            result = response.json()
                            break
                        else:
                            logger.warning(f"External agent returned status code {response.status_code}: {response.text}")
                            
                            if retry < max_retries - 1:
                                # Wait before retrying
                                await asyncio.sleep(retry_delay_seconds)
                            else:
                                # Last retry failed
                                state["error"] = f"External agent returned status code {response.status_code}: {response.text}"
                                return state
                except Exception as e:
                    logger.warning(f"Error calling external agent (retry {retry+1}/{max_retries}): {str(e)}")
                    
                    if retry < max_retries - 1:
                        # Wait before retrying
                        await asyncio.sleep(retry_delay_seconds)
                    else:
                        # Last retry failed
                        state["error"] = f"Error calling external agent: {str(e)}"
                        return state
            
            # Check if we got a result
            if not result:
                state["error"] = "Failed to get response from external agent"
                return state
            
            # Update state
            state["output"] = result.get("output", "")
            
            # Add intermediate steps if available
            if "intermediate_steps" in result:
                state["intermediate_steps"] = result["intermediate_steps"]
            
            # Add to history
            state["history"].append({
                "node": "external_agent",
                "agent": selected_agent_name,
                "output": state["output"]
            })
            
            logger.info(f"External agent execution complete")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in external agent node: {str(e)}")
            state["error"] = str(e)
            return state
    
    return node_fn
