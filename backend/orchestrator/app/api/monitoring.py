"""
Monitoring API - Endpoints for system health and metrics.

Provides health checks, metrics, and system status information.
"""

import logging
import psutil
import time
from datetime import datetime
from fastapi import APIRouter, Depends
from typing import Dict, Any

from ..config import get_settings, Settings
from ..clients.llm_client import LLMClient
from ..clients.external_agent_client import ExternalAgentClient
from ..clients.datasource_client import DataSourceClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])

# Track startup time
_startup_time = time.time()


@router.get("/health")
async def health_check(settings: Settings = Depends(get_settings)) -> Dict[str, Any]:
    """
    Comprehensive system health check.
    
    Returns:
        Health status for all components
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": time.time() - _startup_time,
        "components": {}
    }
    
    # Check LLM
    health_status["components"]["llm"] = {
        "configured": settings.llm_base_url is not None,
        "base_url": settings.llm_base_url,
        "model": settings.llm_default_model
    }
    
    # Check Redis
    redis_url = settings.get_redis_url()
    health_status["components"]["redis"] = {
        "configured": redis_url is not None,
        "url": redis_url if redis_url else None
    }
    
    # Check Postgres
    postgres_dsn = settings.get_postgres_dsn()
    health_status["components"]["postgres"] = {
        "configured": postgres_dsn is not None
    }
    
    # Check agents
    health_status["components"]["agents"] = {
        "count": len(settings.external_agents),
        "configured": len(settings.external_agents) > 0
    }
    
    # Check datasources
    health_status["components"]["datasources"] = {
        "count": len(settings.datasources),
        "configured": len(settings.datasources) > 0
    }
    
    # Check tools
    health_status["components"]["tools"] = {
        "count": len(settings.tools),
        "configured": len(settings.tools) > 0
    }
    
    # Overall status
    critical_components = ["llm"]
    all_critical_ok = all(
        health_status["components"].get(comp, {}).get("configured", False)
        for comp in critical_components
    )
    
    health_status["status"] = "healthy" if all_critical_ok else "degraded"
    
    return health_status


@router.get("/metrics")
async def get_metrics(settings: Settings = Depends(get_settings)) -> Dict[str, Any]:
    """
    Get system metrics.
    
    Returns:
        System performance metrics
    """
    try:
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Memory metrics
        memory = psutil.virtual_memory()
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": time.time() - _startup_time,
            "system": {
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count
                },
                "memory": {
                    "total_mb": memory.total / (1024 * 1024),
                    "available_mb": memory.available / (1024 * 1024),
                    "used_mb": memory.used / (1024 * 1024),
                    "percent": memory.percent
                },
                "disk": {
                    "total_gb": disk.total / (1024 * 1024 * 1024),
                    "used_gb": disk.used / (1024 * 1024 * 1024),
                    "free_gb": disk.free / (1024 * 1024 * 1024),
                    "percent": disk.percent
                }
            },
            "configuration": {
                "llm_configured": settings.llm_base_url is not None,
                "redis_configured": settings.get_redis_url() is not None,
                "postgres_configured": settings.get_postgres_dsn() is not None,
                "agents_count": len(settings.external_agents),
                "datasources_count": len(settings.datasources),
                "tools_count": len(settings.tools)
            }
        }
        
    except Exception as e:
        logger.error(f"[Monitoring] Error getting metrics: {str(e)}")
        return {
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/status")
async def get_status(settings: Settings = Depends(get_settings)) -> Dict[str, Any]:
    """
    Get detailed system status.
    
    Returns:
        Detailed status information
    """
    return {
        "application": {
            "name": settings.app_name,
            "version": settings.app_version,
            "debug": settings.debug,
            "uptime_seconds": time.time() - _startup_time
        },
        "configuration": {
            "llm": {
                "configured": settings.llm_base_url is not None,
                "base_url": settings.llm_base_url,
                "model": settings.llm_default_model,
                "timeout": settings.llm_timeout_seconds
            },
            "memory": {
                "enabled": settings.memory_enabled,
                "max_messages": settings.memory_max_messages,
                "summary_enabled": settings.memory_summary_enabled
            },
            "cache": {
                "enabled": settings.cache_enabled,
                "ttl_seconds": settings.cache_ttl_seconds
            },
            "orchestration": {
                "max_iterations": settings.orchestration_max_iterations,
                "timeout_seconds": settings.orchestration_timeout_seconds
            }
        },
        "resources": {
            "agents": len(settings.external_agents),
            "datasources": len(settings.datasources),
            "tools": len(settings.tools)
        }
    }


@router.get("/connectivity")
async def check_connectivity(settings: Settings = Depends(get_settings)) -> Dict[str, Any]:
    """
    Check connectivity to all configured services.
    
    Returns:
        Connectivity status for all services
    """
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    # Check LLM
    if settings.llm_base_url:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{settings.llm_base_url}/health")
                results["services"]["llm"] = {
                    "reachable": response.status_code == 200,
                    "status_code": response.status_code,
                    "url": settings.llm_base_url
                }
        except Exception as e:
            results["services"]["llm"] = {
                "reachable": False,
                "error": str(e),
                "url": settings.llm_base_url
            }
    else:
        results["services"]["llm"] = {
            "reachable": False,
            "error": "Not configured"
        }
    
    # Check agents
    if settings.external_agents:
        agent_client = ExternalAgentClient(settings)
        agent_results = {}
        for name in settings.external_agents.keys():
            try:
                test_result = await agent_client.test_agent(name)
                agent_results[name] = {
                    "reachable": test_result["success"],
                    "url": test_result.get("url", "")
                }
            except Exception as e:
                agent_results[name] = {
                    "reachable": False,
                    "error": str(e)
                }
        await agent_client.close()
        results["services"]["agents"] = agent_results
    
    # Check datasources
    if settings.datasources:
        ds_client = DataSourceClient(settings)
        ds_results = {}
        for name in settings.datasources.keys():
            try:
                test_result = await ds_client.test_datasource(name)
                ds_results[name] = {
                    "reachable": test_result["success"],
                    "type": test_result.get("type", ""),
                    "url": test_result.get("url", "")
                }
            except Exception as e:
                ds_results[name] = {
                    "reachable": False,
                    "error": str(e)
                }
        await ds_client.close()
        results["services"]["datasources"] = ds_results
    
    # Summary
    total_services = 1  # LLM
    total_services += len(settings.external_agents)
    total_services += len(settings.datasources)
    
    reachable_count = 0
    if results["services"].get("llm", {}).get("reachable"):
        reachable_count += 1
    if "agents" in results["services"]:
        reachable_count += sum(1 for a in results["services"]["agents"].values() if a.get("reachable"))
    if "datasources" in results["services"]:
        reachable_count += sum(1 for d in results["services"]["datasources"].values() if d.get("reachable"))
    
    results["summary"] = {
        "total_services": total_services,
        "reachable": reachable_count,
        "unreachable": total_services - reachable_count
    }
    
    return results


@router.get("/logs")
async def get_recent_logs(limit: int = 100) -> Dict[str, Any]:
    """
    Get recent log entries.
    
    Args:
        limit: Maximum number of log entries to return
        
    Returns:
        Recent log entries
    """
    # This is a placeholder - in production, you'd read from actual log files
    return {
        "message": "Log retrieval not implemented",
        "note": "In production, this would return recent log entries from log files or logging service"
    }
