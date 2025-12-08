"""
Tools API - Endpoints for tool configuration and management.

Provides CRUD operations for tool settings and testing.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from ..config import get_settings, Settings, ToolConfig, clear_settings_cache
from ..tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tools", tags=["tools"])


class ToolConfigModel(BaseModel):
    """Tool configuration model."""
    name: str = Field(..., description="Tool name/identifier")
    type: str = Field(..., description="Tool type (http_request, web_search, code_executor, etc.)")
    config: Dict[str, Any] = Field(default_factory=dict, description="Tool-specific configuration")
    enabled: bool = Field(default=True, description="Whether tool is enabled")
    description: Optional[str] = Field(None, description="Tool description")


@router.get("", response_model=List[ToolConfigModel])
async def list_tools(settings: Settings = Depends(get_settings)) -> List[ToolConfigModel]:
    """
    List all configured tools.
    
    Returns:
        List of tool configurations
    """
    tools = []
    for name, config in settings.tools.items():
        tools.append(ToolConfigModel(
            name=config.name,
            type=config.type,
            config=config.config,
            enabled=config.enabled,
            description=config.description
        ))
    
    return tools


@router.get("/{name}", response_model=ToolConfigModel)
async def get_tool(
    name: str,
    settings: Settings = Depends(get_settings)
) -> ToolConfigModel:
    """
    Get a specific tool configuration.
    
    Args:
        name: Tool name
        
    Returns:
        Tool configuration
    """
    tool_config = settings.get_tool(name)
    
    if not tool_config:
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{name}' not found"
        )
    
    return ToolConfigModel(
        name=tool_config.name,
        type=tool_config.type,
        config=tool_config.config,
        enabled=tool_config.enabled,
        description=tool_config.description
    )


@router.post("", status_code=201)
async def create_tool(
    tool: ToolConfigModel,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Register a new tool.
    
    Args:
        tool: Tool configuration
        
    Returns:
        Success message and created tool
    """
    # Check if tool already exists
    if settings.get_tool(tool.name):
        raise HTTPException(
            status_code=409,
            detail=f"Tool '{tool.name}' already exists"
        )
    
    try:
        # Create tool config
        tool_config = ToolConfig(
            name=tool.name,
            type=tool.type,
            config=tool.config,
            enabled=tool.enabled,
            description=tool.description
        )
        
        # Add to settings
        settings.add_tool(tool_config)
        
        logger.info(f"[Tools API] Created tool: {tool.name}")
        
        return {
            "success": True,
            "message": f"Tool '{tool.name}' created successfully",
            "tool": tool.dict()
        }
        
    except Exception as e:
        logger.error(f"[Tools API] Error creating tool: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create tool: {str(e)}"
        )


@router.put("/{name}")
async def update_tool(
    name: str,
    tool: ToolConfigModel,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Update an existing tool configuration.
    
    Args:
        name: Tool name
        tool: Updated tool configuration
        
    Returns:
        Success message and updated tool
    """
    # Check if tool exists
    if not settings.get_tool(name):
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{name}' not found"
        )
    
    try:
        # Create updated tool config
        tool_config = ToolConfig(
            name=tool.name,
            type=tool.type,
            config=tool.config,
            enabled=tool.enabled,
            description=tool.description
        )
        
        # Update in settings
        settings.add_tool(tool_config)
        
        logger.info(f"[Tools API] Updated tool: {name}")
        
        return {
            "success": True,
            "message": f"Tool '{name}' updated successfully",
            "tool": tool.dict()
        }
        
    except Exception as e:
        logger.error(f"[Tools API] Error updating tool: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update tool: {str(e)}"
        )


@router.delete("/{name}")
async def delete_tool(
    name: str,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Remove a tool configuration.
    
    Args:
        name: Tool name
        
    Returns:
        Success message
    """
    if not settings.remove_tool(name):
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{name}' not found"
        )
    
    logger.info(f"[Tools API] Deleted tool: {name}")
    
    return {
        "success": True,
        "message": f"Tool '{name}' deleted successfully"
    }


