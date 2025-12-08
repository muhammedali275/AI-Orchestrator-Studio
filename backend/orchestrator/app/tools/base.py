"""
Base tool abstractions.

Defines the interface for all tools in the orchestration system.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class ToolStatus(Enum):
    """Tool execution status."""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass
class ToolResult:
    """
    Result of tool execution.
    
    Attributes:
        status: Execution status
        output: Tool output data
        error: Error message if failed
        metadata: Additional metadata
    """
    status: ToolStatus
    output: Any
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def is_success(self) -> bool:
        """Check if execution was successful."""
        return self.status == ToolStatus.SUCCESS
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "metadata": self.metadata or {}
        }


class BaseTool(ABC):
    """
    Base class for all tools.
    
    Tools are executable components that can be invoked by the orchestrator.
    """
    
    def __init__(self, name: str, description: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize tool.
        
        Args:
            name: Tool name
            description: Tool description
            config: Tool-specific configuration
        """
        self.name = name
        self.description = description
        self.config = config or {}
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool.
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            ToolResult with execution outcome
        """
        pass
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """
        Get tool schema for LLM function calling.
        
        Returns:
            JSON schema describing tool parameters
        """
        pass
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """
        Validate tool parameters.
        
        Args:
            params: Parameters to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Default implementation - override for custom validation
        return True
    
    async def __call__(self, **kwargs) -> ToolResult:
        """Allow tool to be called directly."""
        return await self.execute(**kwargs)
    
    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(name='{self.name}')"
