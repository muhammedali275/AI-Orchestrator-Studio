"""
Data Source Client - Interface for data sources and databases.

Uses Settings for configuration - no hard-coded endpoints.
Supports multiple datasources dynamically configured.
"""

import logging
from typing import Dict, Any, Optional, List
import httpx
from ..config import Settings, DataSourceConfig

logger = logging.getLogger(__name__)


class DataSourceClient:
    """
    Client for interacting with data sources.
    
    Supports multiple datasources, querying, authentication, and error handling.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize data source client with settings.
        
        Args:
            settings: Application settings containing datasource configurations
        """
        self.settings = settings
        
        # For backward compatibility
        self.base_url = settings.datasource_base_url
        self.auth_token = settings.datasource_auth_token
        self.timeout = settings.datasource_timeout_seconds
        
        # HTTP clients per datasource (lazy initialization)
        self._clients: Dict[str, httpx.AsyncClient] = {}
    
    def _get_headers(self, auth_token: Optional[str] = None) -> Dict[str, str]:
        """Build request headers with authentication."""
        headers = {
            "Content-Type": "application/json",
        }
        
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        
        return headers
    
    async def _get_client(self, datasource_name: str) -> tuple[httpx.AsyncClient, DataSourceConfig]:
        """
        Get or create HTTP client for a specific datasource.
        
        Args:
            datasource_name: Name of the datasource
            
        Returns:
            Tuple of (HTTP client, datasource config)
            
        Raises:
            ValueError: If datasource not found
        """
        ds_config = self.settings.get_datasource(datasource_name)
        
        if not ds_config:
            raise ValueError(f"Datasource '{datasource_name}' not found in configuration")
        
        if not ds_config.enabled:
            raise ValueError(f"Datasource '{datasource_name}' is disabled")
        
        if datasource_name not in self._clients:
            self._clients[datasource_name] = httpx.AsyncClient(
                timeout=httpx.Timeout(ds_config.timeout_seconds),
                headers=self._get_headers(ds_config.auth_token)
            )
        
        return self._clients[datasource_name], ds_config
    
    def list_datasources(self) -> List[Dict[str, Any]]:
        """
        List all configured datasources.
        
        Returns:
            List of datasource information dicts
        """
        datasources = []
        for name, config in self.settings.datasources.items():
            datasources.append({
                "name": name,
                "type": config.type,
                "url": config.url,
                "enabled": config.enabled,
                "timeout_seconds": config.timeout_seconds,
                "config": config.config
            })
        return datasources
    
    async def query_datasource(
        self,
        name: str,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a query against a specific datasource.
        
        Args:
            name: Datasource name
            query: Query string (SQL, GraphQL, etc.)
            parameters: Query parameters
            
        Returns:
            Query results
        """
        try:
            client, config = await self._get_client(name)
            url = f"{config.url.rstrip('/')}/query"
            
            payload = {
                "query": query,
                "parameters": parameters or {}
            }
            
            logger.info(f"[DataSource:{name}] Executing query")
            
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"[DataSource:{name}] Query successful")
            
            return {
                "success": True,
                "datasource": name,
                "data": result.get("data", []),
                "row_count": result.get("row_count", 0),
                "metadata": result.get("metadata", {})
            }
            
        except ValueError as e:
            logger.error(f"[DataSource:{name}] Configuration error: {str(e)}")
            return {
                "success": False,
                "datasource": name,
                "error": str(e),
                "data": []
            }
        except httpx.HTTPStatusError as e:
            logger.error(f"[DataSource:{name}] HTTP error: {e.response.status_code}")
            return {
                "success": False,
                "datasource": name,
                "error": str(e),
                "data": []
            }
        except Exception as e:
            logger.error(f"[DataSource:{name}] Error: {str(e)}")
            return {
                "success": False,
                "datasource": name,
                "error": str(e),
                "data": []
            }
    
    async def query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a query against the data source.
        
        Args:
            query: Query string (SQL, GraphQL, etc.)
            parameters: Query parameters
            
        Returns:
            Query results
            
        Raises:
            ValueError: If base URL not configured
        """
        if not self.base_url:
            raise ValueError("Data source base URL not configured in settings")
        
        url = f"{self.base_url}/query"
        
        payload = {
            "query": query,
            "parameters": parameters or {}
        }
        
        logger.info(f"[DataSource] Executing query")
        
        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"[DataSource] Query successful")
            
            return {
                "success": True,
                "data": result.get("data", []),
                "row_count": result.get("row_count", 0),
                "metadata": result.get("metadata", {})
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"[DataSource] HTTP error: {e.response.status_code} - {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": []
            }
            
        except Exception as e:
            logger.error(f"[DataSource] Error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": []
            }
    
    async def get_schema(self, name: str) -> Dict[str, Any]:
        """
        Get schema information for a specific datasource.
        
        Args:
            name: Datasource name
            
        Returns:
            Schema metadata
        """
        try:
            client, config = await self._get_client(name)
            url = f"{config.url.rstrip('/')}/schema"
            
            response = await client.get(url)
            response.raise_for_status()
            result = response.json()
            
            return {
                "success": True,
                "datasource": name,
                "schema": result
            }
            
        except Exception as e:
            logger.error(f"[DataSource:{name}] Schema fetch error: {str(e)}")
            return {
                "success": False,
                "datasource": name,
                "error": str(e)
            }
    
    async def get_tables(self, name: str) -> List[str]:
        """
        Get list of available tables/collections for a datasource.
        
        Args:
            name: Datasource name
            
        Returns:
            List of table names
        """
        try:
            client, config = await self._get_client(name)
            url = f"{config.url.rstrip('/')}/tables"
            
            response = await client.get(url)
            response.raise_for_status()
            result = response.json()
            
            return result.get("tables", [])
            
        except Exception as e:
            logger.error(f"[DataSource:{name}] Tables fetch error: {str(e)}")
            return []
    
    async def test_datasource(self, name: str) -> Dict[str, Any]:
        """
        Test connectivity to a specific datasource.
        
        Args:
            name: Datasource name
            
        Returns:
            Test result with status and details
        """
        try:
            client, config = await self._get_client(name)
            url = f"{config.url.rstrip('/')}/health"
            
            logger.info(f"[DataSource:{name}] Testing connectivity to {url}")
            
            response = await client.get(url)
            
            return {
                "success": response.status_code == 200,
                "datasource": name,
                "type": config.type,
                "url": config.url,
                "status_code": response.status_code,
                "message": "Datasource is reachable" if response.status_code == 200 else "Datasource returned non-200 status",
                "response_time_ms": response.elapsed.total_seconds() * 1000 if hasattr(response, 'elapsed') else None
            }
            
        except ValueError as e:
            return {
                "success": False,
                "datasource": name,
                "error": str(e),
                "message": "Datasource not found or disabled"
            }
        except httpx.TimeoutException:
            return {
                "success": False,
                "datasource": name,
                "error": "Connection timeout",
                "message": "Datasource did not respond within timeout period"
            }
        except Exception as e:
            return {
                "success": False,
                "datasource": name,
                "error": str(e),
                "message": "Failed to connect to datasource"
            }
    
    async def health_check(self, name: Optional[str] = None) -> bool:
        """
        Check if datasource(s) are accessible.
        
        Args:
            name: Specific datasource name, or None to check default
            
        Returns:
            True if accessible, False otherwise
        """
        if name:
            result = await self.test_datasource(name)
            return result["success"]
        
        # Backward compatibility: check default datasource
        if self.base_url:
            try:
                client = httpx.AsyncClient(timeout=httpx.Timeout(5.0))
                response = await client.get(f"{self.base_url}/health")
                await client.aclose()
                return response.status_code == 200
            except Exception as e:
                logger.warning(f"[DataSource] Health check failed: {str(e)}")
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
