"""
Topology API routes for AIpanel.

Implements endpoints for managing orchestration topology.
"""

import logging
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db.session import get_db
from ..security import get_current_user, User, verify_scope
from ..orchestrator.executor import get_topology_config, update_topology_config

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/topology", tags=["topology"])


class TopologyNode(BaseModel):
    """Topology node model."""
    id: str = Field(..., description="Node identifier")
    type: str = Field(..., description="Node type")
    data: Dict[str, Any] = Field(default_factory=dict, description="Node data")


class TopologyEdge(BaseModel):
    """Topology edge model."""
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    label: Optional[str] = Field(None, description="Edge label")


class TopologyConfig(BaseModel):
    """Topology configuration model."""
    nodes: List[TopologyNode] = Field(..., description="Nodes in topology")
    edges: List[TopologyEdge] = Field(..., description="Edges in topology")


@router.get("", response_model=TopologyConfig)
async def get_topology(
    agent: str = Query(settings.DEFAULT_AGENT_NAME, description="Agent name"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> TopologyConfig:
    """
    Get topology configuration.
    
    Args:
        agent: Agent name
        user: Authenticated user
        db: Database session
        
    Returns:
        Topology configuration
    """
    logger.info(f"[API:Topology] Get topology for agent: {agent}")
    
    try:
        # Get topology
        topology = await get_topology_config(agent_name=agent, db=db)
        
        return TopologyConfig(**topology)
        
    except Exception as e:
        logger.error(f"[API:Topology] Error getting topology: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting topology: {str(e)}"
        )


@router.post("", response_model=Dict[str, Any])
async def update_topology(
    topology: TopologyConfig,
    agent: str = Query(settings.DEFAULT_AGENT_NAME, description="Agent name"),
    user: User = Depends(verify_scope(["admin"])),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Update topology configuration.
    
    Args:
        topology: Topology configuration
        agent: Agent name
        user: Authenticated user with admin scope
        db: Database session
        
    Returns:
        Success status
    """
    logger.info(f"[API:Topology] Update topology for agent: {agent}")
    
    try:
        # Update topology
        success = await update_topology_config(
            topology=topology.dict(),
            agent_name=agent,
            db=db
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to update topology"
            )
        
        return {
            "success": True,
            "message": f"Topology updated for agent: {agent}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API:Topology] Error updating topology: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error updating topology: {str(e)}"
        )


@router.get("/agents", response_model=List[Dict[str, Any]])
async def get_topology_agents(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get agents with topology configuration.
    
    Args:
        user: Authenticated user
        db: Database session
        
    Returns:
        List of agents
    """
    from ..db.models import Agent
    
    logger.info("[API:Topology] Get agents with topology")
    
    try:
        # Query agents
        agents = db.query(Agent).all()
        
        # Filter to agents with router_config
        agents_with_topology = [
            {
                "id": agent.id,
                "name": agent.name,
                "description": agent.description,
                "has_topology": agent.router_config is not None
            }
            for agent in agents
        ]
        
        return agents_with_topology
        
    except Exception as e:
        logger.error(f"[API:Topology] Error getting agents: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting agents: {str(e)}"
        )


@router.post("/execute", response_model=Dict[str, Any])
async def execute_topology(
    request: Dict[str, Any],
    agent: str = Query(settings.DEFAULT_AGENT_NAME, description="Agent name"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Execute topology with custom input.
    
    Args:
        request: Execution request
        agent: Agent name
        user: Authenticated user
        db: Database session
        
    Returns:
        Execution result
    """
    logger.info(f"[API:Topology] Execute topology for agent: {agent}")
    
    try:
        # Get user input
        user_input = request.get("input", "")
        if not user_input:
            raise HTTPException(
                status_code=400,
                detail="Input is required"
            )
        
        # Execute flow
        from ..orchestrator.executor import run_flow
        
        result = await run_flow(
            user_input=user_input,
            agent_name=agent,
            user_id=user.username,
            db=db
        )
        
        return {
            "success": True,
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API:Topology] Error executing topology: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error executing topology: {str(e)}"
        )
