# Chat Studio Quick Start Guide

## Current Status

✅ **Backend Configuration Created**
- `.env` file created in `backend/orchestrator/` with Llama3 settings
- LLM_BASE_URL: http://localhost:11434
- LLM_DEFAULT_MODEL: llama3

✅ **Servers Status**
- Backend: Running on port 8000 (should auto-reload with new .env)
- Frontend: Starting on port 3000

## Quick Test Steps

### 1. Verify Backend is Running
The backend should have automatically reloaded with the new `.env` file. Check the terminal for:
```
INFO:     Application startup complete.
```

### 2. Test LLM Connection
Open your browser and go to:
```
http://localhost:8000/api/llm/models
```

You should see a JSON response with your available models.

### 3. Access Chat Studio
Once the frontend finishes starting:
1. Go to http://localhost:3000
2. Click "Chat Studio" in the sidebar (3rd item)
3. You should see the chat interface

### 4. Start Chatting
1. Click "New Chat" button
2. The model dropdown should show "llama3"
3. Select "Direct LLM" as the routing profile
4. Type a message like "Hello, how are you?"
5. Press Enter or click Send

## Troubleshooting

### If Models Don't Appear
1. Make sure Ollama is running: `ollama serve`
2. Check if llama3 is installed: `ollama list`
3. If not installed: `ollama pull llama3`

### If Backend Won't Start
1. Stop the backend (CTRL+C)
2. Install missing dependency: `pip install pydantic-settings`
3. Restart: `cd backend/orchestrator && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`

### If Chat Doesn't Work
1. Open browser console (F12)
2. Check for any error messages
3. Verify backend is responding: http://localhost:8000/health
4. Check if models endpoint works: http://localhost:8000/api/chat/ui/models

## API Endpoints You Can Test

### Get Available Models
```bash
curl http://localhost:8000/api/chat/ui/models
```

### Get Routing Profiles
```bash
curl http://localhost:8000/api/chat/ui/profiles
```

### Send a Test Message
```bash
curl -X POST http://localhost:8000/api/chat/ui/send \
  -H "Content-Type: application/json" \
  -D '{
    "message": "Hello, how are you?",
    "model_id": "llama3",
    "routing_profile": "direct_llm",
    "use_memory": false
  }'
```

### List Conversations
```bash
curl http://localhost:8000/api/chat/ui/conversations
```

## Features to Test

### Basic Chat
- [x] Create new conversation
- [x] Send message
- [x] Receive response
- [x] View message history

### Routing Profiles
- [x] Direct LLM - Direct connection to Ollama
- [ ] Zain Agent - Requires agent configuration
- [ ] Tools + Data - Requires tools configuration

### Settings
- [x] Model selection
- [x] Memory toggle (on/off)
- [x] Tools toggle (on/off)

### Conversation Management
- [x] Create conversation
- [x] List conversations
- [x] Switch between conversations
- [x] Delete conversation

## Next Steps

1. **Test Basic Chat**: Send a few messages and verify responses
2. **Test Memory**: Enable memory toggle and verify context is maintained
3. **Test Multiple Conversations**: Create multiple chats and switch between them
4. **Configure Tools**: If you want to use the "Tools + Data" profile
5. **Configure Agent**: If you want to use the "Zain Agent" profile

## Configuration Files

- **Backend Config**: `backend/orchestrator/.env`
- **Frontend**: Uses backend API, no config needed
- **Tools Config**: `backend/orchestrator/config/tools.json` (optional)
- **Agents Config**: `backend/orchestrator/config/agents.json` (optional)

## Support

If you encounter any issues:
1. Check the backend terminal for error messages
2. Check the frontend terminal for build errors
3. Check browser console (F12) for JavaScript errors
4. Verify Ollama is running and llama3 is available

## Success Indicators

✅ Backend starts without errors
✅ Frontend builds and opens browser
✅ Chat Studio appears in sidebar
✅ Models dropdown shows "llama3"
✅ Can send message and receive response
✅ Conversations are saved and can be reopened

Enjoy your new Chat Studio! 🎉
