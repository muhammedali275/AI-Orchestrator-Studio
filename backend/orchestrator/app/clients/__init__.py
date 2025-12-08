"""
Client abstractions for external services.

All clients use Settings for configuration - no hard-coded endpoints.
"""

from .llm_client import LLMClient
from .external_agent_client import ExternalAgentClient
from .datasource_client import DataSourceClient

__all__ = [
    "LLMClient",
    "ExternalAgentClient",
    "DataSourceClient",
]
