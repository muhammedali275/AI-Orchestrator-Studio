"""
Configuration Management API.

Provides endpoints for persisting GUI configuration changes to files.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

from ..config import get_settings, Settings, clear_settings_cache
from ..services.config_writer import ConfigWriter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/config", tags=["configuration"])

# Initialize config writer
config_writer = ConfigWriter()


class EnvConfigUpdate(BaseModel):
    """Model for environment variable updates."""
    variables: Dict[str, str] = Field(..., description="Environment variables to update")


class AgentConfig(BaseModel):
    """Model for agent configuration."""
    name: str
    url: str
    auth_token: Optional[str] = None
    timeout_seconds: int = 30
    enabled: bool = True
    metadata: Dict[str, Any] = {}


class ToolConfig(BaseModel):
    """Model for tool configuration."""
    name: str
    type: str
    config: Dict[str, Any] = {}
    enabled: bool = True
    description: Optional[str] = None


class DataSourceConfig(BaseModel):
    """Model for datasource configuration."""
    name: str
    type: str
    url: str
    auth_token: Optional[str] = None
    timeout_seconds: int = 30
    enabled: bool = True
    config: Dict[str, Any] = {}


@router.post("/env")
async def update_env_config(
    config: EnvConfigUpdate,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Update .env file with new configuration.
    
    This endpoint persists GUI changes to the .env file.
    """
    try:
        # Backup existing config
        config_writer.backup_config(".env")
        
        # Write new config
        success = config_writer.write_env_file(config.variables)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to write .env file")
        
        # Clear settings cache to reload new values
        clear_settings_cache()
        
        return {
            "success": True,
            "message": f"Successfully updated {len(config.variables)} environment variables",
            "variables_updated": list(config.variables.keys())
        }
        
    except Exception as e:
        logger.error(f"Error updating .env config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents")
async def update_agents_config(
    agents: List[AgentConfig],
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Update agents.json configuration file.
    
    This endpoint persists agent configurations from GUI.
    """
    try:
        # Backup existing config
        config_writer.backup_config("agents.json")
        
        # Convert to dict format
        agents_list = [agent.dict() for agent in agents]
        
        # Write new config
        success = config_writer.write_agents_config(agents_list)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to write agents.json")
        
        # Clear settings cache
        clear_settings_cache()
        
        return {
            "success": True,
            "message": f"Successfully updated {len(agents)} agent configurations",
            "agents": [agent.name for agent in agents]
        }
        
    except Exception as e:
        logger.error(f"Error updating agents config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/datasources")
async def update_datasources_config(
    datasources: List[DataSourceConfig],
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Update datasources.json configuration file.
    
    This endpoint persists datasource configurations from GUI.
    """
    try:
        # Backup existing config
        config_writer.backup_config("datasources.json")
        
        # Convert to dict format
        datasources_list = [ds.dict() for ds in datasources]
        
        # Write new config
        success = config_writer.write_datasources_config(datasources_list)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to write datasources.json")
        
        # Clear settings cache
        clear_settings_cache()
        
        return {
            "success": True,
            "message": f"Successfully updated {len(datasources)} datasource configurations",
            "datasources": [ds.name for ds in datasources]
        }
        
    except Exception as e:
        logger.error(f"Error updating datasources config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tools")
async def update_tools_config(
    tools: List[ToolConfig],
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Update tools.json configuration file.
    
    This endpoint persists tool configurations from GUI.
    """
    try:
        # Backup existing config
        config_writer.backup_config("tools.json")
        
        # Convert to dict format
        tools_list = [tool.dict() for tool in tools]
        
        # Write new config
        success = config_writer.write_tools_config(tools_list)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to write tools.json")
        
        # Clear settings cache
        clear_settings_cache()
        
        return {
            "success": True,
            "message": f"Successfully updated {len(tools)} tool configurations",
            "tools": [tool.name for tool in tools]
        }
        
    except Exception as e:
        logger.error(f"Error updating tools config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents")
async def get_agents_config(
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """Get current agents configuration."""
    try:
        config = config_writer.read_json_config("agents.json")
        
        if config is None:
            return {"agents": []}
        
        return config
        
    except Exception as e:
        logger.error(f"Error reading agents config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasources")
async def get_datasources_config(
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """Get current datasources configuration."""
    try:
        config = config_writer.read_json_config("datasources.json")
        
        if config is None:
            return {"datasources": []}
        
        return config
        
    except Exception as e:
        logger.error(f"Error reading datasources config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools")
async def get_tools_config(
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """Get current tools configuration."""
    try:
        config = config_writer.read_json_config("tools.json")
        
        if config is None:
            return {"tools": []}
        
        return config
        
    except Exception as e:
        logger.error(f"Error reading tools config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reload")
async def reload_configuration() -> Dict[str, Any]:
    """
    Reload configuration from files.
    
    Clears the settings cache and forces a reload from disk.
    """
    try:
        clear_settings_cache()
        
        # Get fresh settings
        new_settings = get_settings()
        
        return {
            "success": True,
            "message": "Configuration reloaded successfully",
            "agents_count": len(new_settings.external_agents),
            "datasources_count": len(new_settings.datasources),
            "tools_count": len(new_settings.tools)
        }
        
    except Exception as e:
        logger.error(f"Error reloading configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
