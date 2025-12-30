"""
Configuration Management API.

Provides endpoints for persisting GUI configuration changes to files.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

from ..config import get_settings, Settings, clear_settings_cache
from ..services.config_writer import ConfigWriter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/config", tags=["configuration"])

# Initialize config writer
config_writer = ConfigWriter()


class EnvConfigUpdate(BaseModel):
    """Model for environment variable updates."""
    variables: Dict[str, str] = Field(..., description="Environment variables to update")


class AgentConfig(BaseModel):
    """Model for agent configuration."""
    name: str
    url: str
    auth_token: Optional[str] = None
    timeout_seconds: int = 30
    enabled: bool = True
    metadata: Dict[str, Any] = {}


class ToolConfig(BaseModel):
    """Model for tool configuration."""
    name: str
    type: str
    config: Dict[str, Any] = {}
    enabled: bool = True
    description: Optional[str] = None


class DataSourceConfig(BaseModel):
    """Model for datasource configuration."""
    name: str
    type: str
    url: str
    auth_token: Optional[str] = None
    timeout_seconds: int = 30
    enabled: bool = True
    config: Dict[str, Any] = {}


class LLMConnection(BaseModel):
    """Model for LLM connection persisted by GUI."""
    id: str
    name: str
    base_url: str
    model: Optional[str] = None
    api_key: Optional[str] = None
    timeout: int = 60
    max_tokens: Optional[int] = None
    temperature: float = 0.7
    is_local: bool = False


@router.post("/llm-connections/{conn_id}/test")
async def test_llm_connection(conn_id: str, settings: Settings = Depends(get_settings)) -> Dict[str, Any]:
    """Test reachability of a specific LLM connection by ID.

    Tries provider-specific probes:
    - Ollama: GET /api/tags
    - OpenAI-compatible: GET /v1/models then fallback to /models

    Returns connectivity, latency, status code and a short message.
    """
    try:
        # Resolve connection info by merging file + in-memory settings
        target: Optional[LLMConnection] = None
        try:
            # First, check settings.llm_connections
            if conn_id in settings.llm_connections:
                cfg = settings.llm_connections[conn_id]
                target = LLMConnection(**cfg.dict())
        except Exception:
            pass

        if target is None:
            # Try to read from config file
            from pathlib import Path
            import json as _json
            path = Path("config/llm_connections.json")
            if path.exists():
                try:
                    with open(path, 'r') as f:
                        data = _json.load(f) or {}
                        for c in data.get("connections", []):
                            if c.get("id") == conn_id:
                                try:
                                    target = LLMConnection(**c)
                                    break
                                except Exception:
                                    pass
                except Exception:
                    pass

        if target is None and conn_id == "default":
            # Bridge to single-config .env defaults
            target = LLMConnection(
                id="default",
                name="Default LLM",
                base_url=settings.llm_base_url or "",
                model=settings.llm_default_model or "",
                api_key=settings.llm_api_key or None,
                timeout=settings.llm_timeout_seconds or 60,
                max_tokens=settings.llm_max_tokens,
                temperature=settings.llm_temperature,
                is_local=(settings.llm_base_url or "").find("localhost") != -1 or (settings.llm_base_url or "").find("127.0.0.1") != -1 or (settings.llm_base_url or "").find("11434") != -1,
            )

        if target is None or not target.base_url:
            raise HTTPException(status_code=404, detail=f"LLM connection '{conn_id}' not found or base_url missing")

        base_url = target.base_url.rstrip('/')
        headers = {"Content-Type": "application/json"}
        if target.api_key:
            headers["Authorization"] = f"Bearer {target.api_key}"

        def detect_provider(url: str) -> str:
            u = (url or "").lower()
            if "ollama" in u or "11434" in u:
                return "ollama"
            if "openai" in u or "/v1" in u:
                return "openai"
            return "unknown"

        provider = detect_provider(base_url)

        import time as _time
        import httpx as _httpx
        start = _time.time()
        status_code = None
        models_sample: List[str] = []
        msg = ""

        async with _httpx.AsyncClient(timeout=target.timeout or 10, headers=headers) as client:
            # Try provider-specific endpoints
            try:
                if provider == "ollama":
                    # 1) Preferred: /api/tags
                    try:
                        resp = await client.get(f"{base_url}/api/tags")
                        status_code = resp.status_code
                        if resp.status_code == 200:
                            data = resp.json()
                            models = data.get("models", [])
                            models_sample = [m.get("name") for m in models if m.get("name")][:3]
                            msg = "Ollama reachable"
                        else:
                            msg = f"Ollama /api/tags HTTP {resp.status_code}"
                    except Exception as e1:
                        # 2) Fallback: GET /
                        try:
                            resp = await client.get(f"{base_url}/")
                            status_code = resp.status_code
                            text = resp.text or ""
                            if resp.status_code == 200 and "Ollama is running" in text:
                                msg = "Ollama root reachable"
                            else:
                                msg = f"Ollama root HTTP {resp.status_code}"
                        except Exception as e2:
                            # 3) If localhost, try 127.0.0.1 swap
                            if "localhost" in base_url:
                                host_swapped = base_url.replace("localhost", "127.0.0.1")
                                try:
                                    resp = await client.get(f"{host_swapped}/api/tags")
                                    status_code = resp.status_code
                                    if resp.status_code == 200:
                                        data = resp.json()
                                        models = data.get("models", [])
                                        models_sample = [m.get("name") for m in models if m.get("name")][:3]
                                        msg = "Ollama reachable via 127.0.0.1"
                                        base_url = host_swapped
                                    else:
                                        msg = f"Ollama HTTP {resp.status_code} via 127.0.0.1"
                                except Exception as e3:
                                    msg = f"Probe error (ollama): {e1}; fallback: {e2}; swap: {e3}"
                else:
                    # OpenAI-compatible first
                    resp = await client.get(f"{base_url}/v1/models")
                    status_code = resp.status_code
                    if resp.status_code == 200:
                        data = resp.json()
                        items = data.get("data", []) if isinstance(data, dict) else []
                        for m in items:
                            mid = m.get("id") or m.get("name")
                            if mid:
                                models_sample.append(mid)
                        models_sample = models_sample[:3]
                        msg = "OpenAI-compatible reachable"
                    else:
                        # Fallback to /models
                        try:
                            resp2 = await client.get(f"{base_url}/models")
                            status_code = resp2.status_code
                            if resp2.status_code == 200:
                                data = resp2.json()
                                items = data.get("data", []) if isinstance(data, dict) else []
                                for m in items:
                                    mid = m.get("id") or m.get("name")
                                    if mid:
                                        models_sample.append(mid)
                                models_sample = models_sample[:3]
                                msg = "Models endpoint reachable"
                            else:
                                msg = f"Models endpoint HTTP {resp2.status_code}"
                        except Exception as e2:
                            msg = f"Probe error (openai): HTTP {status_code}; fallback: {e2}"
            except Exception as e:
                msg = f"Probe error: {str(e)}"

        latency_ms = (_time.time() - start) * 1000.0
        connected = status_code == 200

        return {
            "id": target.id,
            "name": target.name,
            "base_url": base_url,
            "provider": provider,
            "connected": connected,
            "status_code": status_code,
            "latency_ms": latency_ms,
            "message": msg,
            "models_sample": models_sample,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing llm connection {conn_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/env")
async def update_env_config(
    config: EnvConfigUpdate,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Update .env file with new configuration.
    
    This endpoint persists GUI changes to the .env file.
    """
    try:
        # Backup existing config
        config_writer.backup_config(".env")
        
        # Write new config
        success = config_writer.write_env_file(config.variables)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to write .env file")
        
        # Clear settings cache to reload new values
        clear_settings_cache()
        
        return {
            "success": True,
            "message": f"Successfully updated {len(config.variables)} environment variables",
            "variables_updated": list(config.variables.keys())
        }
        
    except Exception as e:
        logger.error(f"Error updating .env config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents")
