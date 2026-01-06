#!/bin/bash
echo "========================================"
echo "Stopping exampleOne Orchestrator Studio"
echo "========================================"
echo ""

# Find and kill backend process
echo "Stopping Backend Server..."
BACKEND_PID=$(lsof -t -i:8000 2>/dev/null)
if [ -n "$BACKEND_PID" ]; then
    echo "Killing backend process with PID: $BACKEND_PID"
    kill -15 $BACKEND_PID 2>/dev/null || kill -9 $BACKEND_PID 2>/dev/null
    echo "Backend server stopped."
else
    echo "No backend server running on port 8000."
fi

# Find and kill frontend process
echo ""
echo "Stopping Frontend Server..."
FRONTEND_PID=$(lsof -t -i:3000 2>/dev/null)
if [ -n "$FRONTEND_PID" ]; then
    echo "Killing frontend process with PID: $FRONTEND_PID"
    kill -15 $FRONTEND_PID 2>/dev/null || kill -9 $FRONTEND_PID 2>/dev/null
    echo "Frontend server stopped."
else
    echo "No frontend server running on port 3000."
fi

echo ""
echo "========================================"
echo "All services stopped."
echo "========================================"
