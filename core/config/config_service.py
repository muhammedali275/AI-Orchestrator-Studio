"""
Configuration Service for AIPanel.

Single source of truth for runtime configuration.
Reads/writes config from external DB or config store.
NO hard-coded IPs, ports, or credentials in code.
"""

import json
import logging
import os
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class LLMConfig(BaseModel):
    """Configuration for an LLM provider."""
    name: str = Field(..., description="LLM name/identifier")
    provider: str = Field(..., description="Provider (openai, azure, ollama, vllm, etc.)")
    model: str = Field(..., description="Model name")
    api_key: Optional[str] = Field(None, description="API key")
    base_url: Optional[str] = Field(None, description="Base URL for API")
    timeout_seconds: int = Field(default=60, description="Request timeout")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens for response")
    temperature: float = Field(default=0.7, description="Sampling temperature")
    enabled: bool = Field(default=True, description="Whether LLM is enabled")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ToolConfig(BaseModel):
    """Configuration for a tool."""
    name: str = Field(..., description="Tool name/identifier")
    type: str = Field(..., description="Tool type (http, db, vector, etc.)")
    description: str = Field(..., description="Tool description")
    credential_id: Optional[str] = Field(None, description="Credential ID for authentication")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool-specific parameters")
    enabled: bool = Field(default=True, description="Whether tool is enabled")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AgentConfig(BaseModel):
    """Configuration for an agent."""
    name: str = Field(..., description="Agent name/identifier")
    description: str = Field(..., description="Agent description")
    llm_name: str = Field(..., description="LLM to use for this agent")
    system_prompt: str = Field(..., description="System prompt for the agent")
    tools: List[str] = Field(default_factory=list, description="Tool names available to this agent")
    memory_policy: Dict[str, Any] = Field(default_factory=dict, description="Memory policy configuration")
    enabled: bool = Field(default=True, description="Whether agent is enabled")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class PlannerConfig(BaseModel):
    """Configuration for a planner."""
    name: str = Field(..., description="Planner name/identifier")
    type: str = Field(..., description="Planner type (llm, rules, semantic)")
    llm_name: Optional[str] = Field(None, description="LLM to use for this planner (if applicable)")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Planner-specific parameters")
    enabled: bool = Field(default=True, description="Whether planner is enabled")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class RouterConfig(BaseModel):
    """Configuration for a router."""
    name: str = Field(..., description="Router name/identifier")
    type: str = Field(..., description="Router type (llm, rules, semantic)")
    llm_name: Optional[str] = Field(None, description="LLM to use for this router (if applicable)")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Router-specific parameters")
    enabled: bool = Field(default=True, description="Whether router is enabled")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class TopologyConfig(BaseModel):
    """Configuration for a topology."""
    name: str = Field(..., description="Topology name/identifier")
    description: str = Field(..., description="Topology description")
    nodes: Dict[str, Dict[str, Any]] = Field(..., description="Node configurations")
    edges: List[Dict[str, str]] = Field(..., description="Edge definitions (from_node, to_node)")
    default_agent: str = Field(..., description="Default agent to use")
    default_router: str = Field(..., description="Default router to use")
    default_planner: Optional[str] = Field(None, description="Default planner to use")
    enabled: bool = Field(default=True, description="Whether topology is enabled")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ClientConfig(BaseModel):
    """Configuration for a client."""
    client_id: str = Field(..., description="Client identifier")
    name: str = Field(..., description="Client name")
    api_key: Optional[str] = Field(None, description="API key for this client")
    rate_limit: Optional[int] = Field(None, description="Rate limit in requests per minute")
    default_topology: str = Field(..., description="Default topology to use")
    default_agent: Optional[str] = Field(None, description="Default agent to use")
    enabled: bool = Field(default=True, description="Whether client is enabled")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class MonitoringTarget(BaseModel):
    """Configuration for a monitoring target."""
    name: str = Field(..., description="Target name/identifier")
    type: str = Field(..., description="Target type (service, llm, db, etc.)")
    url: Optional[str] = Field(None, description="URL to check")
    command: Optional[str] = Field(None, description="Command to run for checking")
    interval_seconds: int = Field(default=60, description="Check interval in seconds")
    timeout_seconds: int = Field(default=10, description="Check timeout in seconds")
    enabled: bool = Field(default=True, description="Whether monitoring is enabled")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ConfigService:
    """
    Configuration service for AIPanel.
    
    Single source of truth for runtime configuration.
    Reads/writes config from external DB or config store.
    """
    
    def __init__(self, config_path: Optional[str] = None, db_connection: Optional[Any] = None):
        """
        Initialize configuration service.
        
        Args:
            config_path: Path to configuration directory (for file-based config)
            db_connection: Database connection (for DB-based config)
        """
        self.config_path = config_path or os.environ.get("AIPANEL_CONFIG_PATH", "./config")
        self.db_connection = db_connection
        
        # Cache for configurations
        self._llm_configs: Dict[str, LLMConfig] = {}
        self._tool_configs: Dict[str, ToolConfig] = {}
        self._agent_configs: Dict[str, AgentConfig] = {}
        self._planner_configs: Dict[str, PlannerConfig] = {}
        self._router_configs: Dict[str, RouterConfig] = {}
        self._topology_configs: Dict[str, TopologyConfig] = {}
        self._client_configs: Dict[str, ClientConfig] = {}
        self._monitoring_targets: Dict[str, MonitoringTarget] = {}
        
        # Load configurations
        self._load_configs()
    
    def _load_configs(self) -> None:
        """Load all configurations from storage."""
        if self.db_connection:
            self._load_from_db()
        else:
            self._load_from_files()
    
    def _load_from_files(self) -> None:
        """Load configurations from JSON files."""
        try:
            # Load LLM configurations
            llm_path = os.path.join(self.config_path, "llms.json")
            if os.path.exists(llm_path):
                with open(llm_path, "r") as f:
                    llm_data = json.load(f)
                    for item in llm_data.get("llms", []):
                        config = LLMConfig(**item)
                        self._llm_configs[config.name] = config
            
            # Load tool configurations
            tools_path = os.path.join(self.config_path, "tools.json")
            if os.path.exists(tools_path):
                with open(tools_path, "r") as f:
                    tools_data = json.load(f)
                    for item in tools_data.get("tools", []):
                        config = ToolConfig(**item)
                        self._tool_configs[config.name] = config
            
            # Load agent configurations
            agents_path = os.path.join(self.config_path, "agents.json")
            if os.path.exists(agents_path):
                with open(agents_path, "r") as f:
                    agents_data = json.load(f)
                    for item in agents_data.get("agents", []):
                        config = AgentConfig(**item)
                        self._agent_configs[config.name] = config
            
            # Load planner configurations
            planners_path = os.path.join(self.config_path, "planners.json")
            if os.path.exists(planners_path):
                with open(planners_path, "r") as f:
                    planners_data = json.load(f)
                    for item in planners_data.get("planners", []):
                        config = PlannerConfig(**item)
                        self._planner_configs[config.name] = config
            
            # Load router configurations
            routers_path = os.path.join(self.config_path, "routers.json")
            if os.path.exists(routers_path):
                with open(routers_path, "r") as f:
                    routers_data = json.load(f)
                    for item in routers_data.get("routers", []):
                        config = RouterConfig(**item)
                        self._router_configs[config.name] = config
            
            # Load topology configurations
            topologies_path = os.path.join(self.config_path, "topologies.json")
            if os.path.exists(topologies_path):
                with open(topologies_path, "r") as f:
                    topologies_data = json.load(f)
                    for item in topologies_data.get("topologies", []):
                        config = TopologyConfig(**item)
                        self._topology_configs[config.name] = config
            
            # Load client configurations
            clients_path = os.path.join(self.config_path, "clients.json")
            if os.path.exists(clients_path):
                with open(clients_path, "r") as f:
                    clients_data = json.load(f)
                    for item in clients_data.get("clients", []):
                        config = ClientConfig(**item)
                        self._client_configs[config.client_id] = config
            
            # Load monitoring targets
            monitoring_path = os.path.join(self.config_path, "monitoring.json")
            if os.path.exists(monitoring_path):
                with open(monitoring_path, "r") as f:
                    monitoring_data = json.load(f)
                    for item in monitoring_data.get("targets", []):
                        config = MonitoringTarget(**item)
                        self._monitoring_targets[config.name] = config
            
            logger.info(f"Loaded configurations from {self.config_path}")
            
        except Exception as e:
            logger.error(f"Error loading configurations from files: {str(e)}")
    
    def _load_from_db(self) -> None:
        """Load configurations from database."""
        # Implementation depends on the specific database being used
        # This is a placeholder for the actual implementation
        logger.info("Loading configurations from database")
    
    def get_llm_config(self, name: str) -> Optional[LLMConfig]:
        """
        Get LLM configuration by name.
        
        Args:
            name: LLM name/identifier
            
        Returns:
            LLM configuration or None if not found
        """
        return self._llm_configs.get(name)
    
    def get_tool_config(self, name: str) -> Optional[ToolConfig]:
        """
        Get tool configuration by name.
        
        Args:
            name: Tool name/identifier
            
        Returns:
            Tool configuration or None if not found
        """
        return self._tool_configs.get(name)
    
    def get_agent_config(self, name: str) -> Optional[AgentConfig]:
        """
        Get agent configuration by name.
        
        Args:
            name: Agent name/identifier
            
        Returns:
            Agent configuration or None if not found
        """
        return self._agent_configs.get(name)
    
    def get_planner_config(self, name: str) -> Optional[PlannerConfig]:
        """
        Get planner configuration by name.
        
        Args:
            name: Planner name/identifier
            
        Returns:
            Planner configuration or None if not found
        """
        return self._planner_configs.get(name)
    
    def get_router_config(self, name: str) -> Optional[RouterConfig]:
        """
        Get router configuration by name.
        
        Args:
            name: Router name/identifier
            
        Returns:
            Router configuration or None if not found
        """
        return self._router_configs.get(name)
    
    def get_topology_config(self, name: str) -> Optional[TopologyConfig]:
        """
        Get topology configuration by name.
        
        Args:
            name: Topology name/identifier
            
        Returns:
            Topology configuration or None if not found
        """
        return self._topology_configs.get(name)
    
    def get_client_config(self, client_id: str) -> Optional[ClientConfig]:
        """
        Get client configuration by client ID.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Client configuration or None if not found
        """
        return self._client_configs.get(client_id)
    
    def get_monitoring_targets(self) -> List[MonitoringTarget]:
        """
        Get all monitoring targets.
        
        Returns:
            List of monitoring target configurations
        """
        return list(self._monitoring_targets.values())
    
    def save_llm_config(self, config: LLMConfig) -> bool:
        """
        Save LLM configuration.
        
        Args:
            config: LLM configuration to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._llm_configs[config.name] = config
            self._save_configs("llms")
            return True
        except Exception as e:
            logger.error(f"Error saving LLM configuration: {str(e)}")
            return False
    
    def save_tool_config(self, config: ToolConfig) -> bool:
        """
        Save tool configuration.
        
        Args:
            config: Tool configuration to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._tool_configs[config.name] = config
            self._save_configs("tools")
            return True
        except Exception as e:
            logger.error(f"Error saving tool configuration: {str(e)}")
            return False
    
    def save_agent_config(self, config: AgentConfig) -> bool:
        """
        Save agent configuration.
        
        Args:
            config: Agent configuration to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._agent_configs[config.name] = config
            self._save_configs("agents")
            return True
        except Exception as e:
            logger.error(f"Error saving agent configuration: {str(e)}")
            return False
    
    def save_planner_config(self, config: PlannerConfig) -> bool:
        """
        Save planner configuration.
        
        Args:
            config: Planner configuration to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._planner_configs[config.name] = config
            self._save_configs("planners")
            return True
        except Exception as e:
            logger.error(f"Error saving planner configuration: {str(e)}")
            return False
    
    def save_router_config(self, config: RouterConfig) -> bool:
        """
        Save router configuration.
        
        Args:
            config: Router configuration to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._router_configs[config.name] = config
            self._save_configs("routers")
            return True
        except Exception as e:
            logger.error(f"Error saving router configuration: {str(e)}")
            return False
    
    def save_topology_config(self, config: TopologyConfig) -> bool:
        """
        Save topology configuration.
        
        Args:
            config: Topology configuration to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._topology_configs[config.name] = config
            self._save_configs("topologies")
            return True
        except Exception as e:
            logger.error(f"Error saving topology configuration: {str(e)}")
            return False
    
    def save_client_config(self, config: ClientConfig) -> bool:
        """
        Save client configuration.
        
        Args:
            config: Client configuration to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._client_configs[config.client_id] = config
            self._save_configs("clients")
            return True
        except Exception as e:
            logger.error(f"Error saving client configuration: {str(e)}")
            return False
    
    def save_monitoring_target(self, config: MonitoringTarget) -> bool:
        """
        Save monitoring target configuration.
        
        Args:
            config: Monitoring target configuration to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._monitoring_targets[config.name] = config
            self._save_configs("monitoring")
            return True
        except Exception as e:
            logger.error(f"Error saving monitoring target configuration: {str(e)}")
            return False
    
    def _save_configs(self, config_type: str) -> None:
        """
        Save configurations to storage.
        
        Args:
            config_type: Type of configuration to save
        """
        if self.db_connection:
            self._save_to_db(config_type)
        else:
            self._save_to_files(config_type)
    
    def _save_to_files(self, config_type: str) -> None:
        """
        Save configurations to JSON files.
        
        Args:
            config_type: Type of configuration to save
        """
        try:
            # Ensure config directory exists
            os.makedirs(self.config_path, exist_ok=True)
            
            if config_type == "llms":
                llm_path = os.path.join(self.config_path, "llms.json")
                with open(llm_path, "w") as f:
                    json.dump(
                        {"llms": [config.dict() for config in self._llm_configs.values()]},
                        f,
                        indent=2
                    )
            
            elif config_type == "tools":
                tools_path = os.path.join(self.config_path, "tools.json")
                with open(tools_path, "w") as f:
                    json.dump(
                        {"tools": [config.dict() for config in self._tool_configs.values()]},
                        f,
                        indent=2
                    )
            
            elif config_type == "agents":
                agents_path = os.path.join(self.config_path, "agents.json")
                with open(agents_path, "w") as f:
                    json.dump(
                        {"agents": [config.dict() for config in self._agent_configs.values()]},
                        f,
                        indent=2
                    )
            
            elif config_type == "planners":
                planners_path = os.path.join(self.config_path, "planners.json")
                with open(planners_path, "w") as f:
                    json.dump(
                        {"planners": [config.dict() for config in self._planner_configs.values()]},
                        f,
                        indent=2
                    )
            
            elif config_type == "routers":
                routers_path = os.path.join(self.config_path, "routers.json")
                with open(routers_path, "w") as f:
                    json.dump(
                        {"routers": [config.dict() for config in self._router_configs.values()]},
                        f,
                        indent=2
                    )
            
            elif config_type == "topologies":
                topologies_path = os.path.join(self.config_path, "topologies.json")
                with open(topologies_path, "w") as f:
                    json.dump(
                        {"topologies": [config.dict() for config in self._topology_configs.values()]},
                        f,
                        indent=2
                    )
            
            elif config_type == "clients":
                clients_path = os.path.join(self.config_path, "clients.json")
                with open(clients_path, "w") as f:
                    json.dump(
                        {"clients": [config.dict() for config in self._client_configs.values()]},
                        f,
                        indent=2
                    )
            
            elif config_type == "monitoring":
                monitoring_path = os.path.join(self.config_path, "monitoring.json")
                with open(monitoring_path, "w") as f:
                    json.dump(
                        {"targets": [config.dict() for config in self._monitoring_targets.values()]},
                        f,
                        indent=2
                    )
            
            logger.info(f"Saved {config_type} configurations to {self.config_path}")
            
        except Exception as e:
            logger.error(f"Error saving {config_type} configurations to files: {str(e)}")
    
    def _save_to_db(self, config_type: str) -> None:
        """
        Save configurations to database.
        
        Args:
            config_type: Type of configuration to save
        """
        # Implementation depends on the specific database being used
        # This is a placeholder for the actual implementation
        logger.info(f"Saving {config_type} configurations to database")
    
    def list_llms(self) -> List[LLMConfig]:
        """
        List all LLM configurations.
        
        Returns:
            List of LLM configurations
        """
        return list(self._llm_configs.values())
    
    def list_tools(self) -> List[ToolConfig]:
        """
        List all tool configurations.
        
        Returns:
            List of tool configurations
        """
        return list(self._tool_configs.values())
    
    def list_agents(self) -> List[AgentConfig]:
        """
        List all agent configurations.
        
        Returns:
            List of agent configurations
        """
        return list(self._agent_configs.values())
    
    def list_planners(self) -> List[PlannerConfig]:
        """
        List all planner configurations.
        
        Returns:
            List of planner configurations
        """
        return list(self._planner_configs.values())
    
    def list_routers(self) -> List[RouterConfig]:
        """
        List all router configurations.
        
        Returns:
            List of router configurations
        """
        return list(self._router_configs.values())
    
    def list_topologies(self) -> List[TopologyConfig]:
        """
        List all topology configurations.
        
        Returns:
            List of topology configurations
        """
        return list(self._topology_configs.values())
    
    def list_clients(self) -> List[ClientConfig]:
        """
        List all client configurations.
        
        Returns:
            List of client configurations
        """
        return list(self._client_configs.values())
    
    def delete_llm_config(self, name: str) -> bool:
        """
        Delete LLM configuration.
        
        Args:
            name: LLM name/identifier
            
        Returns:
            True if successful, False otherwise
        """
        if name in self._llm_configs:
            del self._llm_configs[name]
            self._save_configs("llms")
            return True
        return False
    
    def delete_tool_config(self, name: str) -> bool:
        """
        Delete tool configuration.
        
        Args:
            name: Tool name/identifier
            
        Returns:
            True if successful, False otherwise
        """
        if name in self._tool_configs:
            del self._tool_configs[name]
            self._save_configs("tools")
            return True
        return False
    
    def delete_agent_config(self, name: str) -> bool:
        """
        Delete agent configuration.
        
        Args:
            name: Agent name/identifier
            
        Returns:
            True if successful, False otherwise
        """
        if name in self._agent_configs:
            del self._agent_configs[name]
            self._save_configs("agents")
            return True
        return False
    
    def delete_planner_config(self, name: str) -> bool:
        """
        Delete planner configuration.
        
        Args:
            name: Planner name/identifier
            
        Returns:
            True if successful, False otherwise
        """
        if name in self._planner_configs:
            del self._planner_configs[name]
            self._save_configs("planners")
            return True
        return False
    
    def delete_router_config(self, name: str) -> bool:
        """
        Delete router configuration.
        
        Args:
            name: Router name/identifier
            
        Returns:
            True if successful, False otherwise
        """
        if name in self._router_configs:
            del self._router_configs[name]
            self._save_configs("routers")
            return True
        return False
    
    def delete_topology_config(self, name: str) -> bool:
        """
        Delete topology configuration.
        
        Args:
            name: Topology name/identifier
            
        Returns:
            True if successful, False otherwise
        """
        if name in self._topology_configs:
            del self._topology_configs[name]
            self._save_configs("topologies")
            return True
        return False
    
    def delete_client_config(self, client_id: str) -> bool:
        """
        Delete client configuration.
        
        Args:
            client_id: Client identifier
            
        Returns:
            True if successful, False otherwise
        """
        if client_id in self._client_configs:
            del self._client_configs[client_id]
            self._save_configs("clients")
            return True
        return False
    
    def delete_monitoring_target(self, name: str) -> bool:
        """
        Delete monitoring target configuration.
        
        Args:
            name: Target name/identifier
            
        Returns:
            True if successful, False otherwise
        """
        if name in self._monitoring_targets:
            del self._monitoring_targets[name]
            self._save_configs("monitoring")
            return True
        return False
