# Testing Guide - Critical & Moderate Fixes

## Quick Start: Test All Fixes

### 1. Start Backend & Frontend
```bash
# Terminal 1: Backend
cd backend/orchestrator
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend
npm start
# or
yarn dev
```

### 2. Open Browser
```
http://localhost:3000
```

---

## TEST 1: Timeout Misalignment Fix ✅

**Objective**: Verify frontend reads timeout from backend

### Steps:

1. **Open Browser Console** (F12 → Console tab)

2. **Watch for Config Loading**:
   - Look for message: `[ChatStudio] Loaded config - timeout: [number] ms`
   - If you see this, timeout is being read from backend ✓

3. **Verify Timeout Value**:
   - Open `backend/orchestrator/.env`
   - Check `LLM_TIMEOUT_SECONDS=120` (or whatever value)
   - In console, verify timeout_ms = timeout_seconds * 1000
   - Example: 120s → 120000ms (plus 5000ms buffer = 125000ms frontend timeout)

4. **Test API Endpoint Directly**:
   ```bash
   curl http://localhost:8000/api/config/timeout
   # Should return:
   # {
   #   "llm_timeout_ms": 120000,
   #   "llm_timeout_seconds": 120,
   #   "frontend_timeout_ms": 125000
   # }
   ```

5. **Simulate Timeout Change**:
   - Edit `.env`: change `LLM_TIMEOUT_SECONDS=60`
   - Restart backend
   - Refresh frontend (F5)
   - Console should show: `[ChatStudio] Loaded config - timeout: 65000 ms`
   - ✓ Timeout dynamically updated

**✅ PASS**: Frontend reads dynamic timeout from backend
**❌ FAIL**: Console shows hardcoded 120000 (not loading from backend)

---

## TEST 2: Error Response Standardization ✅

**Objective**: Verify error responses include error codes and suggestions

### Steps:

1. **Generate Invalid Conversation Error**:
   - Open DevTools (F12 → Network tab)
   - Open Chat Studio
   - Manually construct request that fails
   ```bash
   curl -X GET http://localhost:8000/api/chat/ui/conversations/invalid-id-xyz
   ```

2. **Check Response Format**:
   - Should see JSON with:
     - `"success": false`
     - `"error_code": "CONVERSATION_NOT_FOUND"`
     - `"message": "Conversation 'invalid-id-xyz' not found"`
     - `"suggestions": [...]` (list of actions)
   ```json
   {
     "success": false,
     "error_code": "CONVERSATION_NOT_FOUND",
     "message": "Conversation 'invalid-id-xyz' not found",
     "detail": "Conversation may have been deleted",
     "suggestions": [
       "Create a new conversation",
       "Reload conversation list",
       "Check if conversation ID is correct"
     ]
   }
   ```

3. **Test Multiple Error Cases**:
   ```bash
   # Missing LLM config
   curl http://localhost:8000/api/llm/config  
   # Should have error_code field

   # Invalid routing profile (after implementing fix #4)
   curl -X POST http://localhost:8000/api/chat/ui/send \
     -H "Content-Type: application/json" \
     -d '{"message": "test", "routing_profile": "invalid_profile"}'
   # Should return error_code: INVALID_ROUTING_PROFILE
   ```

**✅ PASS**: All error responses include error_code enum
**❌ FAIL**: Error responses don't have error_code or suggestions fields

---

## TEST 3: LLM Config Cache ✅

**Objective**: Verify config changes persist and frontend picks them up

### Steps:

1. **Start with Valid LLM Config**:
   - Backend should have `LLM_BASE_URL` in `.env`
   - Frontend should load models successfully

2. **Open Settings > LLM Configuration** (implement this UI or use API):
   ```bash
   # Test API endpoint
   curl http://localhost:8000/api/llm/config
   # Shows current config
   ```

3. **Update LLM Config** (test PUT endpoint):
   ```bash
   curl -X PUT http://localhost:8000/api/llm/config \
     -H "Content-Type: application/json" \
     -d '{
       "base_url": "http://10.99.70.200:4000",
       "default_model": "llama4-scout",
       "timeout_seconds": 120
     }'
   # Should return: {"success": true, "config": {...}}
   ```

4. **Verify Config Persists**:
   - Check `.env` file: `LLM_BASE_URL=http://10.99.70.200:4000` ✓
   - Restart backend
   - Check if config still there: `curl http://localhost:8000/api/llm/config`
   - Should show same values ✓

5. **Verify Frontend Reloads**:
   - After updating config, frontend should immediately reload models
   - Manually call: `curl http://localhost:8000/api/chat/ui/models`
   - Should show models from new server

**✅ PASS**: Config written to .env and survives restart
**❌ FAIL**: Config lost after restart or not written to .env

---

## TEST 4: Soft Delete Filtering ✅

**Objective**: Verify deleted conversations don't appear in lists or messages

### Steps:

1. **Create Test Conversation**:
   ```bash
   curl -X POST http://localhost:8000/api/chat/ui/conversations \
     -H "Content-Type: application/json" \
     -d '{"title": "Test Conversation", "model_id": "test"}'
   # Note: response.id = "conv-id-123"
   ```

