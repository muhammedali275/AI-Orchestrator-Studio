# Restart Instructions to Apply Changes

## Quick Restart Commands

### Windows:

```batch
# Stop all services
taskkill /F /IM node.exe
taskkill /F /IM python.exe

# Start backend (port 8000)
cd backend\orchestrator
start cmd /k "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

# Start chat studio (port 8001)
start cmd /k "python chat_ui_server.py"

# Start frontend (port 3000)
cd ..\..\frontend
start cmd /k "npm start"
```

### Linux/Mac:

```bash
# Stop all services
./stop-all.sh

# Start all services
./start-all.sh

# Or start individually:
./start-backend.sh    # Port 8000
./start-chat-studio.sh # Port 8001
./start-frontend.sh    # Port 3000
```

## What to Expect After Restart:

### 1. LLM Connections Page
- When you enter `http://localhost:11434`, the API key field will show as optional
- Help text will say "API key not required for local LLMs like Ollama"
- You can save without entering an API key

### 2. Tools & Data Sources Page
- You'll see a new explanation section at the top
- Clear distinction between Tools (actions) and Data Sources (read-only data)

### 3. Credentials & Security Page
- New credential types available: HTTPS Certificate, IP Allowlist, Authentication Token
- Explanation section showing which credentials are required vs optional

### 4. Internal Chat (Chat Studio)
- Click the refresh button (🔄) next to the Model dropdown
- Your Ollama models (like llama3) should now appear
- No more fake GPT-3.5, GPT-4 models if they're not configured

## Verification Steps:

1. **Check Backend is Running:**
   ```bash
   curl http://localhost:8000/health
   ```
   Should return: `{"status": "healthy", ...}`

2. **Check Chat Studio is Running:**
   ```bash
   curl http://localhost:8001/api/chat/ui/models
   ```
   Should return your configured models

3. **Check Frontend is Running:**
   - Open browser to `http://localhost:3000`
   - Should see the ZainOne Orchestrator Studio UI

## Troubleshooting:

### If models still don't appear:
1. Check browser console (F12) for errors
2. Look for log message: `[ChatStudio] Models response: {...}`
3. Verify backend has LLM configured:
   ```bash
   curl http://localhost:8000/api/llm/config
   ```

### If Orchestration Flow is still empty:
- This is normal - you need to create a flow
- See `HOW_TO_CONFIGURE_SYSTEM.md` for flow configuration examples
- The flow connects your LLM, Data Sources, and Tools together

### If Data Sources relationship is unclear:
- Read `HOW_TO_CONFIGURE_SYSTEM.md` section "How Components Work Together"
- See the visual diagrams and real-world examples
- Data Sources provide context (RAG) to the LLM
- Tools allow the LLM to take actions

## After Restart Checklist:

- [ ] Backend running on port 8000
- [ ] Chat Studio running on port 8001
- [ ] Frontend running on port 3000
- [ ] LLM Connections page loads without errors
- [ ] Can add local LLM without API key
- [ ] Tools & Data Sources shows explanation section
- [ ] Credentials page shows new credential types
- [ ] Chat Studio shows configured models (click refresh if needed)
