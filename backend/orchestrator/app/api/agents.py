"""
Agents API - Endpoints for external agent configuration and testing.

Provides CRUD operations for agent settings and connectivity testing.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from ..config import get_settings, Settings, ExternalAgentConfig, clear_settings_cache
from ..clients.external_agent_client import ExternalAgentClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agents", tags=["agents"])


class AgentConfigModel(BaseModel):
    """Agent configuration model."""
    name: str = Field(..., description="Agent name/identifier")
    url: str = Field(..., description="Agent base URL")
    auth_token: Optional[str] = Field(None, description="Authentication token")
    timeout_seconds: int = Field(default=30, description="Request timeout")
    enabled: bool = Field(default=True, description="Whether agent is enabled")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AgentTestRequest(BaseModel):
    """Agent test request model."""
    payload: Dict[str, Any] = Field(default_factory=dict, description="Test payload")
    endpoint: str = Field(default="/health", description="Endpoint to test")


@router.get("", response_model=List[AgentConfigModel])
async def list_agents(settings: Settings = Depends(get_settings)) -> List[AgentConfigModel]:
    """
    List all configured external agents.
    
    Returns:
        List of agent configurations
    """
    agents = []
    for name, config in settings.external_agents.items():
        agents.append(AgentConfigModel(
            name=config.name,
            url=config.url,
            auth_token=config.auth_token,
            timeout_seconds=config.timeout_seconds,
            enabled=config.enabled,
            metadata=config.metadata
        ))
    
    return agents


@router.get("/{name}", response_model=AgentConfigModel)
async def get_agent(
    name: str,
    settings: Settings = Depends(get_settings)
) -> AgentConfigModel:
    """
    Get a specific agent configuration.
    
    Args:
        name: Agent name
        
    Returns:
        Agent configuration
    """
    agent_config = settings.get_agent(name)
    
    if not agent_config:
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{name}' not found"
        )
    
    return AgentConfigModel(
        name=agent_config.name,
        url=agent_config.url,
        auth_token=agent_config.auth_token,
        timeout_seconds=agent_config.timeout_seconds,
        enabled=agent_config.enabled,
        metadata=agent_config.metadata
    )


@router.post("", status_code=201)
async def create_agent(
    agent: AgentConfigModel,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Register a new external agent.
    
    Args:
        agent: Agent configuration
        
    Returns:
        Success message and created agent
    """
    # Check if agent already exists
    if settings.get_agent(agent.name):
        raise HTTPException(
            status_code=409,
            detail=f"Agent '{agent.name}' already exists"
        )
    
    try:
        # Create agent config
        agent_config = ExternalAgentConfig(
            name=agent.name,
            url=agent.url,
            auth_token=agent.auth_token,
            timeout_seconds=agent.timeout_seconds,
            enabled=agent.enabled,
            metadata=agent.metadata
        )
        
        # Add to settings
        settings.add_agent(agent_config)
        
        logger.info(f"[Agents API] Created agent: {agent.name}")
        
        return {
            "success": True,
            "message": f"Agent '{agent.name}' created successfully",
            "agent": agent.dict()
        }
        
    except Exception as e:
        logger.error(f"[Agents API] Error creating agent: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create agent: {str(e)}"
        )


@router.put("/{name}")
async def update_agent(
    name: str,
    agent: AgentConfigModel,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Update an existing agent configuration.
    
    Args:
        name: Agent name
        agent: Updated agent configuration
        
    Returns:
        Success message and updated agent
    """
    # Check if agent exists
    if not settings.get_agent(name):
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{name}' not found"
        )
    
    try:
        # Create updated agent config
        agent_config = ExternalAgentConfig(
            name=agent.name,
            url=agent.url,
            auth_token=agent.auth_token,
            timeout_seconds=agent.timeout_seconds,
            enabled=agent.enabled,
            metadata=agent.metadata
        )
        
        # Update in settings
        settings.add_agent(agent_config)
        
        logger.info(f"[Agents API] Updated agent: {name}")
        
        return {
            "success": True,
            "message": f"Agent '{name}' updated successfully",
            "agent": agent.dict()
        }
        
    except Exception as e:
        logger.error(f"[Agents API] Error updating agent: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update agent: {str(e)}"
        )


@router.delete("/{name}")
async def delete_agent(
    name: str,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Remove an agent configuration.
    
    Args:
        name: Agent name
        
    Returns:
        Success message
    """
    if not settings.remove_agent(name):
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{name}' not found"
        )
    
    logger.info(f"[Agents API] Deleted agent: {name}")
    
    return {
        "success": True,
        "message": f"Agent '{name}' deleted successfully"
    }


@router.post("/{name}/test")
async def test_agent(
    name: str,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Test connectivity to a specific agent.
    
    Args:
        name: Agent name
        
    Returns:
        Test result with status and details
    """
    try:
        client = ExternalAgentClient(settings)
        result = await client.test_agent(name)
        await client.close()
        
        logger.info(f"[Agents API] Test result for {name}: {result['success']}")
        
        return result
        
    except Exception as e:
        logger.error(f"[Agents API] Test failed for {name}: {str(e)}")
        return {
            "success": False,
            "agent": name,
            "error": str(e),
            "message": "Test failed with exception"
        }


@router.post("/{name}/call")
async def call_agent(
    name: str,
    payload: Dict[str, Any],
    endpoint: str = "/execute",
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Call a specific agent endpoint.
    
    Args:
        name: Agent name
        payload: Request payload
        endpoint: API endpoint to call
        
    Returns:
        Agent response
    """
    try:
        client = ExternalAgentClient(settings)
        result = await client.call_agent(name, payload, endpoint)
        await client.close()
        
        return result
        
    except Exception as e:
        logger.error(f"[Agents API] Call failed for {name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to call agent: {str(e)}"
        )


@router.get("/health/all")
async def check_all_agents_health(settings: Settings = Depends(get_settings)) -> Dict[str, Any]:
    """
    Check health of all configured agents.
    
    Returns:
        Health status for all agents
    """
    client = ExternalAgentClient(settings)
    results = {}
    
    for name in settings.external_agents.keys():
        try:
            result = await client.test_agent(name)
            results[name] = {
                "healthy": result["success"],
                "message": result.get("message", ""),
                "url": result.get("url", "")
            }
        except Exception as e:
            results[name] = {
                "healthy": False,
                "error": str(e)
            }
    
    await client.close()
    
    return {
        "agents": results,
        "total": len(results),
        "healthy": sum(1 for r in results.values() if r.get("healthy", False))
    }
