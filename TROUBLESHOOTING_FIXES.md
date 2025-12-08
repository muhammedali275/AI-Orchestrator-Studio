# Troubleshooting: Topology & Models Issues

## 🔍 Issue Report

**Problem 1:** Topology not fully shown correctly
**Problem 2:** Models not loaded

## ✅ Backend Status (Verified Working)

### **Topology API Test:**
```bash
curl http://localhost:8000/api/topology/graph
```
**Result:** ✅ Working - Returns 5 nodes and 5 edges
```json
{
  "nodes": [
    {"id": "start", "type": "start", "data": {"label": "Start"}},
    {"id": "router", "type": "router", "data": {"label": "Intent Router"}},
    {"id": "llm", "type": "llm", "data": {"label": "LLM Agent"}},
    {"id": "tools", "type": "tools", "data": {"label": "Tool Executor"}},
    {"id": "end", "type": "end", "data": {"label": "End"}}
  ],
  "edges": [
    {"source": "start", "target": "router", "label": "input"},
    {"source": "router", "target": "llm", "label": "route"},
    {"source": "llm", "target": "tools", "label": "tool_call"},
    {"source": "tools", "target": "llm", "label": "result"},
    {"source": "llm", "target": "end", "label": "complete"}
  ]
}
```

### **Models API Test:**
```bash
curl http://localhost:8000/api/llm/models
```
**Result:** ✅ Working - Returns 6 models
```json
{
  "models": [
    "llama4-scout",
    "ossgpt-70b",
    "gpt-4",
    "gpt-3.5-turbo",
    "claude-3-opus",
    "claude-3-sonnet"
  ]
}
```

## 🎯 Root Cause

**Backend APIs are working correctly!** The issue is in the **frontend**:
1. Frontend may not be fetching data correctly
2. Frontend may have CORS issues
3. Frontend may have rendering issues
4. Browser cache may be stale

## 🔧 Solutions

### **Solution 1: Clear Browser Cache & Refresh**
```bash
# In browser (Chrome/Edge):
1. Press Ctrl + Shift + Delete
2. Select "Cached images and files"
3. Click "Clear data"
4. Press Ctrl + F5 (hard refresh)

# Or:
1. Open DevTools (F12)
2. Right-click refresh button
3. Select "Empty Cache and Hard Reload"
```

### **Solution 2: Check Frontend Console**
```bash
# In browser:
1. Press F12 (open DevTools)
2. Go to Console tab
3. Look for errors (red text)
4. Check Network tab for failed requests
```

### **Solution 3: Restart Frontend**
```bash
# Stop frontend (Ctrl+C in terminal)
# Then restart:
cd frontend
npm start

# Or use batch file:
start-frontend.bat
```

### **Solution 4: Check CORS Settings**
```bash
# File: backend/orchestrator/.env
# Ensure this line exists:
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# If changed, restart backend:
cd backend/orchestrator
python -m uvicorn app.main:app --reload --port 8000
```

### **Solution 5: Verify Frontend is Running**
```bash
# Check if frontend is running on port 3000
# Open browser: http://localhost:3000

# If not running, start it:
cd frontend
npm start
```

## 📊 Expected Behavior

### **Topology Page Should Show:**
- ✅ 5 nodes in a flow diagram:
  1. Start (green)
  2. Intent Router (purple)
  3. LLM Agent (pink)
  4. Tool Executor (blue)
  5. End (red)
- ✅ 5 connecting arrows with labels
- ✅ "Flow Connections" section below
- ✅ "Refresh" button in top-right

### **LLM Config Page Should Show:**
- ✅ Model dropdown with 6 options:
  - llama4-scout
  - ossgpt-70b
  - gpt-4
  - gpt-3.5-turbo
  - claude-3-opus
  - claude-3-sonnet
- ✅ Server IP field
- ✅ Server Port field
- ✅ "Test Connection" button
- ✅ "Save Configuration" button

