"""
External Agent Client - Interface for external agents (e.g., zain_agent).

Uses Settings for configuration - no hard-coded endpoints.
Supports multiple agents dynamically configured.
"""

import logging
from typing import Dict, Any, Optional, List
import httpx
from ..config import Settings, ExternalAgentConfig

logger = logging.getLogger(__name__)


class ExternalAgentClient:
    """
    Client for interacting with external agents.
    
    Supports multiple agents, authentication, timeout handling, and error recovery.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize external agent client with settings.
        
        Args:
            settings: Application settings containing agent configurations
        """
        self.settings = settings
        
        # For backward compatibility
        self.base_url = settings.external_agent_base_url
        self.auth_token = settings.external_agent_auth_token
        self.timeout = settings.external_agent_timeout_seconds
        
        # HTTP clients per agent (lazy initialization)
        self._clients: Dict[str, httpx.AsyncClient] = {}
    
    def _get_headers(self, auth_token: Optional[str] = None) -> Dict[str, str]:
        """Build request headers with authentication."""
        headers = {
            "Content-Type": "application/json",
        }
        
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        
        return headers
    
    async def _get_client(self, agent_name: str) -> tuple[httpx.AsyncClient, ExternalAgentConfig]:
        """
        Get or create HTTP client for a specific agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Tuple of (HTTP client, agent config)
            
        Raises:
            ValueError: If agent not found
        """
        agent_config = self.settings.get_agent(agent_name)
        
        if not agent_config:
            raise ValueError(f"Agent '{agent_name}' not found in configuration")
        
        if not agent_config.enabled:
            raise ValueError(f"Agent '{agent_name}' is disabled")
        
        if agent_name not in self._clients:
            self._clients[agent_name] = httpx.AsyncClient(
                timeout=httpx.Timeout(agent_config.timeout_seconds),
                headers=self._get_headers(agent_config.auth_token)
            )
        
        return self._clients[agent_name], agent_config
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """
        List all configured agents.
        
        Returns:
            List of agent information dicts
        """
        agents = []
        for name, config in self.settings.external_agents.items():
            agents.append({
                "name": name,
                "url": config.url,
                "enabled": config.enabled,
                "timeout_seconds": config.timeout_seconds,
                "metadata": config.metadata
            })
        return agents
    
    async def call_agent(
        self,
        name: str,
        payload: Dict[str, Any],
        endpoint: str = "/execute",
        method: str = "POST"
    ) -> Dict[str, Any]:
        """
        Call a specific agent by name.
        
        Args:
            name: Agent name
            payload: Request payload
            endpoint: API endpoint path
            method: HTTP method
            
        Returns:
            Response data
        """
        try:
            client, config = await self._get_client(name)
            url = f"{config.url.rstrip('/')}/{endpoint.lstrip('/')}"
            
            logger.info(f"[ExternalAgent:{name}] Calling {method} {url}")
            
            if method.upper() == "GET":
                response = await client.get(url, params=payload)
            elif method.upper() == "POST":
                response = await client.post(url, json=payload)
            elif method.upper() == "PUT":
                response = await client.put(url, json=payload)
            elif method.upper() == "DELETE":
                response = await client.delete(url, json=payload)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"[ExternalAgent:{name}] Success")
            
            return {
                "success": True,
                "data": result,
                "agent": name,
                "status_code": response.status_code
            }
            
        except ValueError as e:
            logger.error(f"[ExternalAgent:{name}] Configuration error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "agent": name,
                "status_code": 400
            }
        except httpx.HTTPStatusError as e:
            logger.error(f"[ExternalAgent:{name}] HTTP error: {e.response.status_code}")
            return {
                "success": False,
                "error": str(e),
                "agent": name,
                "status_code": e.response.status_code
            }
        except httpx.TimeoutException as e:
            logger.error(f"[ExternalAgent:{name}] Timeout: {str(e)}")
            return {
                "success": False,
                "error": "Request timeout",
                "agent": name,
                "status_code": 408
            }
        except Exception as e:
            logger.error(f"[ExternalAgent:{name}] Unexpected error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "agent": name,
                "status_code": 500
            }
    
    async def call(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        method: str = "POST"
    ) -> Dict[str, Any]:
        """
        Call external agent endpoint.
        
        Args:
            endpoint: API endpoint path (e.g., '/analyze', '/execute')
            payload: Request payload
            method: HTTP method (GET, POST, PUT, etc.)
            
        Returns:
            Response data
            
        Raises:
            ValueError: If base URL not configured
            httpx.HTTPError: If request fails
        """
        if not self.base_url:
            raise ValueError("External agent base URL not configured in settings")
        
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        logger.info(f"[ExternalAgent] Calling {method} {url}")
        
        try:
            if method.upper() == "GET":
                response = await self.client.get(url, params=payload)
            elif method.upper() == "POST":
                response = await self.client.post(url, json=payload)
            elif method.upper() == "PUT":
                response = await self.client.put(url, json=payload)
            elif method.upper() == "DELETE":
                response = await self.client.delete(url, json=payload)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"[ExternalAgent] Success: {method} {url}")
            
            return {
                "success": True,
                "data": result,
                "status_code": response.status_code
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"[ExternalAgent] HTTP error: {e.response.status_code} - {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "status_code": e.response.status_code
            }
            
        except httpx.TimeoutException as e:
            logger.error(f"[ExternalAgent] Timeout: {str(e)}")
            return {
                "success": False,
                "error": "Request timeout",
                "status_code": 408
            }
            
        except Exception as e:
            logger.error(f"[ExternalAgent] Unexpected error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "status_code": 500
            }
    
    async def test_agent(self, name: str) -> Dict[str, Any]:
        """
        Test connectivity to a specific agent.
        
        Args:
            name: Agent name
            
        Returns:
            Test result with status and details
        """
        try:
            client, config = await self._get_client(name)
            url = f"{config.url.rstrip('/')}/health"
            
            logger.info(f"[ExternalAgent:{name}] Testing connectivity to {url}")
            
            response = await client.get(url)
            
            return {
                "success": response.status_code == 200,
                "agent": name,
                "url": config.url,
                "status_code": response.status_code,
                "message": "Agent is reachable" if response.status_code == 200 else "Agent returned non-200 status",
                "response_time_ms": response.elapsed.total_seconds() * 1000 if hasattr(response, 'elapsed') else None
            }
            
        except ValueError as e:
            return {
                "success": False,
                "agent": name,
                "error": str(e),
                "message": "Agent not found or disabled"
            }
        except httpx.TimeoutException:
            return {
                "success": False,
                "agent": name,
                "error": "Connection timeout",
                "message": "Agent did not respond within timeout period"
            }
        except Exception as e:
            return {
                "success": False,
                "agent": name,
                "error": str(e),
                "message": "Failed to connect to agent"
            }
    
    async def health_check(self, name: Optional[str] = None) -> bool:
        """
        Check if agent(s) are healthy.
        
        Args:
            name: Specific agent name, or None to check default/all
            
        Returns:
            True if agent is healthy, False otherwise
        """
        if name:
            result = await self.test_agent(name)
            return result["success"]
        
        # Backward compatibility: check default agent
        if self.base_url:
            try:
                client = httpx.AsyncClient(timeout=httpx.Timeout(5.0))
                response = await client.get(f"{self.base_url}/health")
                await client.aclose()
                return response.status_code == 200
            except Exception as e:
                logger.warning(f"[ExternalAgent] Health check failed: {str(e)}")
                return False
        
        return False
    
    async def close(self):
        """Close all HTTP clients."""
        for client in self._clients.values():
            await client.aclose()
        self._clients.clear()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