2. **Add Messages to Conversation**:
   ```bash
   curl -X POST http://localhost:8000/api/chat/ui/send \
     -H "Content-Type: application/json" \
     -d '{
       "conversation_id": "conv-id-123",
       "message": "Test message"
     }'
   # Should see both user and assistant messages
   ```

3. **Get Conversation with Messages**:
   ```bash
   curl http://localhost:8000/api/chat/ui/conversations/conv-id-123
   # Should return messages list
   ```

4. **Delete Conversation**:
   ```bash
   curl -X DELETE http://localhost:8000/api/chat/ui/conversations/conv-id-123
   # Sets is_deleted=True
   ```

5. **Verify Deletion**:
   ```bash
   # Get single conversation (should 404)
   curl http://localhost:8000/api/chat/ui/conversations/conv-id-123
   # Should return 404: "Conversation not found"

   # List conversations (deleted should not appear)
   curl http://localhost:8000/api/chat/ui/conversations
   # Response should NOT include conv-id-123
   ```

**✅ PASS**: Deleted conversations don't appear in lists or get calls
**❌ FAIL**: Deleted conversations still show in lists or messages

---

## TEST 5: Error Messages in UI ✅

**Objective**: Verify frontend shows helpful error messages

### Steps:

1. **Stop LLM Server** (simulate offline):
   - Stop Ollama or external LLM
   - Refresh Chat Studio
   - Should see error message with suggestions
   - Error should say: "Connection to LLM server timed out" or similar
   - Should suggest checking LLM server status

2. **Try with Wrong LLM URL**:
   - Edit `.env`: `LLM_BASE_URL=http://invalid-host:9999`
   - Restart backend
   - Try to load models
   - Should see helpful error, not raw exception

3. **Try Sending Message with Timeout**:
   - Slow down network (DevTools → Slow 3G)
   - Or set timeout very low temporarily
   - Send message to external LLM
   - Should show timeout error with suggestions
   - Message should include timeout duration from backend

**✅ PASS**: Errors include error_code, message, and suggestions
**❌ FAIL**: Generic error messages without codes or suggestions

---

## MANUAL TEST SCENARIOS

### Scenario A: Fresh Install
```
1. Start backend (fresh .env)
2. Start frontend
3. See error: "LLM not configured"
4. Error should have suggestions: "Go to Settings > LLM Configuration"
5. Update config via API
6. Reload frontend
7. Models now load ✓
```

### Scenario B: Config Change
```
1. Change LLM_TIMEOUT_SECONDS in .env
2. Restart backend
3. Refresh frontend
4. Frontend timeout should match backend immediately ✓
```

### Scenario C: Conversation Management
```
1. Create conversation A
2. Create conversation B
3. Delete conversation A
4. List conversations - only B should appear ✓
5. Send message to B - should work ✓
```

### Scenario D: Error Handling
```
1. Stop external LLM
2. Try to send message
3. Should timeout after [timeout]s
4. Error should show configured timeout value ✓
5. Suggestions should be helpful ✓
```

---

## CURL COMMANDS FOR TESTING

```bash
# Test frontend config endpoint
curl http://localhost:8000/api/config/frontend | jq

# Test timeout config
curl http://localhost:8000/api/config/timeout | jq

# Test system status
curl http://localhost:8000/api/config/status | jq

# Test error response (invalid conversation)
curl http://localhost:8000/api/chat/ui/conversations/invalid | jq

# Test LLM config
curl http://localhost:8000/api/llm/config | jq

# List all conversations
curl http://localhost:8000/api/chat/ui/conversations | jq

# List models
curl http://localhost:8000/api/chat/ui/models | jq
```

---

## BROWSER CONSOLE CHECKS

```javascript
// Check if config loaded
// Should see in console:
// [ChatStudio] Loaded config - timeout: [number] ms

// Check requestTimeout state
// Open React DevTools and inspect ChatStudio component
// requestTimeout should be > 0 and match backend value

// Check for errors
// Watch Network tab when loading models
// Responses should have error_code field if error
```

---

## CHECKLIST

- [ ] Frontend loads config on startup (console message visible)
- [ ] Timeout value from backend displayed in error messages
- [ ] Error responses include error_code enum
- [ ] Error responses include suggestions array
- [ ] Config changes persist in .env file
- [ ] Soft deleted conversations don't appear in lists
- [ ] Invalid conversation returns 404 with proper error
- [ ] Models load with correct timeout
- [ ] Chat messages sent with correct timeout

---

## DEBUGGING TIPS

1. **Check console logs**:
   - Frontend: Open DevTools Console (F12)
   - Backend: Watch terminal output

2. **Check network requests**:
   - DevTools → Network tab
   - Filter by XHR for API calls
   - Check response bodies for error_code

3. **Check .env file**:
   - `cat backend/orchestrator/.env | grep LLM_`
   - Verify values match what you expect

4. **Check database**:
   - SQLite: `sqlite3 backend/orchestrator/orchestrator.db`
   - Query: `SELECT id, is_deleted FROM conversations LIMIT 10;`
   - Verify deleted ones have is_deleted=1

5. **Restart everything**:
   ```bash
   # Kill all Python/Node processes
   pkill -f python
   pkill -f node
   
   # Start fresh
   cd backend/orchestrator && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
   cd frontend && npm start
   ```
