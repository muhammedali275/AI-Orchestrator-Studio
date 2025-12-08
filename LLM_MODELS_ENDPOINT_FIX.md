# LLM Models Endpoint Fix

## Issue
When opening the chat in the app, users could not see the installed LLM models from localhost. The `/api/chat/ui/models` endpoint was not properly fetching models from Ollama.

## Root Cause
The endpoint had several issues:
1. Insufficient logging to debug connection issues
2. Generic error handling that masked the actual problem
3. No specific error types for connection vs timeout issues
4. Limited visibility into what was happening during the model fetch process

## Solution Implemented

### File Modified
- `backend/orchestrator/app/api/chat_ui.py` - Enhanced the `/models` endpoint

### Changes Made

1. **Enhanced Logging**
   - Added detailed logging at each step of the model fetching process
   - Log the LLM base URL being used
   - Log detection of Ollama vs OpenAI-compatible endpoints
   - Log response status codes and data
   - Log formatted model counts
   - Added `exc_info=True` for better error stack traces

2. **Improved Error Handling**
   - Specific handling for `httpx.ConnectError` (connection refused)
   - Specific handling for `httpx.TimeoutException` (timeout)
   - Better fallback chain with clear messages

3. **Better Response Format**
   - Added `source` field to indicate where models came from (ollama, openai-compatible, config, fallback)
   - Consistent response structure across all code paths
   - Clear messages explaining why fallback models are being used

4. **Ollama Detection**
   - Improved detection logic for Ollama servers
   - Proper handling of Ollama's `/api/tags` endpoint
   - Better model name extraction from Ollama response

## Testing Steps

1. **Test with Ollama Running**
   ```bash
   # Start Ollama
   ollama serve
   
   # Test the endpoint
   curl http://localhost:8001/api/chat/ui/models
   ```
   Expected: Should return actual models from Ollama

2. **Test with Ollama Not Running**
   ```bash
   # Stop Ollama
   # Test the endpoint
   curl http://localhost:8001/api/chat/ui/models
   ```
   Expected: Should return fallback models with appropriate message

3. **Test in Chat Studio**
   - Open Chat Studio at http://localhost:3001
   - Check the Model dropdown
   - Should see either:
     - Actual Ollama models if Ollama is running
     - Fallback models with a message if Ollama is not available

4. **Check Backend Logs**
   - Look for `[Chat UI]` prefixed log messages
   - Should see detailed information about:
     - LLM base URL being used
     - Endpoint detection (Ollama vs OpenAI)
     - Response status and data
     - Any errors encountered

## Configuration Requirements

Ensure the following environment variables are set in `backend/orchestrator/.env`:

```env
# LLM Configuration
LLM_BASE_URL=http://localhost:11434
LLM_DEFAULT_MODEL=llama2
```

## Troubleshooting

### Models Not Showing
1. Check if Ollama is running: `curl http://localhost:11434/api/tags`
2. Check backend logs for `[Chat UI]` messages
3. Verify `LLM_BASE_URL` in `.env` file
4. Ensure Chat Studio backend is running on port 8001

### Connection Errors
- **Error**: "Connection error to LLM server"
  - **Solution**: Start Ollama with `ollama serve`
  
- **Error**: "Timeout connecting to LLM server"
  - **Solution**: Check if Ollama is responsive, may need to restart

### Fallback Models Showing
- This is expected behavior when Ollama is not available
- The app will still work, but you'll need to configure the actual model URL
- Check logs to see why real models couldn't be fetched

## Benefits of This Fix

1. **Better Debugging**: Detailed logs make it easy to diagnose issues
2. **Graceful Degradation**: App continues to work even if Ollama is down
3. **Clear User Feedback**: Messages explain why fallback models are being used
4. **Robust Error Handling**: Specific handling for different error types
5. **Source Tracking**: Know where models came from (ollama, config, fallback)

## Related Files
- `frontend/src/pages/ChatStudio.tsx` - Frontend that consumes this endpoint
- `backend/orchestrator/app/config.py` - Configuration settings
- `backend/orchestrator/config/example.env` - Environment variable examples

## Next Steps

1. Restart the Chat Studio backend to apply changes
2. Test with Ollama running and not running
3. Verify models appear correctly in the UI
4. Check logs for any issues

## Date
2025-01-XX

## Status
✅ Implemented and Ready for Testing
