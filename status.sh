#!/bin/bash
echo "========================================"
echo "ZainOne Orchestrator Studio Status"
echo "========================================"
echo ""

# Check backend status
echo "Backend Server (Port 8000):"
BACKEND_PID=$(lsof -t -i:8000 2>/dev/null)
if [ -n "$BACKEND_PID" ]; then
    echo "  Status: RUNNING"
    echo "  PID: $BACKEND_PID"
    echo "  Process: $(ps -p $BACKEND_PID -o comm=)"
    echo "  Uptime: $(ps -p $BACKEND_PID -o etime=)"
else
    echo "  Status: STOPPED"
fi

# Check frontend status
echo ""
echo "Frontend Server (Port 3000):"
FRONTEND_PID=$(lsof -t -i:3000 2>/dev/null)
if [ -n "$FRONTEND_PID" ]; then
    echo "  Status: RUNNING"
    echo "  PID: $FRONTEND_PID"
    echo "  Process: $(ps -p $FRONTEND_PID -o comm=)"
    echo "  Uptime: $(ps -p $FRONTEND_PID -o etime=)"
else
    echo "  Status: STOPPED"
fi

echo ""
echo "========================================"
echo "Access URLs:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "========================================"