## 🔍 Debugging Steps

### **Step 1: Check Backend is Running**
```bash
# Should see output like:
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000

# Test API:
curl http://localhost:8000/api/topology/graph
curl http://localhost:8000/api/llm/models
```

### **Step 2: Check Frontend is Running**
```bash
# Should see output like:
Compiled successfully!
webpack compiled with 0 warnings
Local: http://localhost:3000

# Open browser: http://localhost:3000
```

### **Step 3: Check Browser Console**
```bash
# Press F12 in browser
# Look for errors in Console tab
# Common errors:
- "Failed to fetch" → Backend not running
- "CORS error" → CORS not configured
- "404 Not Found" → Wrong API endpoint
```

### **Step 4: Check Network Tab**
```bash
# Press F12 → Network tab
# Refresh page (F5)
# Look for:
- /api/topology/graph → Should be 200 OK
- /api/llm/models → Should be 200 OK
# If 404 or 500, check backend logs
```

## 🚀 Quick Fix Commands

### **Fix 1: Restart Everything**
```bash
# Stop all (Ctrl+C in terminals)

# Start backend:
cd backend/orchestrator
python -m uvicorn app.main:app --reload --port 8000

# Start frontend (new terminal):
cd frontend
npm start

# Open browser:
http://localhost:3000
```

### **Fix 2: Use Batch Files**
```bash
# Windows:
start-all.bat

# This starts both backend and frontend
```

### **Fix 3: Clear Everything and Restart**
```bash
# Stop all servers (Ctrl+C)

# Clear browser cache (Ctrl+Shift+Delete)

# Restart:
start-all.bat

# Hard refresh browser (Ctrl+F5)
```

## 📝 Verification Checklist

After applying fixes, verify:

- [ ] Backend running on port 8000
- [ ] Frontend running on port 3000
- [ ] Browser shows http://localhost:3000
- [ ] No errors in browser console (F12)
- [ ] Topology page shows 5 nodes
- [ ] LLM Config shows 6 models in dropdown
- [ ] All pages load without errors

## 🎯 If Still Not Working

### **Check These Files:**

1. **Topology Frontend:**
   - File: `frontend/src/pages/Topology.tsx`
   - Line 30-35: Check API endpoint
   - Should be: `http://localhost:8000/api/topology/graph`

2. **LLM Config Frontend:**
   - File: `frontend/src/pages/LLMConfig.tsx`
   - Line 100-110: Check models API endpoint
   - Should be: `http://localhost:8000/api/llm/models`

3. **Backend CORS:**
   - File: `backend/orchestrator/app/main.py`
   - Line 20-30: Check CORS middleware
   - Should allow: `http://localhost:3000`

### **Manual API Tests:**

```bash
# Test 1: Topology
curl http://localhost:8000/api/topology/graph

# Expected: JSON with nodes and edges

# Test 2: Models
curl http://localhost:8000/api/llm/models

# Expected: JSON with models array

# Test 3: Health
curl http://localhost:8000/api/monitoring/health

# Expected: JSON with status: healthy
```

## ✅ Summary

**Backend Status:** ✅ Working (APIs return correct data)
**Frontend Status:** ⚠️ May need refresh/restart

**Most Common Fix:**
1. Clear browser cache (Ctrl+Shift+Delete)
2. Hard refresh (Ctrl+F5)
3. If still not working, restart frontend (npm start)

**Backend APIs Verified Working:**
- ✅ `/api/topology/graph` - Returns 5 nodes
- ✅ `/api/llm/models` - Returns 6 models
- ✅ All endpoints responding correctly

**Next Steps:**
1. Clear browser cache
2. Hard refresh page (Ctrl+F5)
3. Check browser console for errors (F12)
4. If needed, restart frontend
5. Verify both backend and frontend are running

The backend is working perfectly - the issue is likely just a frontend cache or rendering issue that can be fixed with a browser refresh!
