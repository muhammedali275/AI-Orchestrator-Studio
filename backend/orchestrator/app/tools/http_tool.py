"""
HTTP Tool - Generic HTTP request tool.

Uses configuration from tool config - no hard-coded endpoints.
"""

import logging
from typing import Dict, Any, Optional
import httpx
from .base import BaseTool, ToolResult, ToolStatus

logger = logging.getLogger(__name__)


class HttpTool(BaseTool):
    """
    Generic HTTP tool for making API requests.
    
    Supports GET, POST, PUT, DELETE methods with authentication.
    """
    
    def __init__(self, name: str = "http_request", config: Optional[Dict[str, Any]] = None):
        """
        Initialize HTTP tool.
        
        Args:
            name: Tool name
            config: Configuration including base_url, auth_token, timeout
        """
        super().__init__(
            name=name,
            description="Make HTTP requests to external APIs",
            config=config
        )
        
        self.base_url = self.config.get("base_url")
        self.auth_token = self.config.get("auth_token")
        self.timeout = self.config.get("timeout", 30)
        self.headers = self.config.get("headers", {})
    
    async def execute(
        self,
        url: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> ToolResult:
        """
        Execute HTTP request.
        
        Args:
            url: Request URL (can be relative if base_url configured)
            method: HTTP method (GET, POST, PUT, DELETE)
            params: Query parameters
            data: Request body data
            headers: Additional headers
            
        Returns:
            ToolResult with response data
        """
        try:
            # Build full URL
            if self.base_url and not url.startswith("http"):
                full_url = f"{self.base_url.rstrip('/')}/{url.lstrip('/')}"
            else:
                full_url = url
            
            # Build headers
            request_headers = {**self.headers}
            if self.auth_token:
                request_headers["Authorization"] = f"Bearer {self.auth_token}"
            if headers:
                request_headers.update(headers)
            
            logger.info(f"[HttpTool] {method} {full_url}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if method.upper() == "GET":
                    response = await client.get(full_url, params=params, headers=request_headers)
                elif method.upper() == "POST":
                    response = await client.post(full_url, json=data, headers=request_headers)
                elif method.upper() == "PUT":
                    response = await client.put(full_url, json=data, headers=request_headers)
                elif method.upper() == "DELETE":
                    response = await client.delete(full_url, headers=request_headers)
                else:
                    return ToolResult(
                        status=ToolStatus.ERROR,
                        output=None,
                        error=f"Unsupported HTTP method: {method}"
                    )
                
                response.raise_for_status()
                
                # Try to parse JSON, fallback to text
                try:
                    result_data = response.json()
                except Exception:
                    result_data = response.text
                
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    output=result_data,
                    metadata={
                        "status_code": response.status_code,
                        "url": full_url,
                        "method": method
                    }
                )
                
        except httpx.TimeoutException:
            logger.error(f"[HttpTool] Timeout for {method} {url}")
            return ToolResult(
                status=ToolStatus.TIMEOUT,
                output=None,
                error="Request timeout"
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"[HttpTool] HTTP error: {e.response.status_code}")
            return ToolResult(
                status=ToolStatus.FAILURE,
                output=None,
                error=f"HTTP {e.response.status_code}: {str(e)}"
            )
            
        except Exception as e:
            logger.error(f"[HttpTool] Error: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                output=None,
                error=str(e)
            )
    
    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema for LLM function calling."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Request URL (relative or absolute)"
                    },
                    "method": {
                        "type": "string",
                        "enum": ["GET", "POST", "PUT", "DELETE"],
                        "description": "HTTP method",
                        "default": "GET"
                    },
                    "params": {
                        "type": "object",
                        "description": "Query parameters"
                    },
                    "data": {
                        "type": "object",
                        "description": "Request body data"
                    },
                    "headers": {
                        "type": "object",
                        "description": "Additional headers"
                    }
                },
                "required": ["url"]
            }
        }