@router.post("/{name}/test")
async def test_tool(
    name: str,
    test_payload: Optional[Dict[str, Any]] = None,
    skip_connectivity: bool = False,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Test a specific tool.
    
    Args:
        name: Tool name
        test_payload: Optional test payload
        skip_connectivity: If True, only validate configuration without testing connectivity
        
    Returns:
        Test result with detailed status
    """
    tool_config = settings.get_tool(name)
    
    if not tool_config:
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{name}' not found"
        )
    
    # Configuration validation result
    result = {
        "tool": name,
        "type": tool_config.type,
        "config_valid": True,
        "config_saved": True,
        "enabled": tool_config.enabled
    }
    
    if not tool_config.enabled:
        result.update({
            "success": False,
            "connectivity_tested": False,
            "connectivity_status": "skipped",
            "message": "Tool is disabled. Enable it to test connectivity.",
            "warning": "Tool configuration is saved but tool is disabled"
        })
        return result
    
    try:
        # Create tool registry and register tool
        registry = ToolRegistry()
        registry.register_from_config(tool_config.dict())
        
        # Get the tool
        tool = registry.get_tool(name)
        
        if not tool:
            result.update({
                "success": False,
                "config_valid": False,
                "connectivity_tested": False,
                "connectivity_status": "failed",
                "message": "Tool could not be instantiated from configuration",
                "error": "Invalid tool configuration"
            })
            return result
        
        # If skip_connectivity is True, return success after config validation
        if skip_connectivity:
            result.update({
                "success": True,
                "connectivity_tested": False,
                "connectivity_status": "skipped",
                "message": "Tool configuration is valid. Connectivity test skipped.",
                "schema": tool.get_schema() if hasattr(tool, 'get_schema') else None
            })
            return result
        
        # For HTTP tools, test connectivity
        if tool_config.type == "http_request" and "base_url" in tool_config.config:
            import httpx
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    url = tool_config.config["base_url"]
                    response = await client.get(url)
                    
                    is_reachable = response.status_code < 400
                    result.update({
                        "success": is_reachable,
                        "connectivity_tested": True,
                        "connectivity_status": "reachable" if is_reachable else "unreachable",
                        "status_code": response.status_code,
                        "endpoint_url": url,
                        "message": f"Tool endpoint is {'reachable' if is_reachable else 'unreachable'} (HTTP {response.status_code})"
                    })
                    return result
                    
            except httpx.ConnectError as e:
                result.update({
                    "success": False,
                    "connectivity_tested": True,
                    "connectivity_status": "unreachable",
                    "endpoint_url": tool_config.config.get("base_url"),
                    "error": "Connection refused",
                    "error_detail": str(e),
                    "message": "Cannot connect to tool endpoint. The target service may not be running.",
                    "suggestion": "Ensure the tool's target service is running and accessible, or use 'skip_connectivity=true' to save without testing."
                })
                return result
                
            except httpx.TimeoutException as e:
                result.update({
                    "success": False,
                    "connectivity_tested": True,
                    "connectivity_status": "timeout",
                    "endpoint_url": tool_config.config.get("base_url"),
                    "error": "Connection timeout",
                    "error_detail": str(e),
                    "message": "Tool endpoint connection timed out after 5 seconds.",
                    "suggestion": "Check if the service is running or increase timeout in tool configuration."
                })
                return result
                
            except Exception as e:
                result.update({
                    "success": False,
                    "connectivity_tested": True,
                    "connectivity_status": "error",
                    "endpoint_url": tool_config.config.get("base_url"),
                    "error": type(e).__name__,
                    "error_detail": str(e),
                    "message": f"Failed to connect to tool endpoint: {str(e)}",
                    "suggestion": "Verify the endpoint URL and network connectivity."
                })
                return result
        
        # For other tools, just verify configuration
        result.update({
            "success": True,
            "connectivity_tested": False,
            "connectivity_status": "not_applicable",
            "message": f"Tool configuration is valid. Connectivity testing not available for '{tool_config.type}' tools.",
            "schema": tool.get_schema() if hasattr(tool, 'get_schema') else None
        })
        return result
        
    except Exception as e:
        logger.error(f"[Tools API] Test failed for {name}: {str(e)}")
        result.update({
            "success": False,
            "config_valid": False,
            "connectivity_tested": False,
            "connectivity_status": "error",
            "error": type(e).__name__,
            "error_detail": str(e),
            "message": f"Tool test failed: {str(e)}"
        })
        return result


@router.get("/registry/schemas")
async def get_tool_schemas(settings: Settings = Depends(get_settings)) -> Dict[str, Any]:
    """
    Get schemas for all registered tools.
    
    Returns:
        Tool schemas for LLM function calling
    """
    try:
        registry = ToolRegistry()
        
        # Register all tools from settings
        for tool_config in settings.tools.values():
            if tool_config.enabled:
                registry.register_from_config(tool_config.dict())
        
        schemas = registry.get_tool_schemas()
        
        return {
            "success": True,
            "count": len(schemas),
            "schemas": schemas
        }
        
    except Exception as e:
        logger.error(f"[Tools API] Error getting schemas: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get tool schemas: {str(e)}"
        )


@router.get("/types/available")
async def get_available_tool_types() -> Dict[str, Any]:
    """
    Get list of available tool types.
    
    Returns:
        List of supported tool types
    """
    return {
        "tool_types": [
            {
                "type": "http_request",
                "description": "Make HTTP requests to external APIs",
                "required_config": ["base_url"],
                "optional_config": ["auth_token", "timeout", "headers"]
            },
            {
                "type": "web_search",
                "description": "Search the web for information",
                "required_config": ["api_key", "endpoint"],
                "optional_config": ["provider", "max_results", "timeout"]
            },
            {
                "type": "code_executor",
                "description": "Execute code in a sandboxed environment",
                "required_config": [],
                "optional_config": ["timeout", "max_memory", "allowed_languages"]
            }
        ]
    }
