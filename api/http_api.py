"""
HTTP API - Exposes REST endpoints for AIPanel.

Main endpoints:
- POST /api/chat: Main chat entrypoint (for GUI test + external systems)
- POST /api/flow/execute: Optional, for batch/workflow execution
- GET /api/flow/status/{run_id}: Get status of a flow execution
- Various config and monitoring endpoints
"""

import logging
import time
import uuid
from typing import Dict, Any, Optional, List, Union

from fastapi import FastAPI, HTTPException, Depends, Header, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..core.config.config_service import ConfigService
from ..core.topology.topology_engine import TopologyEngine

logger = logging.getLogger(__name__)


# Request/Response Models
class ChatRequest(BaseModel):
    """Chat request model."""
    
    message: str = Field(..., description="User message")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    client_id: Optional[str] = Field(None, description="Client ID")
    topology: Optional[str] = Field(None, description="Topology name")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ChatResponse(BaseModel):
    """Chat response model."""
    
    message: str = Field(..., description="Assistant message")
    conversation_id: str = Field(..., description="Conversation ID")
    run_id: str = Field(..., description="Run ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class FlowExecuteRequest(BaseModel):
    """Flow execution request model."""
    
    input: Dict[str, Any] = Field(..., description="Flow input")
    topology: str = Field(..., description="Topology name")
    client_id: Optional[str] = Field(None, description="Client ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class FlowExecuteResponse(BaseModel):
    """Flow execution response model."""
    
    run_id: str = Field(..., description="Run ID")
    status: str = Field(..., description="Execution status")
    result: Optional[Dict[str, Any]] = Field(None, description="Execution result")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class FlowStatusResponse(BaseModel):
    """Flow status response model."""
    
    run_id: str = Field(..., description="Run ID")
    status: str = Field(..., description="Execution status")
    result: Optional[Dict[str, Any]] = Field(None, description="Execution result")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ConfigTestResponse(BaseModel):
    """Configuration test response model."""
    
    success: bool = Field(..., description="Test success")
    message: str = Field(..., description="Test message")
    details: Optional[Dict[str, Any]] = Field(None, description="Test details")


class MonitoringSummaryResponse(BaseModel):
    """Monitoring summary response model."""
    
    status: str = Field(..., description="Overall status")
    components: Dict[str, Dict[str, Any]] = Field(..., description="Component statuses")
    metrics: Dict[str, Any] = Field(..., description="Metrics")


class ServiceControlResponse(BaseModel):
    """Service control response model."""
    
    success: bool = Field(..., description="Operation success")
    message: str = Field(..., description="Operation message")
    details: Optional[Dict[str, Any]] = Field(None, description="Operation details")


# API Key Dependency
async def verify_api_key(
    x_api_key: str = Header(None),
    config_service: ConfigService = None
) -> str:
    """
    Verify API key.
    
    Args:
        x_api_key: API key
        config_service: Configuration service
        
    Returns:
        Client ID associated with API key
        
    Raises:
        HTTPException: If API key is invalid
    """
    if not config_service.api_key_required:
        # API key not required
        return None
    
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    # Verify API key
    client_id = config_service.verify_api_key(x_api_key)
    if not client_id:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return client_id


# Background Tasks
async def execute_flow_background(
    run_id: str,
    topology_name: str,
    input_data: Dict[str, Any],
    user_id: str,
    client_id: Optional[str],
    metadata: Optional[Dict[str, Any]],
    topology_engine: TopologyEngine,
    config_service: ConfigService
) -> None:
    """
    Execute flow in background.
    
    Args:
        run_id: Run ID
        topology_name: Topology name
        input_data: Input data
        user_id: User ID
        client_id: Client ID
        metadata: Additional metadata
        topology_engine: Topology engine
        config_service: Configuration service
    """
    try:
        # Update run status
        config_service.update_run_status(
            run_id=run_id,
            status="running",
            result=None,
            metadata={
                "start_time": time.time(),
                "topology": topology_name,
                "user_id": user_id,
                "client_id": client_id
            }
        )
        
        # Execute topology
        result = await topology_engine.execute(
            topology_name=topology_name,
            input_text=input_data.get("input", ""),
            user_id=user_id,
            client_id=client_id,
            metadata=metadata
        )
        
        # Update run status
        config_service.update_run_status(
            run_id=run_id,
            status="completed",
            result=result,
            metadata={
                "end_time": time.time(),
                "execution_time": result.get("execution_time", 0)
            }
        )
        
    except Exception as e:
        logger.error(f"Error executing flow: {str(e)}")
        
        # Update run status
        config_service.update_run_status(
            run_id=run_id,
            status="failed",
            result=None,
            metadata={
                "end_time": time.time(),
                "error": str(e)
            }
        )


# API Class
class HTTPAPI:
    """HTTP API for AIPanel."""
    
    def __init__(
        self,
        config_service: ConfigService,
        topology_engine: TopologyEngine
    ):
        """
        Initialize HTTP API.
        
        Args:
            config_service: Configuration service
            topology_engine: Topology engine
        """
        self.config_service = config_service
        self.topology_engine = topology_engine
        
        # Create FastAPI app
        self.app = FastAPI(
            title="AIPanel API",
            description="API for AIPanel AI Orchestrator",
            version="1.0.0"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=config_service.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self) -> None:
        """Register API routes."""
        # Chat routes
        @self.app.post("/api/chat", response_model=ChatResponse)
        async def chat(
            request: ChatRequest,
            client_id: str = Depends(verify_api_key)
        ) -> ChatResponse:
            """
            Chat endpoint.
            
            Args:
                request: Chat request
                client_id: Client ID from API key
                
            Returns:
                Chat response
            """
            try:
                # Override client ID if provided in request
                if request.client_id:
                    client_id = request.client_id
                
                # Get user ID
                user_id = "anonymous"  # In a real system, this would come from authentication
                
                # Get topology name
                topology_name = request.topology or self.config_service.default_topology
                
                # Generate run ID
                run_id = str(uuid.uuid4())
                
                # Execute topology
                result = await self.topology_engine.execute(
                    topology_name=topology_name,
                    input_text=request.message,
                    user_id=user_id,
                    conversation_id=request.conversation_id,
                    client_id=client_id,
                    metadata=request.metadata
                )
                
                # Get conversation ID
                conversation_id = result.get("conversation_id", request.conversation_id)
                
                # Return response
                return ChatResponse(
                    message=result.get("output", ""),
                    conversation_id=conversation_id,
                    run_id=run_id,
                    metadata=result.get("metadata")
                )
                
            except Exception as e:
                logger.error(f"Error in chat endpoint: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # Flow execution routes
        @self.app.post("/api/flow/execute", response_model=FlowExecuteResponse)
        async def execute_flow(
            request: FlowExecuteRequest,
            background_tasks: BackgroundTasks,
            client_id: str = Depends(verify_api_key)
        ) -> FlowExecuteResponse:
            """
            Execute flow endpoint.
            
            Args:
                request: Flow execution request
                background_tasks: Background tasks
                client_id: Client ID from API key
                
            Returns:
                Flow execution response
            """
            try:
                # Override client ID if provided in request
                if request.client_id:
                    client_id = request.client_id
                
                # Get user ID
                user_id = "anonymous"  # In a real system, this would come from authentication
                
                # Generate run ID
                run_id = str(uuid.uuid4())
                
                # Add background task
                background_tasks.add_task(
                    execute_flow_background,
                    run_id=run_id,
                    topology_name=request.topology,
                    input_data=request.input,
                    user_id=user_id,
                    client_id=client_id,
                    metadata=request.metadata,
                    topology_engine=self.topology_engine,
                    config_service=self.config_service
                )
                
                # Return response
                return FlowExecuteResponse(
                    run_id=run_id,
                    status="queued",
                    metadata={
                        "queue_time": time.time(),
                        "topology": request.topology
                    }
                )
                
            except Exception as e:
                logger.error(f"Error in execute flow endpoint: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/flow/status/{run_id}", response_model=FlowStatusResponse)
        async def get_flow_status(
            run_id: str,
            client_id: str = Depends(verify_api_key)
        ) -> FlowStatusResponse:
            """
            Get flow status endpoint.
            
            Args:
                run_id: Run ID
                client_id: Client ID from API key
                
            Returns:
                Flow status response
            """
            try:
                # Get run status
                status = self.config_service.get_run_status(run_id)
                if not status:
                    raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
                
                # Return response
                return FlowStatusResponse(
                    run_id=run_id,
                    status=status.get("status", "unknown"),
                    result=status.get("result"),
                    metadata=status.get("metadata")
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error in get flow status endpoint: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # Configuration test routes
        @self.app.get("/api/config/test/llm/{id}", response_model=ConfigTestResponse)
        async def test_llm_config(
            id: str,
            client_id: str = Depends(verify_api_key)
        ) -> ConfigTestResponse:
            """
            Test LLM configuration endpoint.
            
            Args:
                id: LLM ID
                client_id: Client ID from API key
                
            Returns:
                Configuration test response
            """
            try:
                # Test LLM configuration
                result = await self.config_service.test_llm_config(id)
                
                # Return response
                return ConfigTestResponse(
                    success=result.get("success", False),
                    message=result.get("message", ""),
                    details=result.get("details")
                )
                
            except Exception as e:
                logger.error(f"Error in test LLM config endpoint: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/config/test/tool/{id}", response_model=ConfigTestResponse)
        async def test_tool_config(
            id: str,
            client_id: str = Depends(verify_api_key)
        ) -> ConfigTestResponse:
            """
            Test tool configuration endpoint.
            
            Args:
                id: Tool ID
                client_id: Client ID from API key
                
            Returns:
                Configuration test response
            """
            try:
                # Test tool configuration
                result = await self.config_service.test_tool_config(id)
                
                # Return response
                return ConfigTestResponse(
                    success=result.get("success", False),
                    message=result.get("message", ""),
                    details=result.get("details")
                )
                
            except Exception as e:
                logger.error(f"Error in test tool config endpoint: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/config/test/db/{id}", response_model=ConfigTestResponse)
        async def test_db_config(
            id: str,
            client_id: str = Depends(verify_api_key)
        ) -> ConfigTestResponse:
            """
            Test database configuration endpoint.
            
            Args:
                id: Database ID
                client_id: Client ID from API key
                
            Returns:
                Configuration test response
            """
            try:
                # Test database configuration
                result = await self.config_service.test_db_config(id)
                
                # Return response
                return ConfigTestResponse(
                    success=result.get("success", False),
                    message=result.get("message", ""),
                    details=result.get("details")
                )
                
            except Exception as e:
                logger.error(f"Error in test DB config endpoint: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # Monitoring routes
        @self.app.get("/api/monitoring/summary", response_model=MonitoringSummaryResponse)
        async def get_monitoring_summary(
            client_id: str = Depends(verify_api_key)
        ) -> MonitoringSummaryResponse:
            """
            Get monitoring summary endpoint.
            
            Args:
                client_id: Client ID from API key
                
            Returns:
                Monitoring summary response
            """
            try:
                # Get monitoring targets
                targets = self.config_service.get_monitoring_targets()
                
                # Get monitoring summary
                # In a real system, this would call a monitoring service
                # For now, we'll just return a placeholder
                
                return MonitoringSummaryResponse(
                    status="healthy",
                    components={
                        "llm": {
                            "status": "healthy",
                            "latency_ms": 150
                        },
                        "database": {
                            "status": "healthy",
                            "connections": 5
                        },
                        "api": {
                            "status": "healthy",
                            "requests_per_minute": 10
                        }
                    },
                    metrics={
                        "requests_total": 1000,
                        "average_latency_ms": 200,
                        "error_rate": 0.01
                    }
                )
                
            except Exception as e:
                logger.error(f"Error in get monitoring summary endpoint: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/monitoring/restart-service", response_model=ServiceControlResponse)
        async def restart_service(
            service: str,
            client_id: str = Depends(verify_api_key)
        ) -> ServiceControlResponse:
            """
            Restart service endpoint.
            
            Args:
                service: Service name
                client_id: Client ID from API key
                
            Returns:
                Service control response
            """
            try:
                # Check if service restart is allowed
                if not self.config_service.is_service_restart_allowed(service):
                    raise HTTPException(status_code=403, detail=f"Restart not allowed for service: {service}")
                
                # Restart service
                # In a real system, this would call a service control service
                # For now, we'll just return a placeholder
                
                return ServiceControlResponse(
                    success=True,
                    message=f"Service restarted: {service}",
                    details={
                        "restart_time": time.time(),
                        "service": service
                    }
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error in restart service endpoint: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
    
    def get_app(self) -> FastAPI:
        """
        Get FastAPI app.
        
        Returns:
            FastAPI app
        """
        return self.app
