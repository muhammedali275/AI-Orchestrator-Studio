"""
DataSources API - Endpoints for data source configuration and testing.

Provides CRUD operations for datasource settings and connectivity testing.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from ..config import get_settings, Settings, DataSourceConfig, clear_settings_cache
from ..clients.datasource_client import DataSourceClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/datasources", tags=["datasources"])


class DataSourceConfigModel(BaseModel):
    """DataSource configuration model."""
    name: str = Field(..., description="DataSource name/identifier")
    type: str = Field(..., description="DataSource type (postgres, cubejs, api, etc.)")
    url: str = Field(..., description="DataSource URL/endpoint")
    auth_token: Optional[str] = Field(None, description="Authentication token")
    timeout_seconds: int = Field(default=30, description="Request timeout")
    enabled: bool = Field(default=True, description="Whether datasource is enabled")
    config: Dict[str, Any] = Field(default_factory=dict, description="Additional configuration")


class QueryRequest(BaseModel):
    """Query request model."""
    query: str = Field(..., description="Query string (SQL, GraphQL, etc.)")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Query parameters")


@router.get("", response_model=List[DataSourceConfigModel])
async def list_datasources(settings: Settings = Depends(get_settings)) -> List[DataSourceConfigModel]:
    """
    List all configured datasources.
    
    Returns:
        List of datasource configurations
    """
    datasources = []
    for name, config in settings.datasources.items():
        datasources.append(DataSourceConfigModel(
            name=config.name,
            type=config.type,
            url=config.url,
            auth_token=config.auth_token,
            timeout_seconds=config.timeout_seconds,
            enabled=config.enabled,
            config=config.config
        ))
    
    return datasources


@router.get("/{name}", response_model=DataSourceConfigModel)
async def get_datasource(
    name: str,
    settings: Settings = Depends(get_settings)
) -> DataSourceConfigModel:
    """
    Get a specific datasource configuration.
    
    Args:
        name: DataSource name
        
    Returns:
        DataSource configuration
    """
    ds_config = settings.get_datasource(name)
    
    if not ds_config:
        raise HTTPException(
            status_code=404,
            detail=f"DataSource '{name}' not found"
        )
    
    return DataSourceConfigModel(
        name=ds_config.name,
        type=ds_config.type,
        url=ds_config.url,
        auth_token=ds_config.auth_token,
        timeout_seconds=ds_config.timeout_seconds,
        enabled=ds_config.enabled,
        config=ds_config.config
    )


@router.post("", status_code=201)
async def create_datasource(
    datasource: DataSourceConfigModel,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Register a new datasource.
    
    Args:
        datasource: DataSource configuration
        
    Returns:
        Success message and created datasource
    """
    # Check if datasource already exists
    if settings.get_datasource(datasource.name):
        raise HTTPException(
            status_code=409,
            detail=f"DataSource '{datasource.name}' already exists"
        )
    
    try:
        # Create datasource config
        ds_config = DataSourceConfig(
            name=datasource.name,
            type=datasource.type,
            url=datasource.url,
            auth_token=datasource.auth_token,
            timeout_seconds=datasource.timeout_seconds,
            enabled=datasource.enabled,
            config=datasource.config
        )
        
        # Add to settings
        settings.add_datasource(ds_config)
        
        # Clear cache to reload settings
        clear_settings_cache()
        
        logger.info(f"[DataSources API] Created datasource: {datasource.name}")
        
        return {
            "success": True,
            "message": f"DataSource '{datasource.name}' created successfully",
            "datasource": datasource.dict()
        }
        
    except Exception as e:
        logger.error(f"[DataSources API] Error creating datasource: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create datasource: {str(e)}"
        )


