"""
Configuration settings for AIpanel.

Uses pydantic BaseSettings to load configuration from environment variables.
No hard-coded credentials or connection strings.
"""

import os
from typing import Optional, List, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All sensitive configuration comes from environment variables or .env file.
    NO hard-coded IPs, ports, URLs, or credentials.
    """
    
    # Application Settings
    AIPANEL_PORT: int = Field(default=8000, description="Port to run the AIpanel server on")
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    
    # TLS Settings
    TLS_ENABLED: bool = Field(default=False, description="Enable TLS")
    TLS_CERT_PATH: Optional[str] = Field(default=None, description="Path to TLS certificate")
    TLS_KEY_PATH: Optional[str] = Field(default=None, description="Path to TLS key")
    
    # Database Settings
    DB_CONNECTION_STRING: str = Field(
        default="sqlite:///./aipanel.db", 
        description="Database connection string"
    )
    
    # LLM Settings
    DEFAULT_AGENT_NAME: str = Field(default="example_agent", description="Default agent name")
    LLM_BASE_URL: Optional[str] = Field(default=None, description="LLM server base URL")
    LLM_API_KEY: Optional[str] = Field(default=None, description="LLM API key")
    LLM_DEFAULT_MODEL: Optional[str] = Field(default=None, description="Default LLM model")
    LLM_TEMPERATURE: float = Field(default=0.7, description="LLM temperature")
    LLM_MAX_TOKENS: Optional[int] = Field(default=None, description="Maximum tokens for LLM response")
    LLM_TIMEOUT_SECONDS: int = Field(default=60, description="LLM request timeout in seconds")
    LLM_MAX_RETRIES: int = Field(default=3, description="Maximum retry attempts for LLM calls")
    
    # API Settings
    API_PREFIX: str = Field(default="/api", description="API prefix")
    CORS_ORIGINS: str = Field(default="http://localhost:3000", description="CORS allowed origins (comma-separated)")
    
    # Security Settings
    API_KEY_HEADER: str = Field(default="X-API-Key", description="API key header name")
    JWT_SECRET_KEY: str = Field(default="CHANGE_ME_IN_PRODUCTION", description="JWT secret key")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_EXPIRATION_MINUTES: int = Field(default=30, description="JWT expiration in minutes")
    
    # Memory Settings
    MEMORY_ENABLED: bool = Field(default=True, description="Enable conversation memory")
    MEMORY_MAX_MESSAGES: int = Field(default=50, description="Maximum messages to keep in memory")
    
    # Cache Settings
    CACHE_ENABLED: bool = Field(default=True, description="Enable response caching")
    CACHE_TTL_SECONDS: int = Field(default=3600, description="Cache TTL in seconds")
    
    # Redis Settings (optional)
    REDIS_HOST: Optional[str] = Field(default=None, description="Redis host")
    REDIS_PORT: int = Field(default=6379, description="Redis port")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis password")
    REDIS_DB: int = Field(default=0, description="Redis database number")
    
    # Tool Settings
    TOOLS_EXECUTION_TIMEOUT: int = Field(default=30, description="Tool execution timeout in seconds")
    TOOLS_MAX_CONCURRENT: int = Field(default=5, description="Maximum concurrent tool executions")
    
    # Orchestration Settings
    ORCHESTRATION_MAX_ITERATIONS: int = Field(default=10, description="Maximum graph iterations")
    ORCHESTRATION_TIMEOUT_SECONDS: int = Field(default=300, description="Overall orchestration timeout")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @validator("CORS_ORIGINS")
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in v.split(",") if origin.strip()]
    
    def get_redis_url(self) -> Optional[str]:
        """Build Redis URL from components if Redis is configured."""
        if not self.REDIS_HOST:
            return None
        
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


# Singleton instance
settings = Settings()


def get_settings() -> Settings:
    """
    Get settings instance.
    
    Returns:
        Settings instance
    """
    return settings
