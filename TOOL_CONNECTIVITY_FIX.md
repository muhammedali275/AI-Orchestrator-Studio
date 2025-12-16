# Tool Connectivity Testing Fix

## Problem
When adding new tools in the Tools & Data Sources page, testing connections would timeout after 5 seconds with the error:
```
Tool endpoint connection timed out after 5 seconds.
```

## Root Cause
The backend API (`backend/orchestrator/app/api/tools.py`) had a hardcoded 5-second timeout for HTTP connectivity tests, which was insufficient for:
- Services that are slow to start or respond
- Services that aren't running yet
- Network latency issues

## Solution Implemented

### Backend Changes (`backend/orchestrator/app/api/tools.py`)

#### 1. **Dynamic Timeout Configuration**
- Replaced hardcoded 5-second timeout with tool's configured timeout
- Default timeout increased to 30 seconds
- Reads from `tool.config.timeout` or `tool.config.timeout_seconds`

#### 2. **Two-Stage Connectivity Testing**

**Stage 1: TCP Port Check (5 seconds)**
- Uses Python's `socket` library to check if the port is open
- Provides immediate feedback if the service isn't running
- Detects DNS resolution failures
- Identifies firewall/network issues

**Stage 2: HTTP Request (configurable timeout)**
- Only runs if port check succeeds
- Uses tool's configured timeout (default 30s)
- Tries HEAD request first (lighter), falls back to GET
- Follows redirects automatically
- Measures response time

#### 3. **Enhanced Error Messages**
Now provides specific error types with actionable suggestions:

| Error Type | Message | Suggestion |
|------------|---------|------------|
| `port_closed` | Port not reachable | Verify service is running, check firewall |
| `dns_error` | DNS resolution failed | Check hostname and DNS configuration |
| `port_timeout` | Port check timeout | Check network connectivity |
| `connection_refused` | Connection refused | Service not running or not accepting connections |
| `http_timeout` | HTTP request timeout | Increase timeout or check service performance |
| `http_error` | HTTP status error | Check authentication or endpoint path |

#### 4. **Additional Response Data**
The test response now includes:
- `host`: Extracted hostname
- `port`: Extracted port number
- `response_time_ms`: Response time in milliseconds
- `timeout_seconds`: Timeout value used
- `connectivity_status`: Detailed status code
- `suggestion`: Actionable troubleshooting advice

## Testing the Fix

### Test Scenario 1: Service Not Running
```bash
# Create a tool pointing to a non-running service
curl -X POST http://localhost:8000/api/tools \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test_tool",
    "type": "http_request",
    "config": {
      "base_url": "http://localhost:9999",
      "timeout": 30
    },
    "enabled": true
  }'

# Test connection
curl -X POST http://localhost:8000/api/tools/test_tool/test
```

**Expected Response:**
```json
{
  "success": false,
  "connectivity_tested": true,
  "connectivity_status": "port_closed",
  "host": "localhost",
  "port": 9999,
  "message": "Cannot connect to localhost:9999. Port appears to be closed or host is unreachable.",
  "suggestion": "Verify the service is running and the host/port are correct. Check firewall settings."
}
```

### Test Scenario 2: Service Running
```bash
# Test with a running service (e.g., backend itself)
curl -X POST http://localhost:8000/api/tools \
  -H "Content-Type: application/json" \
  -d '{
    "name": "backend_test",
    "type": "http_request",
    "config": {
      "base_url": "http://localhost:8000",
      "timeout": 30
    },
    "enabled": true
  }'

# Test connection
curl -X POST http://localhost:8000/api/tools/backend_test/test
```

**Expected Response:**
```json
{
  "success": true,
  "connectivity_tested": true,
  "connectivity_status": "reachable",
  "status_code": 200,
  "host": "localhost",
  "port": 8000,
  "response_time_ms": 15,
  "message": "Tool endpoint is reachable (HTTP 200)"
}
```

### Test Scenario 3: Skip Connectivity Test
```bash
# Save tool without testing connectivity
curl -X POST "http://localhost:8000/api/tools/test_tool/test?skip_connectivity=true"
```

**Expected Response:**
```json
{
  "success": true,
  "connectivity_tested": false,
  "connectivity_status": "skipped",
  "message": "Tool configuration is valid. Connectivity test skipped."
}
```

## Benefits

1. **Better User Experience**
   - Clear, actionable error messages
   - Faster feedback with port checking
   - No more generic timeout errors

2. **Flexible Configuration**
   - Respects tool's configured timeout
   - Can skip connectivity tests when needed
   - Works with various network conditions

3. **Improved Debugging**
   - Detailed connectivity status
   - Response time metrics
   - Specific error types

4. **Production Ready**
   - Handles DNS failures gracefully
   - Detects firewall issues
   - Works with slow services

## Frontend Compatibility

The existing frontend (`frontend/src/pages/ToolsDataSources.tsx`) is fully compatible with these changes:
- Already calls the test endpoint correctly
- Displays error messages from the response
- No frontend changes required

## Configuration Example

```json
{
  "name": "my_api_tool",
  "type": "http_request",
  "config": {
    "base_url": "https://api.example.com",
    "timeout": 60,
    "auth_token": "optional_token"
  },
  "enabled": true,
  "description": "External API integration"
}
```

## Rollback Instructions

If issues occur, revert the changes to `backend/orchestrator/app/api/tools.py`:
```bash
git checkout HEAD~1 backend/orchestrator/app/api/tools.py
```

## Next Steps

1. Restart the backend server to apply changes
2. Test with various tool configurations
3. Monitor logs for any connectivity issues
4. Consider adding similar improvements to datasource testing

## Related Files
- `backend/orchestrator/app/api/tools.py` - Main fix implementation
- `frontend/src/pages/ToolsDataSources.tsx` - Frontend UI (no changes needed)
- `backend/orchestrator/app/tools/registry.py` - Tool registry (no changes needed)