@router.put("/{name}")
async def update_datasource(
    name: str,
    datasource: DataSourceConfigModel,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Update an existing datasource configuration.
    
    Args:
        name: DataSource name
        datasource: Updated datasource configuration
        
    Returns:
        Success message and updated datasource
    """
    # Check if datasource exists
    if not settings.get_datasource(name):
        raise HTTPException(
            status_code=404,
            detail=f"DataSource '{name}' not found"
        )
    
    try:
        # Create updated datasource config
        ds_config = DataSourceConfig(
            name=datasource.name,
            type=datasource.type,
            url=datasource.url,
            auth_token=datasource.auth_token,
            timeout_seconds=datasource.timeout_seconds,
            enabled=datasource.enabled,
            config=datasource.config
        )
        
        # Update in settings
        settings.add_datasource(ds_config)
        
        # Clear cache to reload settings
        clear_settings_cache()
        
        logger.info(f"[DataSources API] Updated datasource: {name}")
        
        return {
            "success": True,
            "message": f"DataSource '{name}' updated successfully",
            "datasource": datasource.dict()
        }
        
    except Exception as e:
        logger.error(f"[DataSources API] Error updating datasource: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update datasource: {str(e)}"
        )


@router.delete("/{name}")
async def delete_datasource(
    name: str,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Remove a datasource configuration.
    
    Args:
        name: DataSource name
        
    Returns:
        Success message
    """
    if not settings.remove_datasource(name):
        raise HTTPException(
            status_code=404,
            detail=f"DataSource '{name}' not found"
        )
    
    # Clear cache to reload settings
    clear_settings_cache()
    
    logger.info(f"[DataSources API] Deleted datasource: {name}")
    
    return {
        "success": True,
        "message": f"DataSource '{name}' deleted successfully"
    }


@router.post("/{name}/test")
async def test_datasource(
    name: str,
    skip_connectivity: bool = False,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Test connectivity to a specific datasource.
    
    Args:
        name: DataSource name
        skip_connectivity: If True, only validate configuration without testing connectivity
        
    Returns:
        Test result with detailed status
    """
    ds_config = settings.get_datasource(name)
    
    if not ds_config:
        raise HTTPException(
            status_code=404,
            detail=f"DataSource '{name}' not found"
        )
    
    # Configuration validation result
    result = {
        "datasource": name,
        "type": ds_config.type,
        "config_valid": True,
        "config_saved": True,
        "enabled": ds_config.enabled,
        "url": ds_config.url
    }
    
    if not ds_config.enabled:
        result.update({
            "success": False,
            "connectivity_tested": False,
            "connectivity_status": "skipped",
            "message": "DataSource is disabled. Enable it to test connectivity.",
            "warning": "DataSource configuration is saved but datasource is disabled"
        })
        return result
    
    # If skip_connectivity is True, return success after config validation
    if skip_connectivity:
        result.update({
            "success": True,
            "connectivity_tested": False,
            "connectivity_status": "skipped",
            "message": "DataSource configuration is valid. Connectivity test skipped."
        })
        return result
    
    try:
        client = DataSourceClient(settings)
        test_result = await client.test_datasource(name)
        await client.close()
        
        logger.info(f"[DataSources API] Test result for {name}: {test_result.get('success', False)}")
        
        # Enhance the result with additional context
        result.update({
            "success": test_result.get("success", False),
            "connectivity_tested": True,
            "connectivity_status": "reachable" if test_result.get("success") else "unreachable",
            "message": test_result.get("message", ""),
            "details": test_result
        })
        
        if not result["success"]:
            result["suggestion"] = "Ensure the datasource service is running and accessible, or use 'skip_connectivity=true' to save without testing."
        
        return result
        
    except Exception as e:
        logger.error(f"[DataSources API] Test failed for {name}: {str(e)}")
        result.update({
            "success": False,
            "connectivity_tested": True,
            "connectivity_status": "error",
            "error": type(e).__name__,
            "error_detail": str(e),
            "message": f"Failed to test datasource: {str(e)}",
            "suggestion": "Verify the datasource URL and network connectivity, or use 'skip_connectivity=true' to save without testing."
        })
        return result


@router.post("/{name}/query")
async def query_datasource(
    name: str,
    request: QueryRequest,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Execute a query against a specific datasource.
    
    Args:
        name: DataSource name
        request: Query request with query string and parameters
        
    Returns:
        Query results
    """
    try:
        client = DataSourceClient(settings)
        result = await client.query_datasource(name, request.query, request.parameters)
        await client.close()
        
        return result
        
    except Exception as e:
        logger.error(f"[DataSources API] Query failed for {name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute query: {str(e)}"
        )


@router.get("/{name}/schema")
async def get_datasource_schema(
    name: str,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Get schema information for a datasource.
    
    Args:
        name: DataSource name
        
    Returns:
        Schema metadata
    """
    try:
        client = DataSourceClient(settings)
        result = await client.get_schema(name)
        await client.close()
        
        return result
        
    except Exception as e:
        logger.error(f"[DataSources API] Schema fetch failed for {name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch schema: {str(e)}"
        )


@router.get("/{name}/tables")
async def get_datasource_tables(
    name: str,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Get list of tables/collections for a datasource.
    
    Args:
        name: DataSource name
        
    Returns:
        List of table names
    """
    try:
        client = DataSourceClient(settings)
        tables = await client.get_tables(name)
        await client.close()
        
        return {
            "success": True,
            "datasource": name,
            "tables": tables,
            "count": len(tables)
        }
        
    except Exception as e:
        logger.error(f"[DataSources API] Tables fetch failed for {name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch tables: {str(e)}"
        )


@router.get("/health/all")
async def check_all_datasources_health(settings: Settings = Depends(get_settings)) -> Dict[str, Any]:
    """
    Check health of all configured datasources.
    
    Returns:
        Health status for all datasources
    """
    client = DataSourceClient(settings)
    results = {}
    
    for name in settings.datasources.keys():
        try:
            result = await client.test_datasource(name)
            results[name] = {
                "healthy": result["success"],
                "type": result.get("type", ""),
                "message": result.get("message", ""),
                "url": result.get("url", "")
            }
        except Exception as e:
            results[name] = {
                "healthy": False,
                "error": str(e)
            }
    
    await client.close()
    
    return {
        "datasources": results,
        "total": len(results),
        "healthy": sum(1 for r in results.values() if r.get("healthy", False))
    }