async def update_agents_config(
    agents: List[AgentConfig],
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Update agents.json configuration file.
    
    This endpoint persists agent configurations from GUI.
    """
    try:
        # Backup existing config
        config_writer.backup_config("agents.json")
        
        # Convert to dict format
        agents_list = [agent.dict() for agent in agents]
        
        # Write new config
        success = config_writer.write_agents_config(agents_list)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to write agents.json")
        
        # Clear settings cache
        clear_settings_cache()
        
        return {
            "success": True,
            "message": f"Successfully updated {len(agents)} agent configurations",
            "agents": [agent.name for agent in agents]
        }
        
    except Exception as e:
        logger.error(f"Error updating agents config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/datasources")
async def update_datasources_config(
    datasources: List[DataSourceConfig],
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Update datasources.json configuration file.
    
    This endpoint persists datasource configurations from GUI.
    """
    try:
        # Backup existing config
        config_writer.backup_config("datasources.json")
        
        # Convert to dict format
        datasources_list = [ds.dict() for ds in datasources]
        
        # Write new config
        success = config_writer.write_datasources_config(datasources_list)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to write datasources.json")
        
        # Clear settings cache
        clear_settings_cache()
        
        return {
            "success": True,
            "message": f"Successfully updated {len(datasources)} datasource configurations",
            "datasources": [ds.name for ds in datasources]
        }
        
    except Exception as e:
        logger.error(f"Error updating datasources config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tools")
async def update_tools_config(
    tools: List[ToolConfig],
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Update tools.json configuration file.
    
    This endpoint persists tool configurations from GUI.
    """
    try:
        # Backup existing config
        config_writer.backup_config("tools.json")
        
        # Convert to dict format
        tools_list = [tool.dict() for tool in tools]
        
        # Write new config
        success = config_writer.write_tools_config(tools_list)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to write tools.json")
        
        # Clear settings cache
        clear_settings_cache()
        
        return {
            "success": True,
            "message": f"Successfully updated {len(tools)} tool configurations",
            "tools": [tool.name for tool in tools]
        }
        
    except Exception as e:
        logger.error(f"Error updating tools config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents")
async def get_agents_config(
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """Get current agents configuration."""
    try:
        config = config_writer.read_json_config("agents.json")
        
        if config is None:
            return {"agents": []}
        
        return config
        
    except Exception as e:
        logger.error(f"Error reading agents config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasources")
async def get_datasources_config(
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """Get current datasources configuration."""
    try:
        config = config_writer.read_json_config("datasources.json")
        
        if config is None:
            return {"datasources": []}
        
        return config
        
    except Exception as e:
        logger.error(f"Error reading datasources config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools")
async def get_tools_config(
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """Get current tools configuration."""
    try:
        config = config_writer.read_json_config("tools.json")
        
        if config is None:
            return {"tools": []}
        
        return config
        
    except Exception as e:
        logger.error(f"Error reading tools config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/llm-connections")
async def get_llm_connections(settings: Settings = Depends(get_settings)) -> Dict[str, Any]:
    """Get LLM connections from file plus default single-LLM fallback."""
    try:
        # Read from default path relative to backend working dir
        from pathlib import Path
        import json as _json
        path = Path("config/llm_connections.json")
        file_conns = []
        if path.exists():
            try:
                with open(path, 'r') as f:
                    file_conns = (_json.load(f) or {}).get("connections", [])
            except Exception:
                file_conns = []

        # Merge with settings.llm_connections (already loaded & includes default if set)
        merged: Dict[str, LLMConnection] = {}
        for c in file_conns:
            try:
                conn = LLMConnection(**c)
                merged[conn.id] = conn
            except Exception:
                continue
        for cid, cfg in settings.llm_connections.items():
            try:
                conn = LLMConnection(**cfg.dict())
                merged[cid] = conn
            except Exception:
                pass

        return {"connections": [c.dict() for c in merged.values()]}
    except Exception as e:
        logger.error(f"Error reading llm connections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/llm-connections")
async def create_llm_connection(connection: LLMConnection) -> Dict[str, Any]:
    """Create or update an LLM connection in llm_connections.json after testing connectivity."""
    import time as _time
    import httpx as _httpx
    
    # First, test the connection
    test_result = {
        "connected": False,
        "message": "Not tested",
        "latency_ms": 0,
        "provider": "unknown"
    }
    
    try:
        base_url = connection.base_url.rstrip('/')
        headers = {"Content-Type": "application/json"}
        if connection.api_key:
            headers["Authorization"] = f"Bearer {connection.api_key}"
        
        # Detect provider
        def detect_provider(url: str) -> str:
            u = (url or "").lower()
            if "ollama" in u or "11434" in u:
                return "ollama"
            if "openai" in u or "/v1" in u:
                return "openai"
            return "unknown"
        
        provider = detect_provider(base_url)
        test_result["provider"] = provider
        
        start = _time.time()
        async with _httpx.AsyncClient(timeout=connection.timeout or 10, headers=headers) as client:
            if provider == "ollama":
                # Try /api/tags for Ollama
                try:
                    resp = await client.get(f"{base_url}/api/tags")
                    if resp.status_code == 200:
                        test_result["connected"] = True
                        test_result["message"] = "Ollama server reachable"
                    else:
                        test_result["message"] = f"Ollama responded with status {resp.status_code}"
                except Exception as e:
                    # Try root endpoint
                    try:
                        resp = await client.get(f"{base_url}/")
                        if resp.status_code == 200 and "Ollama is running" in resp.text:
                            test_result["connected"] = True
                            test_result["message"] = "Ollama server reachable (root endpoint)"
                        else:
                            test_result["message"] = f"Cannot reach Ollama: {str(e)}"
                    except Exception as e2:
                        test_result["message"] = f"Cannot reach Ollama: {str(e2)}"
            else:
                # Try OpenAI-compatible endpoints
                try:
                    resp = await client.get(f"{base_url}/v1/models")
                    if resp.status_code == 200:
                        test_result["connected"] = True
                        test_result["message"] = "OpenAI-compatible server reachable"
                    else:
                        test_result["message"] = f"Server responded with status {resp.status_code}"
                except Exception as e:
                    try:
                        resp = await client.get(f"{base_url}/models")
                        if resp.status_code == 200:
                            test_result["connected"] = True
                            test_result["message"] = "LLM server reachable"
                        else:
                            test_result["message"] = f"Cannot reach server: {str(e)}"
                    except Exception as e2:
                        test_result["message"] = f"Cannot reach server: {str(e2)}"
        
        elapsed = (_time.time() - start) * 1000
        test_result["latency_ms"] = round(elapsed, 2)
        
    except Exception as e:
        test_result["message"] = f"Connection test failed: {str(e)}"
        logger.error(f"Error testing LLM connection: {e}")
    
    # If connection test failed, return error
    if not test_result["connected"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Connection test failed: {test_result['message']}. Please verify the URL and ensure the LLM server is accessible."
        )
    
    # Connection successful, save it
    try:
        from pathlib import Path
        import json as _json
        path = Path("config/llm_connections.json")
        cfg = {"connections": []}
        if path.exists():
            with open(path, 'r') as f:
                try:
                    cfg = _json.load(f) or cfg
                except Exception:
                    pass
        
        # Remove existing connection with same ID if exists
        cfg["connections"] = [c for c in cfg.get("connections", []) if c.get("id") != connection.id]
        
        # Add new connection
        cfg["connections"].append(connection.dict())
        
        # Persist back
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            _json.dump(cfg, f, indent=2)
        clear_settings_cache()
        
        return {
            "success": True, 
            "connection": connection.dict(),
            "test_result": test_result
        }
    except Exception as e:
        logger.error(f"Error creating llm connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/llm-connections/{conn_id}")
async def delete_llm_connection(conn_id: str) -> Dict[str, Any]:
    """Delete an LLM connection from llm_connections.json (no-op for default)."""
    try:
        from pathlib import Path
        import json as _json
        path = Path("config/llm_connections.json")
        cfg = {"connections": []}
        if path.exists():
            with open(path, 'r') as f:
                try:
                    cfg = _json.load(f) or cfg
                except Exception:
                    pass
        before = len(cfg.get("connections", []))
        cfg["connections"] = [c for c in cfg.get("connections", []) if c.get("id") != conn_id]
        after = len(cfg.get("connections", []))
        # Persist back
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            _json.dump(cfg, f, indent=2)
        clear_settings_cache()
        return {"success": True, "removed": before - after}
    except Exception as e:
        logger.error(f"Error deleting llm connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reload")
async def reload_configuration() -> Dict[str, Any]:
    """
    Reload configuration from files.
    
    Clears the settings cache and forces a reload from disk.
    """
    try:
        clear_settings_cache()
        
        # Get fresh settings
        new_settings = get_settings()
        
        return {
            "success": True,
            "message": "Configuration reloaded successfully",
            "agents_count": len(new_settings.external_agents),
            "datasources_count": len(new_settings.datasources),
            "tools_count": len(new_settings.tools)
        }
        
    except Exception as e:
        logger.error(f"Error reloading configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
