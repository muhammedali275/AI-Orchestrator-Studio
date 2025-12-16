"""
Configuration management for ZainOne Orchestrator Studio.

All runtime connectivity comes from environment variables or .env file.
NO hard-coded IPs, ports, URLs, or credentials.
"""

import json
import logging
from functools import lru_cache
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class ExternalAgentConfig(BaseModel):
    """Configuration for an external agent."""
    name: str = Field(..., description="Agent name/identifier")
    url: str = Field(..., description="Agent base URL")
    auth_token: Optional[str] = Field(None, description="Authentication token")
    timeout_seconds: int = Field(default=30, description="Request timeout")
    enabled: bool = Field(default=True, description="Whether agent is enabled")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ToolConfig(BaseModel):
    """Configuration for a tool."""
    name: str = Field(..., description="Tool name/identifier")
    type: str = Field(..., description="Tool type (http_request, web_search, code_executor, etc.)")
    config: Dict[str, Any] = Field(default_factory=dict, description="Tool-specific configuration")
    enabled: bool = Field(default=True, description="Whether tool is enabled")
    description: Optional[str] = Field(None, description="Tool description")


class DataSourceConfig(BaseModel):
    """Configuration for a data source."""
    name: str = Field(..., description="Data source name/identifier")
    type: str = Field(..., description="Data source type (postgres, cubejs, api, etc.)")
    url: str = Field(..., description="Data source URL/endpoint")
    auth_token: Optional[str] = Field(None, description="Authentication token")
    timeout_seconds: int = Field(default=30, description="Request timeout")
    enabled: bool = Field(default=True, description="Whether datasource is enabled")
    config: Dict[str, Any] = Field(default_factory=dict, description="Additional configuration")


class RouterConfig(BaseModel):
    """Configuration for an intent router."""
    name: str = Field(..., description="Router name/identifier")
    type: str = Field(..., description="Router type (rule_based, llm_based, hybrid, keyword)")
    enabled: bool = Field(default=True, description="Whether router is enabled")
    priority: int = Field(default=0, description="Router priority (higher = evaluated first)")
    rules: Dict[str, Any] = Field(default_factory=dict, description="Router-specific rules/patterns")
    description: Optional[str] = Field(None, description="Router description")


