"""
Topology Execution API.

Provides endpoints for executing and monitoring workflow topology.
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from ..config import get_settings, Settings
from ..graph import OrchestrationGraph

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/topology", tags=["topology"])


class FlowExecutionRequest(BaseModel):
    """Model for flow execution request."""
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Input data for the flow")
    test_mode: bool = Field(default=True, description="Run in test mode")


class ComponentTestRequest(BaseModel):
    """Model for component testing request."""
    component_id: str = Field(..., description="Component ID to test")
    test_data: Dict[str, Any] = Field(default_factory=dict, description="Test data")


class FlowStatus(BaseModel):
    """Model for flow execution status."""
    execution_id: str
    status: str  # running, completed, failed, paused
    current_node: Optional[str] = None
    progress: float = 0.0
    start_time: datetime
    end_time: Optional[datetime] = None
    error: Optional[str] = None
    logs: List[Dict[str, Any]] = []


# Store active executions
active_executions: Dict[str, FlowStatus] = {}


@router.get("/graph")
async def get_topology_graph(
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Get the current topology graph structure.
    
    Returns nodes and edges for visualization.
    """
    try:
        # Define the topology structure with proper format for frontend
        nodes = [
            {
                "id": "start",
                "type": "start",
                "label": "Start",
                "description": "Entry Point - Receives user input",
                "status": "idle"
            },
            {
                "id": "intent_router",
                "type": "intent_router",
                "label": "Intent Router",
                "description": "Analyzes and classifies user intent",
                "status": "idle"
            },
            {
                "id": "planner",
                "type": "planner",
                "label": "Planner",
                "description": "Plans execution strategy and task breakdown",
                "status": "idle"
            },
            {
                "id": "llm_agent",
                "type": "llm_agent",
                "label": "LLM Agent",
                "description": f"Processes with {settings.llm_default_model or 'LLM'}",
                "status": "idle",
                "config": {
                    "model": settings.llm_default_model,
                    "endpoint": settings.llm_base_url
                }
            },
            {
                "id": "tool_executor",
                "type": "tool_executor",
                "label": "Tool Executor",
                "description": f"Executes {len(settings.tools)} configured tools",
                "status": "idle",
                "config": {
                    "tools_count": len(settings.tools),
                    "tools": list(settings.tools.keys()) if settings.tools else []
                }
            },
            {
                "id": "grounding",
                "type": "grounding",
                "label": "Data Grounding",
                "description": "Retrieves context from data sources (RAG)",
                "status": "idle",
                "config": {
                    "datasource_configured": settings.datasource_base_url is not None
                }
            },
            {
                "id": "memory_store",
                "type": "memory_store",
                "label": "Memory Store",
                "description": "Manages conversation cache and state",
                "status": "idle"
            },
            {
                "id": "audit",
                "type": "audit",
                "label": "Audit Log",
                "description": "Records execution for compliance",
                "status": "idle"
            },
            {
                "id": "end",
                "type": "end",
                "label": "End",
                "description": "Returns final response to user",
                "status": "idle"
            }
        ]
        
        edges = [
            {"source": "start", "target": "intent_router", "label": "input"},
            {"source": "intent_router", "target": "planner", "label": "route"},
            {"source": "planner", "target": "llm_agent", "label": "plan"},
            {"source": "llm_agent", "target": "tool_executor", "label": "tool_call"},
            {"source": "tool_executor", "target": "grounding", "label": "fetch_data"},
            {"source": "grounding", "target": "llm_agent", "label": "context"},
            {"source": "llm_agent", "target": "memory_store", "label": "store"},
            {"source": "memory_store", "target": "audit", "label": "log"},
            {"source": "audit", "target": "end", "label": "result"},
            {"source": "llm_agent", "target": "end", "label": "complete"}
        ]
        
        return {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "llm_configured": settings.llm_base_url is not None,
                "llm_model": settings.llm_default_model,
                "tools_configured": len(settings.tools) > 0,
                "datasource_configured": settings.datasource_base_url is not None
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting topology graph: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute")
async def execute_flow(
    request: FlowExecutionRequest,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Execute the workflow topology.
    
    Starts a new flow execution and returns execution ID.
    """
    try:
        import uuid
        execution_id = str(uuid.uuid4())
        
        # Create flow status
        flow_status = FlowStatus(
            execution_id=execution_id,
            status="running",
            current_node="start",
            progress=0.0,
            start_time=datetime.utcnow(),
            logs=[{
                "timestamp": datetime.utcnow().isoformat(),
                "level": "info",
                "message": "Flow execution started",
                "node": "start"
            }]
        )
        
        active_executions[execution_id] = flow_status
        
        # Start async execution
        asyncio.create_task(run_flow_execution(execution_id, request, settings))
        
        return {
            "success": True,
            "execution_id": execution_id,
            "status": "running",
            "message": "Flow execution started"
        }
        
    except Exception as e:
        logger.error(f"Error starting flow execution: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def run_flow_execution(
    execution_id: str,
    request: FlowExecutionRequest,
    settings: Settings
):
    """
    Run the actual flow execution asynchronously.
    """
    try:
        flow_status = active_executions[execution_id]
        
        # Simulate flow execution through nodes
        nodes = ["start", "intent_router", "planner", "llm_agent", "safety_check", "end"]
        
        for i, node in enumerate(nodes):
            # Update current node
            flow_status.current_node = node
            flow_status.progress = (i + 1) / len(nodes) * 100
            
            # Add log
            flow_status.logs.append({
                "timestamp": datetime.utcnow().isoformat(),
                "level": "info",
                "message": f"Processing node: {node}",
                "node": node
            })
            
            # Simulate processing time
            await asyncio.sleep(1)
            
            # Check for errors (simulate)
            if node == "llm_agent" and not settings.llm_base_url:
                flow_status.status = "failed"
                flow_status.error = "LLM not configured"
                flow_status.logs.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "level": "error",
                    "message": "LLM endpoint not configured",
                    "node": node
                })
                flow_status.end_time = datetime.utcnow()
                return
        
        # Mark as completed
        flow_status.status = "completed"
        flow_status.current_node = "end"
        flow_status.progress = 100.0
        flow_status.end_time = datetime.utcnow()
        flow_status.logs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "level": "info",
            "message": "Flow execution completed successfully",
            "node": "end"
        })
        
    except Exception as e:
        logger.error(f"Error in flow execution {execution_id}: {str(e)}")
        flow_status = active_executions.get(execution_id)
        if flow_status:
            flow_status.status = "failed"
            flow_status.error = str(e)
            flow_status.end_time = datetime.utcnow()


@router.get("/execution/{execution_id}")
async def get_execution_status(execution_id: str) -> Dict[str, Any]:
    """
    Get the status of a flow execution.
    """
    if execution_id not in active_executions:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    flow_status = active_executions[execution_id]
    
    return {
        "execution_id": flow_status.execution_id,
        "status": flow_status.status,
        "current_node": flow_status.current_node,
        "progress": flow_status.progress,
        "start_time": flow_status.start_time.isoformat(),
        "end_time": flow_status.end_time.isoformat() if flow_status.end_time else None,
        "error": flow_status.error,
        "logs": flow_status.logs[-10:]  # Return last 10 logs
    }


@router.post("/test-component")
async def test_component(
    request: ComponentTestRequest,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Test a specific component in the topology.
    """
    try:
        component_id = request.component_id
        
        # Simulate component testing
        if component_id == "llm_agent":
            if not settings.llm_base_url:
                return {
                    "success": False,
                    "component_id": component_id,
                    "error": "LLM endpoint not configured",
                    "status": "failed"
                }
            
            return {
                "success": True,
                "component_id": component_id,
                "status": "healthy",
                "message": "LLM agent is configured and ready",
                "config": {
                    "endpoint": settings.llm_base_url,
                    "model": settings.llm_default_model
                }
            }
        
        elif component_id == "tool_executor":
            return {
                "success": True,
                "component_id": component_id,
                "status": "healthy",
                "message": f"{len(settings.tools)} tools configured",
                "tools": list(settings.tools.keys())
            }
        
        else:
            return {
                "success": True,
                "component_id": component_id,
                "status": "healthy",
                "message": f"Component {component_id} is operational"
            }
        
    except Exception as e:
        logger.error(f"Error testing component {request.component_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/execution/{execution_id}")
async def stop_execution(execution_id: str) -> Dict[str, Any]:
    """
    Stop a running flow execution.
    """
    if execution_id not in active_executions:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    flow_status = active_executions[execution_id]
    
    if flow_status.status == "running":
        flow_status.status = "stopped"
        flow_status.end_time = datetime.utcnow()
        flow_status.logs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "level": "warning",
            "message": "Flow execution stopped by user",
            "node": flow_status.current_node
        })
    
    return {
        "success": True,
        "execution_id": execution_id,
        "status": flow_status.status,
        "message": "Execution stopped"
    }


@router.get("/executions")
async def list_executions() -> Dict[str, Any]:
    """
    List all flow executions.
    """
    executions = []
    
    for exec_id, flow_status in active_executions.items():
        executions.append({
            "execution_id": exec_id,
            "status": flow_status.status,
            "current_node": flow_status.current_node,
            "progress": flow_status.progress,
            "start_time": flow_status.start_time.isoformat(),
            "end_time": flow_status.end_time.isoformat() if flow_status.end_time else None
        })
    
    return {
        "executions": executions,
        "total": len(executions)
    }
