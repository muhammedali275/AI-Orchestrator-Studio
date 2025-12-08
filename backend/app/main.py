from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import yaml
import aiofiles
from pathlib import Path

app = FastAPI(title="ZainOne Orchestrator Studio API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class FileContentRequest(BaseModel):
    content: str

class SettingsUpdate(BaseModel):
    llm_model: Optional[str] = None
    llm_endpoint: Optional[str] = None

class ToolConfig(BaseModel):
    name: str
    type: str
    config: Dict[str, Any]

class ToolsConfigUpdate(BaseModel):
    tools: List[ToolConfig]

# Helper functions
def get_orchestrator_path():
    return os.getenv("ORCHESTRATOR_PATH", os.path.join(os.getcwd(), "orchestrator"))

def get_config_path():
    return os.path.join(get_orchestrator_path(), "etc", "enterprise-agent", "settings.yaml")

# File management endpoints
@app.get("/api/files/list")
async def list_files(path: str = Query(default="")):
    """List files in a directory"""
    try:
        base_path = get_orchestrator_path()
        target_path = os.path.join(base_path, path) if path else base_path
        
        if not os.path.exists(target_path):
            raise HTTPException(status_code=404, detail="Path not found")
        
        items = []
        for item in os.listdir(target_path):
            item_path = os.path.join(target_path, item)
            relative_path = os.path.relpath(item_path, base_path)
            items.append({
                "name": item,
                "type": "directory" if os.path.isdir(item_path) else "file",
                "path": relative_path
            })
        
        return {"files": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/files/content")
async def get_file_content(path: str = Query(...)):
    """Get content of a file"""
    try:
        base_path = get_orchestrator_path()
        file_path = os.path.join(base_path, path)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        if not os.path.isfile(file_path):
            raise HTTPException(status_code=400, detail="Path is not a file")
        
        async with aiofiles.open(file_path, 'r') as f:
            content = await f.read()
        
        return {"content": content, "path": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/files/content")
async def update_file_content(path: str = Query(...), request: FileContentRequest = None):
    """Update content of a file"""
    try:
        base_path = get_orchestrator_path()
        file_path = os.path.join(base_path, path)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        async with aiofiles.open(file_path, 'w') as f:
            await f.write(request.content)
        
        return {"message": "File updated successfully", "path": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/files/create")
async def create_file(path: str = Query(...), request: FileContentRequest = None):
    """Create a new file"""
    try:
        base_path = get_orchestrator_path()
        file_path = os.path.join(base_path, path)
        
        # Check if file already exists
        if os.path.exists(file_path):
            raise HTTPException(status_code=400, detail="File already exists")
        
        # Create parent directories if they don't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Create the file with content
        content = request.content if request and request.content else ""
        async with aiofiles.open(file_path, 'w') as f:
            await f.write(content)
        
        return {"message": "File created successfully", "path": path}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/folders/create")
async def create_folder(path: str = Query(...)):
    """Create a new folder"""
    try:
        base_path = get_orchestrator_path()
        folder_path = os.path.join(base_path, path)
        
        # Check if folder already exists
        if os.path.exists(folder_path):
            raise HTTPException(status_code=400, detail="Folder already exists")
        
        # Create the folder
        os.makedirs(folder_path, exist_ok=True)
        
        return {"message": "Folder created successfully", "path": path}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/files/delete")
async def delete_file(path: str = Query(...)):
    """Delete a file or folder"""
    try:
        base_path = get_orchestrator_path()
        target_path = os.path.join(base_path, path)
        
        if not os.path.exists(target_path):
            raise HTTPException(status_code=404, detail="File or folder not found")
        
        # Delete file or folder
        if os.path.isfile(target_path):
            os.remove(target_path)
            return {"message": "File deleted successfully", "path": path}
        elif os.path.isdir(target_path):
            import shutil
            shutil.rmtree(target_path)
            return {"message": "Folder deleted successfully", "path": path}
        else:
            raise HTTPException(status_code=400, detail="Invalid path")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Configuration endpoints
@app.get("/api/config/settings")
async def get_settings():
    """Get current settings"""
    try:
        config_path = get_config_path()
        
        if os.path.exists(config_path):
            async with aiofiles.open(config_path, 'r') as f:
                content = await f.read()
                settings = yaml.safe_load(content) or {}
        else:
            settings = {}
        
        return {"settings": settings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/config/settings")
async def update_settings(settings: Dict[str, Any]):
    """Update settings"""
    try:
        config_path = get_config_path()
        
        # Load existing settings
        if os.path.exists(config_path):
            async with aiofiles.open(config_path, 'r') as f:
                content = await f.read()
                current_settings = yaml.safe_load(content) or {}
        else:
            current_settings = {}
        
        # Update with new settings
        current_settings.update(settings)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # Write updated settings
        async with aiofiles.open(config_path, 'w') as f:
            await f.write(yaml.dump(current_settings))
        
        return {"message": "Settings updated successfully", "settings": current_settings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Memory management endpoints
@app.get("/api/memory/stats")
async def get_memory_stats():
    """Get memory and cache statistics"""
    # Mock data for now - in production, this would query Redis/actual memory stores
    return {
        "conversation_count": 5,
        "cache_hit_rate": 0.85,
        "redis_memory_usage": "45.2 MB",
        "state_store_entries": 12
    }

@app.post("/api/memory/clear")
async def clear_memory():
    """Clear memory and cache"""
    # Mock implementation - in production, this would clear Redis/memory stores
    return {"message": "Memory cleared successfully"}

# Tools configuration endpoints
@app.get("/api/tools/config")
async def get_tools_config():
    """Get tools configuration"""
    try:
        tools_path = os.path.join(
            get_orchestrator_path(),
            "etc", "enterprise-agent", "tools.yaml"
        )
        
        if os.path.exists(tools_path):
            async with aiofiles.open(tools_path, 'r') as f:
                content = await f.read()
                config = yaml.safe_load(content) or {}
        else:
            # Default tools configuration
            config = {
                "tools": [
                    {
                        "name": "web_search",
                        "type": "search",
                        "config": {
                            "api_key": "",
                            "endpoint": "https://api.search.com"
                        }
                    },
                    {
                        "name": "code_executor",
                        "type": "execution",
                        "config": {
                            "timeout": "30",
                            "max_memory": "512MB"
                        }
                    }
                ]
            }
        
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/tools/config")
async def update_tools_config(config: List[ToolConfig]):
    """Update tools configuration"""
    try:
        tools_path = os.path.join(
            get_orchestrator_path(),
            "etc", "enterprise-agent", "tools.yaml"
        )
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(tools_path), exist_ok=True)
        
        # Convert to dict format
        tools_dict = {"tools": [tool.dict() for tool in config]}
        
        # Write configuration
        async with aiofiles.open(tools_path, 'w') as f:
            await f.write(yaml.dump(tools_dict))
        
        return {"message": "Tools configuration updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Topology/Graph endpoints
@app.get("/api/topology/graph")
async def get_topology_graph():
    """Get orchestrator topology graph"""
    # Return proper format with label and description at node level
    return {
        "nodes": [
            {
                "id": "start",
                "type": "start",
                "label": "Start",
                "description": "Entry Point - Receives user input",
                "status": "idle"
            },
            {
                "id": "intent_router",
                "type": "intent_router",
                "label": "Intent Router",
                "description": "Analyzes and classifies user intent",
                "status": "idle"
            },
            {
                "id": "planner",
                "type": "planner",
                "label": "Planner",
                "description": "Plans execution strategy and task breakdown",
                "status": "idle"
            },
            {
                "id": "llm_agent",
                "type": "llm_agent",
                "label": "LLM Agent",
                "description": "Processes with configured LLM (llama3)",
                "status": "idle"
            },
            {
                "id": "tool_executor",
                "type": "tool_executor",
                "label": "Tool Executor",
                "description": "Executes configured tools and actions",
                "status": "idle"
            },
            {
                "id": "grounding",
                "type": "grounding",
                "label": "Data Grounding",
                "description": "Retrieves context from data sources (RAG)",
                "status": "idle"
            },
            {
                "id": "memory_store",
                "type": "memory_store",
                "label": "Memory Store",
                "description": "Manages conversation cache and state",
                "status": "idle"
            },
            {
                "id": "audit",
                "type": "audit",
                "label": "Audit Log",
                "description": "Records execution for compliance",
                "status": "idle"
            },
            {
                "id": "end",
                "type": "end",
                "label": "End",
                "description": "Returns final response to user",
                "status": "idle"
            }
        ],
        "edges": [
            {"source": "start", "target": "intent_router", "label": "input"},
            {"source": "intent_router", "target": "planner", "label": "route"},
            {"source": "planner", "target": "llm_agent", "label": "plan"},
            {"source": "llm_agent", "target": "tool_executor", "label": "tool_call"},
            {"source": "tool_executor", "target": "grounding", "label": "fetch_data"},
            {"source": "grounding", "target": "llm_agent", "label": "context"},
            {"source": "llm_agent", "target": "memory_store", "label": "store"},
            {"source": "memory_store", "target": "audit", "label": "log"},
            {"source": "audit", "target": "end", "label": "result"},
            {"source": "llm_agent", "target": "end", "label": "complete"}
        ],
        "metadata": {
            "total_nodes": 9,
            "total_edges": 10,
            "llm_configured": True,
            "tools_configured": False
        }
    }

# Database management endpoints
@app.get("/api/db/status")
async def get_db_status():
    """Get database connection status"""
    return {
        "postgres": {"status": "connected", "connections": 5},
        "redis": {"status": "connected", "memory": "45.2 MB"},
        "vector_db": {"status": "connected", "collections": 3}
    }

@app.get("/api/db/collections")
async def get_db_collections():
    """Get vector database collections"""
    return {
        "collections": [
            {"name": "documents", "count": 1250, "dimension": 1536},
            {"name": "conversations", "count": 450, "dimension": 768},
            {"name": "code_snippets", "count": 890, "dimension": 1536}
        ]
    }

# LLM endpoints
@app.get("/api/llm/models")
async def get_llm_models():
    """Get available LLM models"""
    try:
        # In production, fetch from LLM client
        models = [
            "llama4-scout",
            "ossgpt-70b",
            "gpt-4",
            "gpt-3.5-turbo",
            "claude-3-opus",
            "claude-3-sonnet",
        ]
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/llm/test-connection")
async def test_llm_connection(request: Dict[str, Any]):
    """Test LLM server connection"""
    try:
        server_path = request.get("server_path", "")
        port = request.get("port", "")
        endpoint = request.get("endpoint", "")
        model = request.get("model", "")
        timeout = request.get("timeout", 60)
        
        full_url = f"{server_path}:{port}{endpoint}"
        
        # In production, make actual request to LLM server
        # For now, simulate connection test
        import asyncio
        await asyncio.sleep(0.5)  # Simulate network delay
        
        # Mock successful response
        return {
            "success": True,
            "url": full_url,
            "model_info": {
                "model": model,
                "status": "available",
                "version": "1.0.0",
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/llm/system-stats")
async def get_llm_system_stats():
    """Get system statistics (CPU, Memory, GPU)"""
    try:
        import psutil
        
        # CPU Usage
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        # Memory Usage
        memory = psutil.virtual_memory()
        memory_total = memory.total / (1024 ** 3)  # Convert to GB
        memory_used = memory.used / (1024 ** 3)
        memory_percent = memory.percent
        
        # Disk Usage
        disk = psutil.disk_usage('/')
        disk_total = disk.total / (1024 ** 3)
        disk_used = disk.used / (1024 ** 3)
        disk_percent = disk.percent
        
        # GPU Usage (mock for now - in production use nvidia-smi or similar)
        gpu_stats = {
            "available": True,
            "count": 1,
            "devices": [
                {
                    "id": 0,
                    "name": "NVIDIA GPU",
                    "memory_used": 4.2,
                    "memory_total": 8.0,
                    "memory_percent": 52.5,
                    "utilization": 45.0,
                    "temperature": 65,
                }
            ]
        }
        
        return {
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count,
                "frequency": cpu_freq.current if cpu_freq else 0,
            },
            "memory": {
                "total_gb": round(memory_total, 2),
                "used_gb": round(memory_used, 2),
                "percent": memory_percent,
            },
            "disk": {
                "total_gb": round(disk_total, 2),
                "used_gb": round(disk_used, 2),
                "percent": disk_percent,
            },
            "gpu": gpu_stats,
        }
    except ImportError:
        # If psutil is not installed, return mock data
        return {
            "cpu": {
                "percent": 45.5,
                "count": 8,
                "frequency": 2400,
            },
            "memory": {
                "total_gb": 16.0,
                "used_gb": 8.5,
                "percent": 53.1,
            },
            "disk": {
                "total_gb": 500.0,
                "used_gb": 250.0,
                "percent": 50.0,
            },
            "gpu": {
                "available": True,
                "count": 1,
                "devices": [
                    {
                        "id": 0,
                        "name": "NVIDIA GPU",
                        "memory_used": 4.2,
                        "memory_total": 8.0,
                        "memory_percent": 52.5,
                        "utilization": 45.0,
                        "temperature": 65,
                    }
                ]
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/llm/test-port")
async def test_port_connectivity(request: Dict[str, Any]):
    """Test port connectivity using telnet-like functionality"""
    try:
        import socket
        import asyncio
        
        host = request.get("host", "localhost")
        port = request.get("port", 8000)
        timeout = request.get("timeout", 5)
        
        # Remove protocol if present
        if "://" in host:
            host = host.split("://")[1]
        
        # Remove port if present in host
        if ":" in host:
            host = host.split(":")[0]
        
        # Special handling for localhost
        if host.lower() == "localhost":
            # Try with 127.0.0.1 if localhost doesn't work
            hosts_to_try = ["localhost", "127.0.0.1"]
        else:
            hosts_to_try = [host]
        
        start_time = asyncio.get_event_loop().time()
        
        # Try each host
        for current_host in hosts_to_try:
            try:
                # Test connection
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                
                result = sock.connect_ex((current_host, int(port)))
                latency = (asyncio.get_event_loop().time() - start_time) * 1000  # Convert to ms
                
                if result == 0:
                    return {
                        "success": True,
                        "host": host,  # Return original host for UI consistency
                        "port": port,
                        "latency_ms": round(latency, 2),
                        "message": f"Port {port} is open and accessible"
                    }
                
                # Close socket before trying next host
                sock.close()
            except:
                # Continue to next host on any error
                if 'sock' in locals() and sock:
                    sock.close()
        
        # If we get here, all connection attempts failed
        return {
            "success": False,
            "host": host,
            "port": port,
            "message": f"Port {port} is closed or unreachable"
        }
            
    except socket.gaierror:
        return {
            "success": False,
            "host": host,
            "port": port,
            "message": "Hostname could not be resolved"
        }
    except socket.timeout:
        return {
            "success": False,
            "host": host,
            "port": port,
            "message": "Connection timeout"
        }
    except Exception as e:
        return {
            "success": False,
            "host": host,
            "port": port,
            "message": str(e)
        }

# Tools endpoints
@app.post("/api/tools/test-connection")
async def test_tool_connection(request: Dict[str, Any]):
    """Test tool connection"""
    try:
        name = request.get("name", "")
        endpoint = request.get("endpoint", "")
        port = request.get("port", "")
        timeout = request.get("timeout", 30)
        
        # In production, make actual request to tool endpoint
        # For now, simulate connection test
        import asyncio
        await asyncio.sleep(0.3)  # Simulate network delay
        
        # Mock successful response
        return {
            "success": True,
            "tool": name,
            "endpoint": f"{endpoint}:{port}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# Admin endpoints
@app.get("/api/admin/users")
async def get_admin_users():
    """Get all users"""
    try:
        # In production, fetch from database
        users = [
            {
                "id": "1",
                "username": "admin",
                "email": "admin@zainone.com",
                "role": "Administrator",
                "status": "active",
                "lastLogin": "2024-01-15 10:30:00",
            },
            {
                "id": "2",
                "username": "developer",
                "email": "dev@zainone.com",
                "role": "Developer",
                "status": "active",
                "lastLogin": "2024-01-15 09:15:00",
            },
        ]
        return {"users": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/metrics")
async def get_admin_metrics():
    """Get system metrics"""
    try:
        # In production, fetch real metrics
        metrics = [
            {
                "name": "API Response Time",
                "value": "45ms",
                "status": "healthy",
                "description": "Average API response time",
            },
            {
                "name": "Error Rate",
                "value": "0.5%",
                "status": "healthy",
                "description": "Percentage of failed requests",
            },
            {
                "name": "Active Sessions",
                "value": "12",
                "status": "healthy",
                "description": "Currently active user sessions",
            },
        ]
        return {"metrics": metrics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/feature-flags")
async def get_feature_flags():
    """Get feature flags"""
    try:
        # In production, fetch from database/config
        flags = [
            {
                "name": "advanced_analytics",
                "enabled": True,
                "description": "Enable advanced analytics features",
            },
            {
                "name": "experimental_llm",
                "enabled": False,
                "description": "Enable experimental LLM models",
            },
        ]
        return {"flags": flags}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/admin/feature-flags")
async def update_feature_flags(request: Dict[str, Any]):
    """Update feature flags"""
    try:
        flags = request.get("flags", [])
        # In production, save to database/config
        return {"message": "Feature flags updated successfully", "flags": flags}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ZainOne Orchestrator Studio API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
