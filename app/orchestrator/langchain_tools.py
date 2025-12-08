"""
LangChain tools for AIpanel.

Implements various tools using LangChain community packages.
"""

import json
import logging
import re
from typing import Dict, Any, Optional, List, Type, Union

import httpx
from langchain.tools import BaseTool
from langchain.pydantic_v1 import BaseModel, Field
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db.models import DataSource, Credential
from ..db.session import get_db

logger = logging.getLogger(__name__)
settings = get_settings()


class HttpToolInput(BaseModel):
    """Input for HTTP tool."""
    url: str = Field(..., description="URL to make request to")
    method: str = Field(default="GET", description="HTTP method (GET, POST, PUT, DELETE)")
    headers: Optional[Dict[str, str]] = Field(default=None, description="HTTP headers")
    params: Optional[Dict[str, Any]] = Field(default=None, description="Query parameters")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Request body for POST/PUT")


class HttpTool(BaseTool):
    """
    HTTP tool for making API requests.
    
    Uses credentials from database.
    """
    name = "http_tool"
    description = "Make HTTP requests to external APIs"
    args_schema: Type[BaseModel] = HttpToolInput
    
    def __init__(
        self,
        credential_id: Optional[str] = None,
        credential_name: Optional[str] = None,
        base_url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        db: Optional[Session] = None
    ):
        """
        Initialize HTTP tool.
        
        Args:
            credential_id: Credential ID
            credential_name: Credential name (alternative to credential_id)
            base_url: Base URL for requests
            headers: Default headers
            db: Database session
        """
        super().__init__()
        self.credential_id = credential_id
        self.credential_name = credential_name
        self.base_url = base_url
        self.default_headers = headers or {}
        self.db = db
        self._credential = None
    
    async def _arun(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Run HTTP tool asynchronously.
        
        Args:
            url: URL to make request to
            method: HTTP method
            headers: HTTP headers
            params: Query parameters
            data: Request body for POST/PUT
            
        Returns:
            Response as string
        """
        # Load credential if needed
        if (self.credential_id or self.credential_name) and not self._credential:
            await self._load_credential()
        
        # Build full URL
        if self.base_url and not url.startswith(("http://", "https://")):
            full_url = f"{self.base_url.rstrip('/')}/{url.lstrip('/')}"
        else:
            full_url = url
        
        # Build headers
        request_headers = {**self.default_headers}
        if self._credential and "data" in self._credential:
            # Add authentication based on credential type
            cred_data = self._credential["data"]
            if self._credential["type"] == "api_key":
                if "header_name" in cred_data and "key" in cred_data:
                    request_headers[cred_data["header_name"]] = cred_data["key"]
            elif self._credential["type"] == "bearer_token":
                if "token" in cred_data:
                    request_headers["Authorization"] = f"Bearer {cred_data['token']}"
            elif self._credential["type"] == "basic_auth":
                if "username" in cred_data and "password" in cred_data:
                    import base64
                    auth_str = f"{cred_data['username']}:{cred_data['password']}"
                    encoded = base64.b64encode(auth_str.encode()).decode()
                    request_headers["Authorization"] = f"Basic {encoded}"
        
        # Add user-provided headers
        if headers:
            request_headers.update(headers)
        
        # Make request
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method.upper() == "GET":
                response = await client.get(full_url, headers=request_headers, params=params)
            elif method.upper() == "POST":
                response = await client.post(full_url, headers=request_headers, params=params, json=data)
            elif method.upper() == "PUT":
                response = await client.put(full_url, headers=request_headers, params=params, json=data)
            elif method.upper() == "DELETE":
                response = await client.delete(full_url, headers=request_headers, params=params)
            else:
                return f"Unsupported HTTP method: {method}"
            
            # Handle response
            response.raise_for_status()
            
            # Try to parse as JSON
            try:
                result = response.json()
                return json.dumps(result, indent=2)
            except:
                return response.text
    
    async def _load_credential(self) -> None:
        """
        Load credential from database.
        
        Raises:
            ValueError: If credential not found
        """
        if not self.db:
            # Create a new session if not provided
            async for db_session in get_db():
                self.db = db_session
                break
        
        query = self.db.query(Credential)
        if self.credential_id:
            credential = query.filter(Credential.id == self.credential_id).first()
        elif self.credential_name:
            credential = query.filter(Credential.name == self.credential_name).first()
        else:
            return
        
        if not credential:
            logger.warning(f"Credential not found: {self.credential_id or self.credential_name}")
            return
        
        self._credential = credential.to_dict(include_data=True)
    
    def _run(self, *args, **kwargs) -> str:
        """
        Run HTTP tool synchronously.
        
        This is a placeholder that raises NotImplementedError.
        The tool is designed to be used asynchronously.
        """
        raise NotImplementedError("HttpTool is async only, use _arun")


class CubeJsToolInput(BaseModel):
    """Input for Cube.js tool."""
    query: Dict[str, Any] = Field(..., description="Cube.js query object")
    datasource_name: Optional[str] = Field(default=None, description="Data source name")


class CubeJsTool(BaseTool):
    """
    Cube.js tool for analytics queries.
    
    Uses datasource configuration from database.
    """
    name = "cubejs_tool"
    description = "Query Cube.js for analytics data"
    args_schema: Type[BaseModel] = CubeJsToolInput
    
    def __init__(
        self,
        datasource_id: Optional[str] = None,
        datasource_name: Optional[str] = None,
        db: Optional[Session] = None
    ):
        """
        Initialize Cube.js tool.
        
        Args:
            datasource_id: Data source ID
            datasource_name: Data source name (alternative to datasource_id)
            db: Database session
        """
        super().__init__()
        self.datasource_id = datasource_id
        self.datasource_name = datasource_name
        self.db = db
        self._datasource = None
        self._credential = None
    
    async def _arun(
        self,
        query: Dict[str, Any],
        datasource_name: Optional[str] = None
    ) -> str:
        """
        Run Cube.js tool asynchronously.
        
        Args:
            query: Cube.js query object
            datasource_name: Data source name (overrides constructor)
            
        Returns:
            Query results as string
        """
        # Override datasource name if provided
        if datasource_name:
            self.datasource_name = datasource_name
        
        # Load datasource if needed
        if (self.datasource_id or self.datasource_name) and not self._datasource:
            await self._load_datasource()
        
        if not self._datasource:
            return "Error: No Cube.js datasource configured"
        
        # Get base URL and auth from datasource
        base_url = self._datasource.get("url")
        if not base_url:
            return "Error: Cube.js datasource URL not configured"
        
        # Build headers
        headers = {"Content-Type": "application/json"}
        
        # Add authentication if credential is available
        if self._credential and "data" in self._credential:
            cred_data = self._credential["data"]
            if "api_key" in cred_data:
                headers["Authorization"] = cred_data["api_key"]
        
        # Make request to Cube.js
        async with httpx.AsyncClient(timeout=60.0) as client:
            endpoint = f"{base_url.rstrip('/')}/cubejs-api/v1/load"
            response = await client.post(endpoint, headers=headers, json={"query": query})
            
            # Handle response
            response.raise_for_status()
            result = response.json()
            
            return json.dumps(result, indent=2)
    
    async def _load_datasource(self) -> None:
        """
        Load datasource from database.
        
        Raises:
            ValueError: If datasource not found
        """
        if not self.db:
            # Create a new session if not provided
            async for db_session in get_db():
                self.db = db_session
                break
        
        query = self.db.query(DataSource)
        if self.datasource_id:
            datasource = query.filter(DataSource.id == self.datasource_id).first()
        elif self.datasource_name:
            datasource = query.filter(DataSource.name == self.datasource_name).first()
        else:
            return
        
        if not datasource:
            logger.warning(f"Datasource not found: {self.datasource_id or self.datasource_name}")
            return
        
        self._datasource = datasource.to_dict()
        
        # Load credential if available
        if datasource.credential_id:
            credential = self.db.query(Credential).filter(
                Credential.id == datasource.credential_id
            ).first()
            
            if credential:
                self._credential = credential.to_dict(include_data=True)
    
    def _run(self, *args, **kwargs) -> str:
        """
        Run Cube.js tool synchronously.
        
        This is a placeholder that raises NotImplementedError.
        The tool is designed to be used asynchronously.
        """
        raise NotImplementedError("CubeJsTool is async only, use _arun")


class ChurnQueryToolInput(BaseModel):
    """Input for churn query tool."""
    limit: Optional[int] = Field(default=50, description="Number of results to return")
    order: Optional[str] = Field(default="desc", description="Sort order (asc or desc)")


class ChurnQueryTool(BaseTool):
    """
    Specialized tool for churn analytics queries.
    
    Implements the exact Cube.js query template for "Top churn contracts".
    """
    name = "churn_query_tool"
    description = "Query for top contracts by churn rate"
    args_schema: Type[BaseModel] = ChurnQueryToolInput
    
    def __init__(
        self,
        cubejs_tool: Optional[CubeJsTool] = None,
        datasource_name: Optional[str] = None,
        db: Optional[Session] = None
    ):
        """
        Initialize churn query tool.
        
        Args:
            cubejs_tool: Existing CubeJsTool instance
            datasource_name: Data source name
            db: Database session
        """
        super().__init__()
        self.cubejs_tool = cubejs_tool
        self.datasource_name = datasource_name
        self.db = db
    
    async def _arun(
        self,
        limit: int = 50,
        order: str = "desc"
    ) -> str:
        """
        Run churn query tool asynchronously.
        
        Args:
            limit: Number of results to return
            order: Sort order (asc or desc)
            
        Returns:
            Query results as string
        """
        # Create CubeJsTool if not provided
        if not self.cubejs_tool:
            self.cubejs_tool = CubeJsTool(
                datasource_name=self.datasource_name,
                db=self.db
            )
        
        # Validate order
        if order.lower() not in ["asc", "desc"]:
            order = "desc"
        
        # Build the exact query for "Top churn contracts"
        query = {
            "dimensions": ["fct_contract_trends.contract_number"],
            "measures": ["fct_contract_trends.churns"],
            "order": [["fct_contract_trends.churns", order.lower()]],
            "limit": limit
        }
        
        # Execute query
        return await self.cubejs_tool._arun(query=query)
    
    def _run(self, *args, **kwargs) -> str:
        """
        Run churn query tool synchronously.
        
        This is a placeholder that raises NotImplementedError.
        The tool is designed to be used asynchronously.
        """
        raise NotImplementedError("ChurnQueryTool is async only, use _arun")


def is_churn_query(query: str) -> bool:
    """
    Check if a query is asking for churn data.
    
    Args:
        query: User query
        
    Returns:
        True if query is about churn, False otherwise
    """
    churn_patterns = [
        r"top\s+churn(ed)?\s+contracts",
        r"top\s+contracts\s+by\s+churn",
        r"highest\s+churn\s+contracts",
        r"top\s+\d+\s+contracts\s+by\s+churn",
        r"contracts\s+with\s+highest\s+churn"
    ]
    
    for pattern in churn_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            return True
    
    return False


async def get_tools_for_query(
    query: str,
    db: Optional[Session] = None
) -> List[BaseTool]:
    """
    Get appropriate tools for a query.
    
    Args:
        query: User query
        db: Database session
        
    Returns:
        List of tools
    """
    tools = []
    
    # Check for churn query
    if is_churn_query(query):
        tools.append(ChurnQueryTool(datasource_name="cubejs_main", db=db))
    else:
        # Add generic tools
        tools.append(HttpTool(db=db))
        tools.append(CubeJsTool(datasource_name="cubejs_main", db=db))
    
    return tools
