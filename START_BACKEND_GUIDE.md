# How to Start the Backend Server

## The Issue
The "Error: Not Found" message appears because the backend server is not running. The frontend is trying to connect to `http://localhost:8000` but nothing is listening on that port.

## Solution: Start the Backend

### Option 1: Using Python directly (Recommended)

1. **Open a terminal/command prompt**

2. **Navigate to the backend directory:**
```bash
cd backend/orchestrator
```

3. **Install dependencies (if not already done):**
```bash
pip install -r requirements.txt
```

4. **Start the server:**
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. **Verify it's running:**
   - Open your browser and go to: `http://localhost:8000/docs`
   - You should see the FastAPI documentation page

### Option 2: Using the start script

**Windows:**
```bash
start-backend.bat
```

**Linux/Mac:**
```bash
./start-backend.sh
```

## Verify Backend is Running

Once started, you should see output like:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## Test the Backend

Open these URLs in your browser to verify:

1. **API Documentation:** http://localhost:8000/docs
2. **Health Check:** http://localhost:8000/health
3. **Tools API:** http://localhost:8000/api/tools
4. **Datasources API:** http://localhost:8000/api/datasources

## Common Issues

### Issue: "Module not found"
**Solution:** Install dependencies
```bash
cd backend/orchestrator
pip install -r requirements.txt
```

### Issue: "Port 8000 already in use"
**Solution:** Kill the process using port 8000 or use a different port
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

### Issue: "Cannot find module 'app'"
**Solution:** Make sure you're in the correct directory
```bash
cd backend/orchestrator
python -m uvicorn app.main:app --reload --port 8000
```

## After Backend is Running

1. Keep the backend terminal open (don't close it)
2. Open a NEW terminal for the frontend
3. Start the frontend:
   ```bash
   cd frontend
   npm start
   ```
4. Open http://localhost:3000 in your browser
5. Navigate to "Tools & Data Sources"
6. Try adding a tool - it should work now!

## Quick Start Command (All-in-One)

If you want to start both backend and frontend together:

**Windows:**
```bash
start-all.bat
```

**Linux/Mac:**
```bash
./start-all.sh
```

This will start both servers in separate terminal windows.
