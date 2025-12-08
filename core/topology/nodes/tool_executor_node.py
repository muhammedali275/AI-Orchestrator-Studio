"""
Tool Executor Node - Executes tools based on agent output.

Uses tool_registry to get and execute tools.
"""

import logging
import json
from typing import Dict, Any, Callable, List, Optional, Union

from ...agent.agent_registry import AgentRegistry
from ...planner_router.planner_registry import PlannerRegistry
from ...planner_router.router_registry import RouterRegistry
from ...tools.tool_registry import ToolRegistry
from ...memory_cache.memory_service import MemoryService
from ...memory_cache.cache_service import CacheService
from ...config.config_service import ConfigService

logger = logging.getLogger(__name__)


def tool_executor_node(
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
    Create tool executor node.
    
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
    # Get max iterations
    max_iterations = config.get("max_iterations", 5)
    
    # Get allowed tools
    allowed_tools = config.get("allowed_tools", [])
    
    # Get timeout
    timeout_seconds = config.get("timeout_seconds", 30)
    
    async def node_fn(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tool executor node function.
        
        Args:
            state: Current state
            
        Returns:
            Updated state
        """
        try:
            logger.info(f"Executing tools: {state.get('run_id')}")
            
            # Check if there are tool calls to execute
            tool_calls = _extract_tool_calls(state)
            if not tool_calls:
                logger.info("No tool calls to execute")
                return state
            
            # Initialize tool results
            if "tool_results" not in state:
                state["tool_results"] = []
            
            # Execute tools
            for i, tool_call in enumerate(tool_calls):
                if i >= max_iterations:
                    logger.warning(f"Reached maximum tool iterations ({max_iterations})")
                    break
                
                # Get tool name and input
                tool_name = tool_call.get("name")
                tool_input = tool_call.get("input", {})
                
                # Check if tool is allowed
                if allowed_tools and tool_name not in allowed_tools:
                    logger.warning(f"Tool not allowed: {tool_name}")
                    state["tool_results"].append({
                        "tool": tool_name,
                        "input": tool_input,
                        "error": f"Tool not allowed: {tool_name}"
                    })
                    continue
                
                # Get tool
                tool = tool_registry.get_tool(tool_name)
                if not tool:
                    logger.error(f"Tool not found: {tool_name}")
                    state["tool_results"].append({
                        "tool": tool_name,
                        "input": tool_input,
                        "error": f"Tool not found: {tool_name}"
                    })
                    continue
                
                try:
                    # Execute tool
                    logger.info(f"Executing tool: {tool_name}")
                    result = await tool.ainvoke(tool_input)
                    
                    # Add result to state
                    state["tool_results"].append({
                        "tool": tool_name,
                        "input": tool_input,
                        "output": result
                    })
                    
                    logger.info(f"Tool execution complete: {tool_name}")
                    
                except Exception as e:
                    logger.error(f"Error executing tool {tool_name}: {str(e)}")
                    state["tool_results"].append({
                        "tool": tool_name,
                        "input": tool_input,
                        "error": str(e)
                    })
            
            # Add to history
            state["history"].append({
                "node": "tool_executor",
                "tool_results": state["tool_results"]
            })
            
            # Update output with tool results if needed
            if config.get("include_results_in_output", False):
                state["output"] = _format_output_with_results(state["output"], state["tool_results"])
            
            logger.info(f"Tool execution complete")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in tool executor node: {str(e)}")
            state["error"] = str(e)
            return state
    
    def _extract_tool_calls(state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract tool calls from state.
        
        Args:
            state: Current state
            
        Returns:
            List of tool calls
        """
        tool_calls = []
        
        # Check intermediate steps
        intermediate_steps = state.get("intermediate_steps", [])
        for step in intermediate_steps:
            if isinstance(step, tuple) and len(step) == 2:
                action, _ = step
                
                if hasattr(action, "tool") and hasattr(action, "tool_input"):
                    tool_calls.append({
                        "name": action.tool,
                        "input": action.tool_input
                    })
        
        # Check for tool calls in output
        output = state.get("output", "")
        if output:
            # Try to extract JSON tool calls
            tool_calls_from_output = _extract_tool_calls_from_output(output)
            if tool_calls_from_output:
                tool_calls.extend(tool_calls_from_output)
        
        return tool_calls
    
    def _extract_tool_calls_from_output(output: str) -> List[Dict[str, Any]]:
        """
        Extract tool calls from output text.
        
        Args:
            output: Output text
            
        Returns:
            List of tool calls
        """
        tool_calls = []
        
        # Try to find JSON blocks
        import re
        json_blocks = re.findall(r'```json\n(.*?)\n```', output, re.DOTALL)
        
        for block in json_blocks:
            try:
                data = json.loads(block)
                
                # Check if it's a tool call
                if isinstance(data, dict) and "name" in data and "input" in data:
                    tool_calls.append(data)
                elif isinstance(data, dict) and "tool" in data and "input" in data:
                    tool_calls.append({
                        "name": data["tool"],
                        "input": data["input"]
                    })
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "name" in item and "input" in item:
                            tool_calls.append(item)
                        elif isinstance(item, dict) and "tool" in item and "input" in item:
                            tool_calls.append({
                                "name": item["tool"],
                                "input": item["input"]
                            })
            except Exception as e:
                logger.warning(f"Error parsing JSON block: {str(e)}")
        
        return tool_calls
    
    def _format_output_with_results(output: str, tool_results: List[Dict[str, Any]]) -> str:
        """
        Format output with tool results.
        
        Args:
            output: Original output
            tool_results: Tool results
            
        Returns:
            Formatted output
        """
        if not tool_results:
            return output
        
        # Format tool results
        result_text = "\n\nTool Results:\n"
        for i, result in enumerate(tool_results):
            result_text += f"\n{i+1}. Tool: {result['tool']}\n"
            result_text += f"   Input: {json.dumps(result['input'], indent=2)}\n"
            
            if "error" in result:
                result_text += f"   Error: {result['error']}\n"
            else:
                result_text += f"   Output: {json.dumps(result['output'], indent=2)}\n"
        
        return output + result_text
    
    return node_fn
