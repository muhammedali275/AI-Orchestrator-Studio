"""
Web Search Tool - Search the web for information.

Uses configuration from tool config - no hard-coded API keys.
"""

import logging
from typing import Dict, Any, Optional, List
import httpx
from .base import BaseTool, ToolResult, ToolStatus

logger = logging.getLogger(__name__)


class WebSearchTool(BaseTool):
    """
    Web search tool for retrieving information from the internet.
    
    Supports various search providers via configuration.
    """
    
    def __init__(self, name: str = "web_search", config: Optional[Dict[str, Any]] = None):
        """
        Initialize web search tool.
        
        Args:
            name: Tool name
            config: Configuration including api_key, endpoint, provider
        """
        super().__init__(
            name=name,
            description="Search the web for information",
            config=config
        )
        
        self.api_key = self.config.get("api_key")
        self.endpoint = self.config.get("endpoint")
        self.provider = self.config.get("provider", "generic")
        self.timeout = self.config.get("timeout", 30)
        self.max_results = self.config.get("max_results", 10)
    
    async def execute(
        self,
        query: str,
        max_results: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """
        Execute web search.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            filters: Additional search filters (date, domain, etc.)
            
        Returns:
            ToolResult with search results
        """
        if not self.endpoint:
            return ToolResult(
                status=ToolStatus.ERROR,
                output=None,
                error="Search endpoint not configured"
            )
        
        if not self.api_key:
            return ToolResult(
                status=ToolStatus.ERROR,
                output=None,
                error="Search API key not configured"
            )
        
        max_results = max_results or self.max_results
        
        try:
            logger.info(f"[WebSearch] Searching for: {query}")
            
            # Build request based on provider
            headers = {"Authorization": f"Bearer {self.api_key}"}
            params = {
                "q": query,
                "limit": max_results
            }
            
            if filters:
                params.update(filters)
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    self.endpoint,
                    params=params,
                    headers=headers
                )
                response.raise_for_status()
                data = response.json()
            
            # Parse results based on provider
            results = self._parse_results(data)
            
            logger.info(f"[WebSearch] Found {len(results)} results")
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                output=results,
                metadata={
                    "query": query,
                    "result_count": len(results),
                    "provider": self.provider
                }
            )
            
        except httpx.TimeoutException:
            logger.error(f"[WebSearch] Timeout for query: {query}")
            return ToolResult(
                status=ToolStatus.TIMEOUT,
                output=None,
                error="Search request timeout"
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"[WebSearch] HTTP error: {e.response.status_code}")
            return ToolResult(
                status=ToolStatus.FAILURE,
                output=None,
                error=f"Search API error: {e.response.status_code}"
            )
            
        except Exception as e:
            logger.error(f"[WebSearch] Error: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                output=None,
                error=str(e)
            )
    
    def _parse_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse search results based on provider format.
        
        Args:
            data: Raw API response
            
        Returns:
            Normalized list of results
        """
        # Generic parser - override for specific providers
        results = []
        
        # Try common result formats
        items = data.get("results") or data.get("items") or data.get("data") or []
        
        for item in items:
            result = {
                "title": item.get("title") or item.get("name") or "",
                "url": item.get("url") or item.get("link") or "",
                "snippet": item.get("snippet") or item.get("description") or "",
                "source": item.get("source") or item.get("domain") or ""
            }
            results.append(result)
        
        return results
    
    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema for LLM function calling."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": self.max_results
                    },
                    "filters": {
                        "type": "object",
                        "description": "Additional search filters"
                    }
                },
                "required": ["query"]
            }
        }
