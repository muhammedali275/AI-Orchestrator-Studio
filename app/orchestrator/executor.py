"""
Executor for AIpanel orchestration.

Provides high-level functions for running the orchestration flow.
"""

import logging
import uuid
import time
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

from sqlalchemy.orm import Session

from ..config import get_settings
from ..db.models import Agent, ChatSession, Message
from ..db.session import get_db
from ..llm.client import LLMClient
from .graph import run_graph
from .memory import get_memory_for_session, get_global_cache

logger = logging.getLogger(__name__)
settings = get_settings()


async def run_flow(
    user_input: str,
    agent_name: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Run orchestration flow.
    
    Args:
        user_input: User input
        agent_name: Agent name
        user_id: User ID
        session_id: Chat session ID
        db: Database session
        
    Returns:
        Flow result
    """
    start_time = time.time()
    execution_id = str(uuid.uuid4())
    
    logger.info(f"[Executor] Starting flow execution {execution_id}")
    
    # Use provided session or create a new one
    if not db:
        async for db_session in get_db():
            db = db_session
            break
    
    try:
        # Use default agent if not specified
        if not agent_name:
            agent_name = settings.DEFAULT_AGENT_NAME
        
        # Get agent from database
        agent = db.query(Agent).filter(Agent.name == agent_name).first()
        if not agent:
            logger.warning(f"Agent {agent_name} not found, using default configuration")
        
        # Create or get chat session
        if session_id:
            chat_session = db.query(ChatSession).filter(
                ChatSession.id == session_id
            ).first()
            
            if not chat_session:
                chat_session = ChatSession(
                    id=session_id,
                    user_id=user_id,
                    agent_id=agent.id if agent else None,
                    title=f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                )
                db.add(chat_session)
                db.commit()
        else:
            # Create new session
            chat_session = ChatSession(
                user_id=user_id,
                agent_id=agent.id if agent else None,
                title=f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            db.add(chat_session)
            db.commit()
            session_id = chat_session.id
        
        # Check cache for similar queries
        cache = await get_global_cache(db)
        cache_key = f"flow:{agent_name}:{hash(user_input)}"
        
        cached_result = await cache.get(cache_key)
        if cached_result and settings.CACHE_ENABLED:
            logger.info(f"[Executor] Cache hit for {cache_key}")
            
            # Update timestamp for cached result
            cached_result["timestamp"] = datetime.now().isoformat()
            cached_result["from_cache"] = True
            
            # Store in memory even for cached results
            memory = await get_memory_for_session(
                session_id=session_id,
                user_id=user_id,
                db=db
            )
            
            # Add user message
            await memory.chat_memory.add_message(
                message={"role": "user", "content": user_input}
            )
            
            # Add assistant message
            await memory.chat_memory.add_message(
                message={"role": "assistant", "content": cached_result["answer"]}
            )
            
            return cached_result
        
        # Run graph
        result = await run_graph(
            user_input=user_input,
            session_id=session_id,
            user_id=user_id,
            agent_name=agent_name,
            db=db
        )
        
        # Add execution metadata
        execution_time = time.time() - start_time
        result["execution_time"] = execution_time
        result["timestamp"] = datetime.now().isoformat()
        result["agent_name"] = agent_name
        result["session_id"] = session_id
        
        # Cache result
        if settings.CACHE_ENABLED and not result["error"]:
            await cache.set(
                key=cache_key,
                value=result,
                ttl=settings.CACHE_TTL_SECONDS
            )
        
        logger.info(f"[Executor] Completed flow execution {execution_id} in {execution_time:.2f}s")
        
        return result
        
    except Exception as e:
        logger.error(f"[Executor] Error in flow execution: {str(e)}")
        
        execution_time = time.time() - start_time
        
        return {
            "answer": f"I'm sorry, an error occurred: {str(e)}",
            "sources": [],
            "execution_id": execution_id,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "agent_name": agent_name,
            "session_id": session_id
        }


async def get_topology_config(
    agent_name: Optional[str] = None,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Get topology configuration.
    
    Args:
        agent_name: Agent name
        db: Database session
        
    Returns:
        Topology configuration
    """
    # Use provided session or create a new one
    if not db:
        async for db_session in get_db():
            db = db_session
            break
    
    # Use default agent if not specified
    if not agent_name:
        agent_name = settings.DEFAULT_AGENT_NAME
    
    # Get agent from database
    agent = db.query(Agent).filter(Agent.name == agent_name).first()
    
    # Default topology
    topology = {
        "nodes": [
            {"id": "start", "type": "start", "data": {"label": "Start"}},
            {"id": "intent_router", "type": "router", "data": {"label": "Intent Router"}},
            {"id": "planner", "type": "planner", "data": {"label": "Planner"}},
            {"id": "llm_agent", "type": "llm", "data": {"label": "LLM Agent"}},
            {"id": "tool_executor", "type": "tools", "data": {"label": "Tool Executor"}},
            {"id": "grounding", "type": "grounding", "data": {"label": "Grounding"}},
            {"id": "memory_store", "type": "memory", "data": {"label": "Memory Store"}},
            {"id": "end", "type": "end", "data": {"label": "End"}}
        ],
        "edges": [
            {"source": "start", "target": "intent_router", "label": "input"},
            {"source": "intent_router", "target": "planner", "label": "complex_intent"},
            {"source": "intent_router", "target": "llm_agent", "label": "simple_intent"},
            {"source": "intent_router", "target": "tool_executor", "label": "tool_intent"},
            {"source": "planner", "target": "llm_agent", "label": "plan"},
            {"source": "planner", "target": "tool_executor", "label": "tool_plan"},
            {"source": "llm_agent", "target": "tool_executor", "label": "tool_call"},
            {"source": "llm_agent", "target": "memory_store", "label": "response"},
            {"source": "tool_executor", "target": "grounding", "label": "result"},
            {"source": "grounding", "target": "memory_store", "label": "grounded"},
            {"source": "memory_store", "target": "end", "label": "complete"}
        ]
    }
    
    # Customize based on agent configuration
    if agent and agent.router_config:
        # Apply agent-specific customizations
        router_config = agent.router_config
        
        # Example: Add or remove nodes based on configuration
        if router_config.get("disable_grounding", False):
            # Remove grounding node
            topology["nodes"] = [node for node in topology["nodes"] if node["id"] != "grounding"]
            
            # Update edges
            topology["edges"] = [
                edge for edge in topology["edges"] 
                if edge["source"] != "grounding" and edge["target"] != "grounding"
            ]
            
            # Add direct edge from tool_executor to memory_store
            topology["edges"].append({
                "source": "tool_executor", 
                "target": "memory_store", 
                "label": "result"
            })
    
    return topology


async def update_topology_config(
    topology: Dict[str, Any],
    agent_name: Optional[str] = None,
    db: Optional[Session] = None
) -> bool:
    """
    Update topology configuration.
    
    Args:
        topology: Topology configuration
        agent_name: Agent name
        db: Database session
        
    Returns:
        True if successful, False otherwise
    """
    # Use provided session or create a new one
    if not db:
        async for db_session in get_db():
            db = db_session
            break
    
    # Use default agent if not specified
    if not agent_name:
        agent_name = settings.DEFAULT_AGENT_NAME
    
    try:
        # Get agent from database
        agent = db.query(Agent).filter(Agent.name == agent_name).first()
        
        if not agent:
            # Create new agent if not found
            agent = Agent(
                name=agent_name,
                description=f"Agent {agent_name}",
                system_prompt="You are a helpful AI assistant."
            )
            db.add(agent)
        
        # Extract router configuration from topology
        router_config = {
            "topology": topology,
            "updated_at": datetime.now().isoformat()
        }
        
        # Update agent
        agent.router_config = router_config
        db.commit()
        
        return True
        
    except Exception as e:
        logger.error(f"[Executor] Error updating topology: {str(e)}")
        return False
