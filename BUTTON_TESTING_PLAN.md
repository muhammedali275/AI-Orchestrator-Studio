# Button Testing Plan for ZainOne Orchestrator Studio

This document outlines a comprehensive testing plan for all buttons in the ZainOne Orchestrator Studio application, with special focus on the LLM IP and port configuration that had issues with localhost.

## LLM Configuration Page

### Issue: LLM IP and Port Configuration with localhost

The primary issue reported is that setting the LLM IP to "localhost" and configuring the port doesn't work properly. Based on the code review, here's what needs to be tested and fixed:

#### Test Cases for LLM Configuration:

1. **Server Path Input**
   - Enter "localhost" in the Server Path field
   - Enter "http://localhost" in the Server Path field
   - Enter "127.0.0.1" in the Server Path field
   - Enter "http://127.0.0.1" in the Server Path field
   - Enter a remote IP address (e.g., "192.168.1.100")

2. **Port Input**
   - Enter "11434" (default Ollama port)
   - Enter "8000" (API server port)
   - Enter other valid ports

3. **Test Connection Button**
   - Test with localhost + 11434
   - Test with http://localhost + 11434
   - Test with 127.0.0.1 + 11434
   - Test with http://127.0.0.1 + 11434

4. **Port Testing Functionality**
   - Test with localhost + 11434
   - Test with 127.0.0.1 + 11434
   - Test with invalid hostname
   - Test with closed port

5. **Save Configuration Button**
   - Save with localhost configuration
   - Verify configuration is saved correctly

### Root Cause Analysis:

Based on the code review, the potential issues with localhost could be:

1. In `backend/app/main.py`, the `test_port_connectivity` function:
   - It removes protocol if present (`http://` or similar)
   - It removes port if present in host
   - It uses socket connection to test port
   - For localhost, this should work correctly, but there might be issues with how the frontend is handling the URL construction

2. In `LLMConfig.tsx`, the port testing functionality:
   - It sends a request to `/api/llm/test-port` with host and port
   - The UI shows the result of the test

3. In `llm_client.py`, the connection logic:
   - It has special handling for Ollama endpoints (checking for "11434" in URL or "ollama" in URL)
   - It constructs different endpoints based on the LLM type

## Other Button Testing

### Topology Page

1. **Fetch Graph Button**
   - Test clicking to refresh the graph
   - Verify graph is loaded correctly

2. **Start Execution Button**
   - Test starting a topology execution
   - Verify execution starts correctly

3. **Stop Execution Button**
   - Test stopping a running execution
   - Verify execution stops correctly

4. **View Logs Button**
   - Test viewing execution logs
   - Verify logs are displayed correctly

5. **Test Component Button**
   - Test individual component testing
   - Verify test results are displayed

### Tools Configuration Page

1. **Toggle Enable/Disable Button**
   - Test enabling/disabling tools
   - Verify state changes correctly

2. **Test Connection Button**
   - Test connection for each tool
   - Verify connection status is displayed correctly

3. **Delete Tool Button**
   - Test deleting a tool
   - Verify tool is removed from the list

4. **Add New Tool Button**
   - Test adding a new tool
   - Verify tool is added to the list

5. **Save Configuration Button**
   - Test saving tool configurations
   - Verify configurations are saved correctly

### Monitoring Page

1. **Add Server Button**
   - Test adding a new server
   - Verify server is added to the list

2. **Test Connection Button**
   - Test connection to each server
   - Verify connection status is displayed correctly

3. **View Metrics Button**
   - Test viewing server metrics
   - Verify metrics are displayed correctly

4. **Delete Server Button**
   - Test deleting a server
   - Verify server is removed from the list

5. **Refresh Metrics Button**
   - Test refreshing metrics
   - Verify metrics are updated

### System Configuration Page

1. **Save Configuration Button**
   - Test saving system configurations
   - Verify configurations are saved correctly

2. **Reload Configuration Button**
   - Test reloading configurations
   - Verify configurations are reloaded correctly

## Testing Procedure

For each button:

1. Click the button
2. Verify the expected action occurs
3. Check for any error messages in the console
4. Verify the UI updates correctly
5. Test with different input values where applicable

## LLM IP and Port Issue Resolution

Based on the code review, here are potential fixes for the localhost issue:

1. **URL Construction**: Ensure the frontend correctly constructs the URL with protocol, host, and port
2. **Socket Connection**: Verify the backend correctly handles localhost and 127.0.0.1
3. **Error Handling**: Improve error messages to provide more details about connection failures
4. **Protocol Handling**: Ensure consistent handling of http:// prefix in both frontend and backend

## Testing Notes

- For the LLM configuration, pay special attention to how localhost is handled
- Test both with and without the http:// prefix
- Test with both localhost and 127.0.0.1
- Verify error messages are clear and helpful
- Check the browser console for any JavaScript errors
- Monitor the backend logs for any Python errors
