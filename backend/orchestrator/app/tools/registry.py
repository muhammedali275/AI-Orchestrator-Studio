"""
Tool Registry - Dynamic tool registration and management.

Loads tools from configuration - no hard-coded tool instances.
"""

import logging
from typing import Dict, List, Optional, Any
from .base import BaseTool
from .http_tool import HttpTool
from .web_search_tool import WebSearchTool
from .code_executor_tool import CodeExecutorTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Registry for managing available tools.
    
    Supports dynamic tool registration from configuration.
    """
    
    # Map of tool types to classes
    TOOL_CLASSES = {
        "http": HttpTool,
        "http_request": HttpTool,  # Alias for http
        "web_search": WebSearchTool,
        "code_executor": CodeExecutorTool,
    }
    
    def __init__(self):
        """Initialize tool registry."""
        self._tools: Dict[str, BaseTool] = {}
    
    def register_tool(self, tool: BaseTool) -> None:
        """
        Register a tool instance.
        
        Args:
            tool: Tool instance to register
        """
        self._tools[tool.name] = tool
        logger.info(f"[ToolRegistry] Registered tool: {tool.name}")
    
    def register_from_config(self, config: Dict[str, Any]) -> None:
        """
        Register tool from configuration.
        
        Args:
            config: Tool configuration with 'type', 'name', and 'config' fields
        """
        tool_type = config.get("type")
        tool_name = config.get("name")
        tool_config = config.get("config", {})
        
        if not tool_type or not tool_name:
            logger.error("[ToolRegistry] Invalid tool config: missing type or name")
            return
        
        tool_class = self.TOOL_CLASSES.get(tool_type)
        if not tool_class:
            logger.error(f"[ToolRegistry] Unknown tool type: {tool_type}")
            return
        
        try:
            tool = tool_class(name=tool_name, config=tool_config)
            self.register_tool(tool)
        except Exception as e:
            logger.error(f"[ToolRegistry] Failed to create tool {tool_name}: {str(e)}")
    
    def register_from_config_list(self, configs: List[Dict[str, Any]]) -> None:
        """
        Register multiple tools from configuration list.
        
        Args:
            configs: List of tool configurations
        """
        for config in configs:
            self.register_from_config(config)
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        Get tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool instance or None if not found
        """
        return self._tools.get(name)
    
    def list_tools(self) -> List[str]:
        """
        List all registered tool names.
        
        Returns:
            List of tool names
        """
        return list(self._tools.keys())
    
    def get_all_tools(self) -> Dict[str, BaseTool]:
        """
        Get all registered tools.
        
        Returns:
            Dictionary of tool name to tool instance
        """
        return self._tools.copy()
    
    def get_schemas(self) -> List[Dict[str, Any]]:
        """
        Get schemas for all registered tools.
        
        Returns:
            List of tool schemas for LLM function calling
        """
        return [tool.get_schema() for tool in self._tools.values()]
    
    def unregister_tool(self, name: str) -> bool:
        """
        Unregister a tool.
        
        Args:
            name: Tool name
            
        Returns:
            True if tool was unregistered, False if not found
        """
        if name in self._tools:
            del self._tools[name]
            logger.info(f"[ToolRegistry] Unregistered tool: {name}")
            return True
        return False
    
    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()
        logger.info("[ToolRegistry] Cleared all tools")
    
    def __len__(self) -> int:
        """Get number of registered tools."""
        return len(self._tools)
    
    def __contains__(self, name: str) -> bool:
        """Check if tool is registered."""
        return name in self._tools