class PlannerConfig(BaseModel):
    """Configuration for a task planner."""
    name: str = Field(..., description="Planner name/identifier")
    type: str = Field(..., description="Planner type (sequential, parallel, conditional, llm_based)")
    enabled: bool = Field(default=True, description="Whether planner is enabled")
    strategy: str = Field(default="sequential", description="Planning strategy")
    templates: Dict[str, Any] = Field(default_factory=dict, description="Plan templates for different intents")
    description: Optional[str] = Field(None, description="Planner description")


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    The GUI will manage and inject these values at runtime.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )
    
    # Application Settings
    app_name: str = Field(default="ZainOne Orchestrator Studio", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # API Settings
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_prefix: str = Field(default="/v1", description="API prefix")
    cors_origins: str = Field(default="http://localhost:3000", description="CORS allowed origins (comma-separated)")
    
    # LLM Configuration
    llm_base_url: Optional[str] = Field(default=None, description="LLM server base URL")
    llm_default_model: Optional[str] = Field(default=None, description="Default LLM model name")
    llm_timeout_seconds: int = Field(default=60, description="LLM request timeout in seconds")
    llm_max_retries: int = Field(default=3, description="Maximum retry attempts for LLM calls")
    llm_temperature: float = Field(default=0.7, description="Default temperature for LLM")
    llm_max_tokens: Optional[int] = Field(default=None, description="Maximum tokens for LLM response")
    llm_api_key: Optional[str] = Field(default=None, description="LLM API key")
    
    # External Agent Configuration
    external_agent_base_url: Optional[str] = Field(default=None, description="External agent base URL (e.g., zain_agent)")
    external_agent_auth_token: Optional[str] = Field(default=None, description="External agent authentication token")
    external_agent_timeout_seconds: int = Field(default=30, description="External agent request timeout")
    
    # Data Source Configuration
    datasource_base_url: Optional[str] = Field(default=None, description="Data source base URL")
    datasource_auth_token: Optional[str] = Field(default=None, description="Data source authentication token")
    datasource_timeout_seconds: int = Field(default=30, description="Data source request timeout")
    
    # PostgreSQL Configuration
    postgres_host: Optional[str] = Field(default=None, description="PostgreSQL host")
    postgres_port: int = Field(default=5432, description="PostgreSQL port")
    postgres_user: Optional[str] = Field(default=None, description="PostgreSQL user")
    postgres_password: Optional[str] = Field(default=None, description="PostgreSQL password")
    postgres_database: Optional[str] = Field(default=None, description="PostgreSQL database name")
    postgres_dsn: Optional[str] = Field(default=None, description="PostgreSQL DSN (overrides individual fields)")
    
    # Redis Configuration
    redis_host: Optional[str] = Field(default=None, description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_password: Optional[str] = Field(default=None, description="Redis password")
    redis_db: int = Field(default=0, description="Redis database number")
    redis_url: Optional[str] = Field(default=None, description="Redis URL (overrides individual fields)")
    redis_ttl_seconds: int = Field(default=3600, description="Default Redis TTL in seconds")
    
    # Vector Database Configuration
    vector_db_type: str = Field(default="chroma", description="Vector DB type (chroma, pinecone, weaviate, etc.)")
    vector_db_url: Optional[str] = Field(default=None, description="Vector database URL")
    vector_db_api_key: Optional[str] = Field(default=None, description="Vector database API key")
    vector_db_collection: str = Field(default="orchestrator_vectors", description="Default vector collection name")
    vector_db_dimension: int = Field(default=1536, description="Vector dimension")
    
    # Memory Configuration
    memory_enabled: bool = Field(default=True, description="Enable conversation memory")
    memory_max_messages: int = Field(default=50, description="Maximum messages to keep in memory")
    memory_summary_enabled: bool = Field(default=True, description="Enable conversation summarization")
    
    # Cache Configuration
    cache_enabled: bool = Field(default=True, description="Enable response caching")
    cache_ttl_seconds: int = Field(default=3600, description="Cache TTL in seconds")
    
    # Multi-Agent Configuration
    external_agents: Dict[str, ExternalAgentConfig] = Field(
        default_factory=dict,
        description="Dictionary of external agent configurations"
    )
    
    # Multi-Tool Configuration
    tools: Dict[str, ToolConfig] = Field(
        default_factory=dict,
        description="Dictionary of tool configurations"
    )
    tools_config_path: Optional[str] = Field(default=None, description="Path to tools configuration file")
    tools_execution_timeout: int = Field(default=30, description="Tool execution timeout in seconds")
    tools_max_concurrent: int = Field(default=5, description="Maximum concurrent tool executions")
    
    # Multi-DataSource Configuration
    datasources: Dict[str, DataSourceConfig] = Field(
        default_factory=dict,
        description="Dictionary of data source configurations"
    )
    datasources_config_path: Optional[str] = Field(default=None, description="Path to datasources configuration file")
    
    # Router Configuration
    routers: Dict[str, RouterConfig] = Field(
        default_factory=dict,
        description="Dictionary of router configurations"
    )
    routers_config_path: Optional[str] = Field(default=None, description="Path to routers configuration file")
    
    # Planner Configuration
    planners: Dict[str, PlannerConfig] = Field(
        default_factory=dict,
        description="Dictionary of planner configurations"
    )
    planners_config_path: Optional[str] = Field(default=None, description="Path to planners configuration file")
    
    # Grounding Configuration
    grounding_enabled: bool = Field(default=True, description="Enable grounding/RAG")
    grounding_top_k: int = Field(default=5, description="Top K results for retrieval")
    grounding_similarity_threshold: float = Field(default=0.7, description="Similarity threshold for retrieval")
    
    # Orchestration Configuration
    orchestration_max_iterations: int = Field(default=10, description="Maximum graph iterations")
    orchestration_timeout_seconds: int = Field(default=300, description="Overall orchestration timeout")
    
    # Monitoring Configuration
    monitoring_enabled: bool = Field(default=True, description="Enable monitoring and metrics")
    monitoring_export_interval: int = Field(default=60, description="Metrics export interval in seconds")
    
    # Security Configuration
    auth_enabled: bool = Field(default=False, description="Enable authentication")
    auth_secret_key: Optional[str] = Field(default=None, description="JWT secret key")
    auth_algorithm: str = Field(default="HS256", description="JWT algorithm")
    auth_token_expire_minutes: int = Field(default=30, description="Token expiration in minutes")
    
    def get_postgres_dsn(self) -> Optional[str]:
        """Build PostgreSQL DSN from components if not provided directly."""
        if self.postgres_dsn:
            return self.postgres_dsn
        
        if all([self.postgres_host, self.postgres_user, self.postgres_password, self.postgres_database]):
            return (
                f"postgresql://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"
            )
        
        return None
    
    def get_redis_url(self) -> Optional[str]:
        """Build Redis URL from components if not provided directly."""
        if self.redis_url:
            return self.redis_url
        
        if self.redis_host:
            auth = f":{self.redis_password}@" if self.redis_password else ""
            return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"
        
        return None
    
    def get_cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
    
    def load_agents_from_file(self, filepath: str) -> None:
        """
        Load external agent configurations from JSON file.
        
        Args:
            filepath: Path to JSON file containing agent configs
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                agents_data = data.get('agents', [])
                
                for agent_data in agents_data:
                    agent_config = ExternalAgentConfig(**agent_data)
                    self.external_agents[agent_config.name] = agent_config
                
                logger.info(f"Loaded {len(agents_data)} agent configurations from {filepath}")
        except FileNotFoundError:
            logger.warning(f"Agent config file not found: {filepath}")
        except Exception as e:
            logger.error(f"Error loading agent configs from {filepath}: {str(e)}")
    
    def load_tools_from_file(self, filepath: str) -> None:
        """
        Load tool configurations from JSON file.
        
        Args:
            filepath: Path to JSON file containing tool configs
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                tools_data = data.get('tools', [])
                
                for tool_data in tools_data:
                    tool_config = ToolConfig(**tool_data)
                    self.tools[tool_config.name] = tool_config
                
                logger.info(f"Loaded {len(tools_data)} tool configurations from {filepath}")
        except FileNotFoundError:
            logger.warning(f"Tool config file not found: {filepath}")
        except Exception as e:
            logger.error(f"Error loading tool configs from {filepath}: {str(e)}")
    
    def load_datasources_from_file(self, filepath: str) -> None:
        """
        Load data source configurations from JSON file.
        
        Args:
            filepath: Path to JSON file containing datasource configs
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                datasources_data = data.get('datasources', [])
                
                for ds_data in datasources_data:
                    ds_config = DataSourceConfig(**ds_data)
                    self.datasources[ds_config.name] = ds_config
                
                logger.info(f"Loaded {len(datasources_data)} datasource configurations from {filepath}")
        except FileNotFoundError:
            logger.warning(f"Datasource config file not found: {filepath}")
        except Exception as e:
            logger.error(f"Error loading datasource configs from {filepath}: {str(e)}")
    
    def load_routers_from_file(self, filepath: str) -> None:
        """
        Load router configurations from JSON file.
        
        Args:
            filepath: Path to JSON file containing router configs
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                routers_data = data.get('routers', [])
                
                for router_data in routers_data:
                    router_config = RouterConfig(**router_data)
                    self.routers[router_config.name] = router_config
                
                logger.info(f"Loaded {len(routers_data)} router configurations from {filepath}")
        except FileNotFoundError:
            logger.warning(f"Router config file not found: {filepath}")
        except Exception as e:
            logger.error(f"Error loading router configs from {filepath}: {str(e)}")
    
    def load_planners_from_file(self, filepath: str) -> None:
        """
        Load planner configurations from JSON file.
        
        Args:
            filepath: Path to JSON file containing planner configs
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                planners_data = data.get('planners', [])
                
                for planner_data in planners_data:
                    planner_config = PlannerConfig(**planner_data)
                    self.planners[planner_config.name] = planner_config
                
                logger.info(f"Loaded {len(planners_data)} planner configurations from {filepath}")
        except FileNotFoundError:
            logger.warning(f"Planner config file not found: {filepath}")
        except Exception as e:
            logger.error(f"Error loading planner configs from {filepath}: {str(e)}")
    
    def get_agent(self, name: str) -> Optional[ExternalAgentConfig]:
        """Get agent configuration by name."""
        return self.external_agents.get(name)
    
    def get_tool(self, name: str) -> Optional[ToolConfig]:
        """Get tool configuration by name."""
        return self.tools.get(name)
    
    def get_datasource(self, name: str) -> Optional[DataSourceConfig]:
        """Get datasource configuration by name."""
        return self.datasources.get(name)
    
    def get_router(self, name: str) -> Optional[RouterConfig]:
        """Get router configuration by name."""
        return self.routers.get(name)
    
    def get_planner(self, name: str) -> Optional[PlannerConfig]:
        """Get planner configuration by name."""
        return self.planners.get(name)
    
    def add_agent(self, agent: ExternalAgentConfig) -> None:
        """Add or update an agent configuration."""
        self.external_agents[agent.name] = agent
        self._persist_agents()
    
    def add_tool(self, tool: ToolConfig) -> None:
        """Add or update a tool configuration."""
        self.tools[tool.name] = tool
        self._persist_tools()
    
    def add_datasource(self, datasource: DataSourceConfig) -> None:
        """Add or update a datasource configuration."""
        self.datasources[datasource.name] = datasource
        self._persist_datasources()
    
    def add_router(self, router: RouterConfig) -> None:
        """Add or update a router configuration."""
        self.routers[router.name] = router
        self._persist_routers()
    
    def add_planner(self, planner: PlannerConfig) -> None:
        """Add or update a planner configuration."""
        self.planners[planner.name] = planner
        self._persist_planners()
    
    def remove_agent(self, name: str) -> bool:
        """Remove an agent configuration. Returns True if removed."""
        if name in self.external_agents:
            del self.external_agents[name]
            self._persist_agents()
            return True
        return False
    
    def remove_tool(self, name: str) -> bool:
        """Remove a tool configuration. Returns True if removed."""
        if name in self.tools:
            del self.tools[name]
            self._persist_tools()
            return True
        return False
    
    def remove_datasource(self, name: str) -> bool:
        """Remove a datasource configuration. Returns True if removed."""
        if name in self.datasources:
            del self.datasources[name]
            self._persist_datasources()
            return True
        return False
    
    def remove_router(self, name: str) -> bool:
        """Remove a router configuration. Returns True if removed."""
        if name in self.routers:
            del self.routers[name]
            self._persist_routers()
            return True
        return False
    
    def remove_planner(self, name: str) -> bool:
        """Remove a planner configuration. Returns True if removed."""
        if name in self.planners:
            del self.planners[name]
            self._persist_planners()
            return True
        return False
    
    def _persist_tools(self) -> None:
        """Persist tools configuration to file."""
        try:
            from pathlib import Path
            import os
            # Get the directory where the backend is running from
            config_dir = Path("config")
            config_dir.mkdir(parents=True, exist_ok=True)
            
            tools_file = config_dir / "tools.json"
            tools_list = [tool.dict() for tool in self.tools.values()]
            
            with open(tools_file, 'w') as f:
                json.dump({"tools": tools_list}, f, indent=2)
            
            logger.info(f"Persisted {len(tools_list)} tools to {tools_file.absolute()}")
        except Exception as e:
            logger.error(f"Error persisting tools: {str(e)}")
    
    def _persist_datasources(self) -> None:
        """Persist datasources configuration to file."""
        try:
            from pathlib import Path
            config_dir = Path("config")
            config_dir.mkdir(parents=True, exist_ok=True)
            
            datasources_file = config_dir / "datasources.json"
            datasources_list = [ds.dict() for ds in self.datasources.values()]
            
            with open(datasources_file, 'w') as f:
                json.dump({"datasources": datasources_list}, f, indent=2)
            
            logger.info(f"Persisted {len(datasources_list)} datasources to {datasources_file.absolute()}")
        except Exception as e:
            logger.error(f"Error persisting datasources: {str(e)}")
    
    def _persist_agents(self) -> None:
        """Persist agents configuration to file."""
        try:
            from pathlib import Path
            config_dir = Path("config")
            config_dir.mkdir(parents=True, exist_ok=True)
            
            agents_file = config_dir / "agents.json"
            agents_list = [agent.dict() for agent in self.external_agents.values()]
            
            with open(agents_file, 'w') as f:
                json.dump({"agents": agents_list}, f, indent=2)
            
            logger.info(f"Persisted {len(agents_list)} agents to {agents_file.absolute()}")
        except Exception as e:
            logger.error(f"Error persisting agents: {str(e)}")
    
    def _persist_routers(self) -> None:
        """Persist routers configuration to file."""
        try:
            from pathlib import Path
            config_dir = Path("config")
            config_dir.mkdir(parents=True, exist_ok=True)
            
            routers_file = config_dir / "routers.json"
            routers_list = [router.dict() for router in self.routers.values()]
            
            with open(routers_file, 'w') as f:
                json.dump({"routers": routers_list}, f, indent=2)
            
            logger.info(f"Persisted {len(routers_list)} routers to {routers_file.absolute()}")
        except Exception as e:
            logger.error(f"Error persisting routers: {str(e)}")
    
    def _persist_planners(self) -> None:
        """Persist planners configuration to file."""
        try:
            from pathlib import Path
            config_dir = Path("config")
            config_dir.mkdir(parents=True, exist_ok=True)
            
            planners_file = config_dir / "planners.json"
            planners_list = [planner.dict() for planner in self.planners.values()]
            
            with open(planners_file, 'w') as f:
                json.dump({"planners": planners_list}, f, indent=2)
            
            logger.info(f"Persisted {len(planners_list)} planners to {planners_file.absolute()}")
        except Exception as e:
            logger.error(f"Error persisting planners: {str(e)}")


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    This function is cached to avoid re-reading environment variables
    on every call. The cache is cleared when the process restarts.
    """
    settings = Settings()
    
    # Load configurations from files if paths are provided
    if settings.tools_config_path:
        settings.load_tools_from_file(settings.tools_config_path)
    else:
        # Try to load from default location
        from pathlib import Path
        default_tools_file = Path("config/tools.json")
        if default_tools_file.exists():
            settings.load_tools_from_file(str(default_tools_file))
    
    if settings.datasources_config_path:
        settings.load_datasources_from_file(settings.datasources_config_path)
    else:
        # Try to load from default location
        from pathlib import Path
        default_datasources_file = Path("config/datasources.json")
        if default_datasources_file.exists():
            settings.load_datasources_from_file(str(default_datasources_file))
    
    # Load routers
    if settings.routers_config_path:
        settings.load_routers_from_file(settings.routers_config_path)
    else:
        from pathlib import Path
        default_routers_file = Path("config/routers.json")
        if default_routers_file.exists():
            settings.load_routers_from_file(str(default_routers_file))
    
    # Load planners
    if settings.planners_config_path:
        settings.load_planners_from_file(settings.planners_config_path)
    else:
        from pathlib import Path
        default_planners_file = Path("config/planners.json")
        if default_planners_file.exists():
            settings.load_planners_from_file(str(default_planners_file))
    
    # Backward compatibility: Create default agent from single-agent config
    if settings.external_agent_base_url and "default" not in settings.external_agents:
        default_agent = ExternalAgentConfig(
            name="default",
            url=settings.external_agent_base_url,
            auth_token=settings.external_agent_auth_token,
            timeout_seconds=settings.external_agent_timeout_seconds
        )
        settings.external_agents["default"] = default_agent
    
    # Backward compatibility: Create default datasource from single-datasource config
    if settings.datasource_base_url and "default" not in settings.datasources:
        default_datasource = DataSourceConfig(
            name="default",
            type="api",
            url=settings.datasource_base_url,
            auth_token=settings.datasource_auth_token,
            timeout_seconds=settings.datasource_timeout_seconds
        )
        settings.datasources["default"] = default_datasource
    
    return settings


def clear_settings_cache():
    """Clear the settings cache to force reload."""
    get_settings.cache_clear()
