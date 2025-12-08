"""
Configuration API routes for AIpanel.

Implements endpoints for managing configuration.
"""

import logging
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db.session import get_db
from ..security import get_current_user, User, verify_scope
from ..db.models import LLMConnection, Tool, Agent, Credential, DataSource

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/config", tags=["config"])


# LLM Connection models
class LLMConnectionCreate(BaseModel):
    """LLM connection create model."""
    name: str = Field(..., description="Connection name")
    provider: str = Field(..., description="Provider name (openai, anthropic, ollama, etc.)")
    base_url: Optional[str] = Field(None, description="Base URL")
    api_key: Optional[str] = Field(None, description="API key")
    default_model: Optional[str] = Field(None, description="Default model")
    config: Optional[Dict[str, Any]] = Field(None, description="Additional configuration")


class LLMConnectionUpdate(BaseModel):
    """LLM connection update model."""
    name: Optional[str] = Field(None, description="Connection name")
    provider: Optional[str] = Field(None, description="Provider name")
    base_url: Optional[str] = Field(None, description="Base URL")
    api_key: Optional[str] = Field(None, description="API key")
    default_model: Optional[str] = Field(None, description="Default model")
    config: Optional[Dict[str, Any]] = Field(None, description="Additional configuration")


# Tool models
class ToolCreate(BaseModel):
    """Tool create model."""
    name: str = Field(..., description="Tool name")
    type: str = Field(..., description="Tool type")
    description: Optional[str] = Field(None, description="Tool description")
    config: Optional[Dict[str, Any]] = Field(None, description="Tool configuration")


class ToolUpdate(BaseModel):
    """Tool update model."""
    name: Optional[str] = Field(None, description="Tool name")
    type: Optional[str] = Field(None, description="Tool type")
    description: Optional[str] = Field(None, description="Tool description")
    config: Optional[Dict[str, Any]] = Field(None, description="Tool configuration")


# Agent models
class AgentCreate(BaseModel):
    """Agent create model."""
    name: str = Field(..., description="Agent name")
    description: Optional[str] = Field(None, description="Agent description")
    system_prompt: str = Field(..., description="System prompt")
    llm_connection_id: Optional[str] = Field(None, description="LLM connection ID")
    router_config: Optional[Dict[str, Any]] = Field(None, description="Router configuration")
    planner_config: Optional[Dict[str, Any]] = Field(None, description="Planner configuration")
    tool_ids: Optional[List[str]] = Field(None, description="Tool IDs")


class AgentUpdate(BaseModel):
    """Agent update model."""
    name: Optional[str] = Field(None, description="Agent name")
    description: Optional[str] = Field(None, description="Agent description")
    system_prompt: Optional[str] = Field(None, description="System prompt")
    llm_connection_id: Optional[str] = Field(None, description="LLM connection ID")
    router_config: Optional[Dict[str, Any]] = Field(None, description="Router configuration")
    planner_config: Optional[Dict[str, Any]] = Field(None, description="Planner configuration")
    tool_ids: Optional[List[str]] = Field(None, description="Tool IDs")


# Credential models
class CredentialCreate(BaseModel):
    """Credential create model."""
    name: str = Field(..., description="Credential name")
    type: str = Field(..., description="Credential type")
    data: Dict[str, Any] = Field(..., description="Credential data")


class CredentialUpdate(BaseModel):
    """Credential update model."""
    name: Optional[str] = Field(None, description="Credential name")
    type: Optional[str] = Field(None, description="Credential type")
    data: Optional[Dict[str, Any]] = Field(None, description="Credential data")


# Data source models
class DataSourceCreate(BaseModel):
    """Data source create model."""
    name: str = Field(..., description="Data source name")
    type: str = Field(..., description="Data source type")
    url: str = Field(..., description="Data source URL")
    credential_id: Optional[str] = Field(None, description="Credential ID")
    config: Optional[Dict[str, Any]] = Field(None, description="Additional configuration")


