# LLM Configuration Fix for Localhost Issue

Based on the code review, I've identified the issue with the localhost configuration in the LLM settings. Here's the fix:

## Issue Description

When configuring the LLM server with "localhost" as the IP and setting a port (e.g., 11434 for Ollama), the connection test fails even though the server is running correctly. This appears to be due to how the URL is constructed and how the socket connection test is performed.

## Root Cause

1. In `backend/app/main.py`, the `test_port_connectivity` function:
   - It removes protocol if present (`http://` or similar)
   - It removes port if present in host
   - The socket connection test should work with localhost, but there might be issues with hostname resolution

2. In `LLMConfig.tsx`, the port testing functionality:
   - It sends a request to `/api/llm/test-port` with host and port
   - The UI shows the result of the test

3. In `llm_client.py`, the connection logic:
   - It has special handling for Ollama endpoints (checking for "11434" in URL or "ollama" in URL)
   - It constructs different endpoints based on the LLM type

## Fix Implementation

### 1. Fix in `backend/app/main.py`

```python
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
                if sock:
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
```

### 2. Fix in `frontend/src/pages/LLMConfig.tsx`

In the `testConnection` function, ensure the URL is properly constructed:

```typescript
const testConnection = async () => {
  setTesting(true);
  setConnectionStatus({
    status: 'testing',
    message: 'Testing connection...',
  });

  try {
    const startTime = Date.now();
    
    // Ensure server_path has protocol
    let serverPath = settings.llm_server_path;
    if (!serverPath.startsWith('http://') && !serverPath.startsWith('https://')) {
      serverPath = `http://${serverPath}`;
    }
    
    const fullUrl = `${serverPath}:${settings.llm_port}${settings.llm_endpoint}`;
    
    const response = await axios.post(
      'http://localhost:8000/api/llm/test-connection',
      {
        server_path: serverPath,
        port: settings.llm_port,
        endpoint: settings.llm_endpoint,
        model: settings.llm_model,
        timeout: parseInt(settings.llm_timeout),
      },
      { timeout: parseInt(settings.llm_timeout) * 1000 }
    );

    const latency = Date.now() - startTime;

    if (response.data.success) {
      setConnectionStatus({
        status: 'connected',
        message: 'Connection successful!',
        latency,
        model_info: response.data.model_info,
      });
    } else {
      setConnectionStatus({
        status: 'disconnected',
        message: response.data.error || 'Connection failed',
      });
    }
  } catch (error: any) {
    setConnectionStatus({
      status: 'disconnected',
      message: error.response?.data?.detail || error.message || 'Connection failed',
    });
  } finally {
    setTesting(false);
  }
};
```

### 3. Fix in `backend/orchestrator/app/clients/llm_client.py`

Ensure the client properly handles localhost URLs:

```python
def __init__(self, settings: Settings):
    """
    Initialize LLM client with settings.
    
    Args:
        settings: Application settings containing LLM configuration
    """
    self.settings = settings
    
    # Ensure base_url has protocol
    base_url = settings.llm_base_url
    if base_url and not (base_url.startswith('http://') or base_url.startswith('https://')):
        base_url = f"http://{base_url}"
    
    self.base_url = base_url
    self.default_model = settings.llm_default_model
    self.timeout = settings.llm_timeout_seconds
    self.max_retries = settings.llm_max_retries
    self.api_key = settings.llm_api_key
    
    # HTTP client for making requests
    self.client = httpx.AsyncClient(
        timeout=httpx.Timeout(self.timeout),
        headers=self._get_headers()
    )
```

## Testing the Fix

After implementing these changes, test the LLM configuration with:

1. Server Path: "localhost" (without protocol)
2. Server Path: "http://localhost" (with protocol)
3. Server Path: "127.0.0.1" (IP address)
4. Port: 11434 (Ollama default)
5. Port: 8000 (API server)

The connection test should now work correctly with localhost, and the error message should be more informative if the connection fails.

## Additional Recommendations

1. Add more detailed error messages in the UI to help users troubleshoot connection issues
2. Add a tooltip or help text explaining the expected format for the server path (with or without protocol)
3. Consider adding a dropdown for common LLM server types (Ollama, OpenAI API, etc.) to simplify configuration
4. Add a "Detect" button that attempts to auto-detect running LLM servers on common ports
