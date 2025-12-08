# Troubleshooting: Empty Pages Issue

## Problem
File Explorer and Topology pages appear empty in the GUI.

## Root Cause
The backend API server is not running or not accessible from the frontend.

## Solution

### Step 1: Start the Backend Server

Open a terminal and run:

```bash
cd backend/orchestrator
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or use the provided batch file:
```bash
start-backend.bat
```

### Step 2: Verify Backend is Running

Open browser and go to:
- http://localhost:8000/health
- http://localhost:8000/docs

You should see:
- Health endpoint returns JSON with status
- Docs page shows Swagger UI

### Step 3: Check Frontend Connection

The frontend is trying to connect to:
- `http://localhost:8000/api/topology/graph`
- `http://localhost:8000/api/files/*`

If backend is running, these should return data.

### Step 4: Check Browser Console

1. Open browser DevTools (F12)
2. Go to Console tab
3. Look for errors like:
   - "Failed to fetch"
   - "Network error"
   - "CORS error"

### Step 5: Fix CORS if Needed

If you see CORS errors, the backend is already configured to allow `http://localhost:3000`.

Check `backend/orchestrator/.env`:
```
CORS_ORIGINS=http://localhost:3000
```

## Quick Fix Commands

### Windows:

```batch
REM Terminal 1 - Start Backend
cd backend\orchestrator
python -m uvicorn app.main:app --reload --port 8000

REM Terminal 2 - Start Frontend  
cd frontend
npm start
```

### Verify Both Running:
- Backend: http://localhost:8000/docs
- Frontend: http://localhost:3000

## Expected Behavior After Fix

### File Explorer:
- Should show directory tree
- Files and folders visible
- Can navigate and view files

### Topology:
- Should show 9 workflow nodes
- Nodes displayed vertically
- Start Flow button functional
- Component test buttons visible

## If Still Empty

### Check Backend Logs:

Look for errors in backend terminal:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Check Frontend Logs:

Look in browser console for:
```
Error fetching graph: ...
Error fetching files: ...
```

### Test API Directly:

```bash
# Test topology endpoint
curl http://localhost:8000/api/topology/graph

# Should return JSON with nodes and edges
```

## Common Issues

### Issue 1: Port Already in Use
```
Error: Address already in use
```
**Solution:** Kill process on port 8000 or use different port

### Issue 2: Module Not Found
```
ModuleNotFoundError: No module named 'fastapi'
```
**Solution:** Install dependencies
```bash
cd backend/orchestrator
pip install -r requirements.txt
```

### Issue 3: Frontend Can't Connect
```
Failed to fetch
```
**Solution:** 
1. Verify backend is running
2. Check CORS settings
3. Verify port 8000 is accessible

## Verification Checklist

- [ ] Backend running on port 8000
- [ ] Frontend running on port 3000
- [ ] http://localhost:8000/health returns JSON
- [ ] http://localhost:8000/docs shows Swagger UI
- [ ] Browser console shows no errors
- [ ] File Explorer shows files
- [ ] Topology shows workflow nodes

## Success Indicators

When everything is working:

**File Explorer:**
- ✅ Directory tree visible
- ✅ Files listed
- ✅ Can click and view files

**Topology:**
- ✅ 9 workflow nodes displayed
- ✅ Colored cards for each node
- ✅ Arrows between nodes
- ✅ Start Flow button works
- ✅ Test icons on each node

**Backend Terminal:**
```
INFO:     127.0.0.1:xxxxx - "GET /api/topology/graph HTTP/1.1" 200 OK
INFO:     127.0.0.1:xxxxx - "GET /api/files/list HTTP/1.1" 200 OK
```

## Need Help?

1. Check both terminals are running
2. Verify no error messages
3. Test API endpoints directly with curl
4. Check browser console for errors
5. Restart both backend and frontend