class DataSourceUpdate(BaseModel):
    """Data source update model."""
    name: Optional[str] = Field(None, description="Data source name")
    type: Optional[str] = Field(None, description="Data source type")
    url: Optional[str] = Field(None, description="Data source URL")
    credential_id: Optional[str] = Field(None, description="Credential ID")
    config: Optional[Dict[str, Any]] = Field(None, description="Additional configuration")


# LLM Connection endpoints
@router.get("/llm-connections", response_model=List[Dict[str, Any]])
async def get_llm_connections(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get LLM connections.
    
    Args:
        user: Authenticated user
        db: Database session
        
    Returns:
        List of LLM connections
    """
    logger.info("[API:Config] Get LLM connections")
    
    try:
        # Query connections
        connections = db.query(LLMConnection).all()
        
        # Convert to dictionaries (without API keys)
        connection_dicts = []
        for conn in connections:
            conn_dict = conn.to_dict()
            # Remove API key for security
            conn_dict["api_key"] = "********" if conn.api_key else None
            connection_dicts.append(conn_dict)
        
        return connection_dicts
        
    except Exception as e:
        logger.error(f"[API:Config] Error getting LLM connections: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting LLM connections: {str(e)}"
        )


@router.post("/llm-connections", response_model=Dict[str, Any])
async def create_llm_connection(
    connection: LLMConnectionCreate,
    user: User = Depends(verify_scope(["admin"])),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Create LLM connection.
    
    Args:
        connection: LLM connection data
        user: Authenticated user with admin scope
        db: Database session
        
    Returns:
        Created LLM connection
    """
    logger.info(f"[API:Config] Create LLM connection: {connection.name}")
    
    try:
        # Check if name already exists
        existing = db.query(LLMConnection).filter(
            LLMConnection.name == connection.name
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"LLM connection with name '{connection.name}' already exists"
            )
        
        # Create connection
        new_connection = LLMConnection(
            name=connection.name,
            provider=connection.provider,
            base_url=connection.base_url,
            api_key=connection.api_key,
            default_model=connection.default_model,
            config=connection.config
        )
        
        db.add(new_connection)
        db.commit()
        db.refresh(new_connection)
        
        # Return without API key
        result = new_connection.to_dict()
        result["api_key"] = "********" if new_connection.api_key else None
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API:Config] Error creating LLM connection: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating LLM connection: {str(e)}"
        )


@router.get("/llm-connections/{connection_id}", response_model=Dict[str, Any])
async def get_llm_connection(
    connection_id: str = Path(..., description="LLM connection ID"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get LLM connection.
    
    Args:
        connection_id: LLM connection ID
        user: Authenticated user
        db: Database session
        
    Returns:
        LLM connection
    """
    logger.info(f"[API:Config] Get LLM connection: {connection_id}")
    
    try:
        # Query connection
        connection = db.query(LLMConnection).filter(
            LLMConnection.id == connection_id
        ).first()
        
        if not connection:
            raise HTTPException(
                status_code=404,
                detail=f"LLM connection not found: {connection_id}"
            )
        
        # Return without API key
        result = connection.to_dict()
        result["api_key"] = "********" if connection.api_key else None
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API:Config] Error getting LLM connection: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting LLM connection: {str(e)}"
        )


@router.put("/llm-connections/{connection_id}", response_model=Dict[str, Any])
async def update_llm_connection(
    connection: LLMConnectionUpdate,
    connection_id: str = Path(..., description="LLM connection ID"),
    user: User = Depends(verify_scope(["admin"])),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Update LLM connection.
    
    Args:
        connection: LLM connection data
        connection_id: LLM connection ID
        user: Authenticated user with admin scope
        db: Database session
        
    Returns:
        Updated LLM connection
    """
    logger.info(f"[API:Config] Update LLM connection: {connection_id}")
    
    try:
        # Query connection
        db_connection = db.query(LLMConnection).filter(
            LLMConnection.id == connection_id
        ).first()
        
        if not db_connection:
            raise HTTPException(
                status_code=404,
                detail=f"LLM connection not found: {connection_id}"
            )
        
        # Update fields
        if connection.name is not None:
            # Check if name already exists
            existing = db.query(LLMConnection).filter(
                LLMConnection.name == connection.name,
                LLMConnection.id != connection_id
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"LLM connection with name '{connection.name}' already exists"
                )
            
            db_connection.name = connection.name
        
        if connection.provider is not None:
            db_connection.provider = connection.provider
        
        if connection.base_url is not None:
            db_connection.base_url = connection.base_url
        
        if connection.api_key is not None:
            db_connection.api_key = connection.api_key
        
        if connection.default_model is not None:
            db_connection.default_model = connection.default_model
        
        if connection.config is not None:
            db_connection.config = connection.config
        
        db.commit()
        db.refresh(db_connection)
        
        # Return without API key
        result = db_connection.to_dict()
        result["api_key"] = "********" if db_connection.api_key else None
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API:Config] Error updating LLM connection: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error updating LLM connection: {str(e)}"
        )


@router.delete("/llm-connections/{connection_id}", response_model=Dict[str, Any])
async def delete_llm_connection(
    connection_id: str = Path(..., description="LLM connection ID"),
    user: User = Depends(verify_scope(["admin"])),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Delete LLM connection.
    
    Args:
        connection_id: LLM connection ID
        user: Authenticated user with admin scope
        db: Database session
        
    Returns:
        Success status
    """
    logger.info(f"[API:Config] Delete LLM connection: {connection_id}")
    
    try:
        # Query connection
        connection = db.query(LLMConnection).filter(
            LLMConnection.id == connection_id
        ).first()
        
        if not connection:
            raise HTTPException(
                status_code=404,
                detail=f"LLM connection not found: {connection_id}"
            )
        
        # Check if connection is used by agents
        agents = db.query(Agent).filter(
            Agent.llm_connection_id == connection_id
        ).all()
        
        if agents:
            agent_names = [agent.name for agent in agents]
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete LLM connection: used by agents {agent_names}"
            )
        
        # Delete connection
        db.delete(connection)
        db.commit()
        
        return {
            "success": True,
            "message": f"LLM connection deleted: {connection_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API:Config] Error deleting LLM connection: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting LLM connection: {str(e)}"
        )


# Tool endpoints
@router.get("/tools", response_model=List[Dict[str, Any]])
async def get_tools(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get tools.
    
    Args:
        user: Authenticated user
        db: Database session
        
    Returns:
        List of tools
    """
    logger.info("[API:Config] Get tools")
    
    try:
        # Query tools
        tools = db.query(Tool).all()
        
        return [tool.to_dict() for tool in tools]
        
    except Exception as e:
        logger.error(f"[API:Config] Error getting tools: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting tools: {str(e)}"
        )


@router.post("/tools", response_model=Dict[str, Any])
async def create_tool(
    tool: ToolCreate,
    user: User = Depends(verify_scope(["admin"])),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Create tool.
    
    Args:
        tool: Tool data
        user: Authenticated user with admin scope
        db: Database session
        
    Returns:
        Created tool
    """
    logger.info(f"[API:Config] Create tool: {tool.name}")
    
    try:
        # Check if name already exists
        existing = db.query(Tool).filter(
            Tool.name == tool.name
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Tool with name '{tool.name}' already exists"
            )
        
        # Create tool
        new_tool = Tool(
            name=tool.name,
            type=tool.type,
            description=tool.description,
            config=tool.config
        )
        
        db.add(new_tool)
        db.commit()
        db.refresh(new_tool)
        
        return new_tool.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API:Config] Error creating tool: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating tool: {str(e)}"
        )


# Agent endpoints
@router.get("/agents", response_model=List[Dict[str, Any]])
async def get_agents(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get agents.
    
    Args:
        user: Authenticated user
        db: Database session
        
    Returns:
        List of agents
    """
    logger.info("[API:Config] Get agents")
    
    try:
        # Query agents
        agents = db.query(Agent).all()
        
        return [agent.to_dict() for agent in agents]
        
    except Exception as e:
        logger.error(f"[API:Config] Error getting agents: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting agents: {str(e)}"
        )


@router.post("/agents", response_model=Dict[str, Any])
async def create_agent(
    agent: AgentCreate,
    user: User = Depends(verify_scope(["admin"])),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Create agent.
    
    Args:
        agent: Agent data
        user: Authenticated user with admin scope
        db: Database session
        
    Returns:
        Created agent
    """
    logger.info(f"[API:Config] Create agent: {agent.name}")
    
    try:
        # Check if name already exists
        existing = db.query(Agent).filter(
            Agent.name == agent.name
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Agent with name '{agent.name}' already exists"
            )
        
        # Create agent
        new_agent = Agent(
            name=agent.name,
            description=agent.description,
            system_prompt=agent.system_prompt,
            llm_connection_id=agent.llm_connection_id,
            router_config=agent.router_config,
            planner_config=agent.planner_config
        )
        
        db.add(new_agent)
        db.commit()
        db.refresh(new_agent)
        
        # Add tools if provided
        if agent.tool_ids:
            tools = db.query(Tool).filter(Tool.id.in_(agent.tool_ids)).all()
            new_agent.tools = tools
            db.commit()
            db.refresh(new_agent)
        
        return new_agent.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API:Config] Error creating agent: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating agent: {str(e)}"
        )


# Credential endpoints
@router.get("/credentials", response_model=List[Dict[str, Any]])
async def get_credentials(
    user: User = Depends(verify_scope(["admin"])),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get credentials.
    
    Args:
        user: Authenticated user with admin scope
        db: Database session
        
    Returns:
        List of credentials (without sensitive data)
    """
    logger.info("[API:Config] Get credentials")
    
    try:
        # Query credentials
        credentials = db.query(Credential).all()
        
        # Return without sensitive data
        return [cred.to_safe_dict() for cred in credentials]
        
    except Exception as e:
        logger.error(f"[API:Config] Error getting credentials: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting credentials: {str(e)}"
        )


@router.post("/credentials", response_model=Dict[str, Any])
async def create_credential(
    credential: CredentialCreate,
    user: User = Depends(verify_scope(["admin"])),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Create credential.
    
    Args:
        credential: Credential data
        user: Authenticated user with admin scope
        db: Database session
        
    Returns:
        Created credential (without sensitive data)
    """
    logger.info(f"[API:Config] Create credential: {credential.name}")
    
    try:
        # Check if name already exists
        existing = db.query(Credential).filter(
            Credential.name == credential.name
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Credential with name '{credential.name}' already exists"
            )
        
        # Create credential
        new_credential = Credential(
            name=credential.name,
            type=credential.type,
            secret=str(credential.data)  # In production, this would be encrypted
        )
        
        db.add(new_credential)
        db.commit()
        db.refresh(new_credential)
        
        # Return without sensitive data
        return new_credential.to_safe_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API:Config] Error creating credential: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating credential: {str(e)}"
        )


# Data source endpoints
@router.get("/datasources", response_model=List[Dict[str, Any]])
async def get_datasources(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get data sources.
    
    Args:
        user: Authenticated user
        db: Database session
        
    Returns:
        List of data sources
    """
    logger.info("[API:Config] Get data sources")
    
    try:
        # Query data sources
        datasources = db.query(DataSource).all()
        
        return [ds.to_dict() for ds in datasources]
        
    except Exception as e:
        logger.error(f"[API:Config] Error getting data sources: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting data sources: {str(e)}"
        )


@router.post("/datasources", response_model=Dict[str, Any])
async def create_datasource(
    datasource: DataSourceCreate,
    user: User = Depends(verify_scope(["admin"])),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Create data source.
    
    Args:
        datasource: Data source data
        user: Authenticated user with admin scope
        db: Database session
        
    Returns:
        Created data source
    """
    logger.info(f"[API:Config] Create data source: {datasource.name}")
    
    try:
        # Check if name already exists
        existing = db.query(DataSource).filter(
            DataSource.name == datasource.name
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Data source with name '{datasource.name}' already exists"
            )
        
        # Create data source
        new_datasource = DataSource(
            name=datasource.name,
            type=datasource.type,
            url=datasource.url,
            credential_id=datasource.credential_id,
            config=datasource.config
        )
        
        db.add(new_datasource)
        db.commit()
        db.refresh(new_datasource)
        
        return new_datasource.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API:Config] Error creating data source: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating data source: {str(e)}"
        )
