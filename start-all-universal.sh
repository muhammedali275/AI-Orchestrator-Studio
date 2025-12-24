#!/bin/bash
echo "========================================"
echo "AI Orchestrator Studio"
echo "========================================"
echo ""

# Detect primary server IP for display (fallback to localhost)
SERVER_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
if [ -z "$SERVER_IP" ]; then
    SERVER_IP="localhost"
fi

echo "Starting Backend Server..."

# Try to detect the terminal emulator
if command -v gnome-terminal &> /dev/null; then
    gnome-terminal -- bash -c "cd backend && python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000; exec bash"
elif command -v konsole &> /dev/null; then
    konsole --new-tab -e "cd backend && python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
elif command -v xfce4-terminal &> /dev/null; then
    xfce4-terminal -e "cd backend && python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
elif command -v x-terminal-emulator &> /dev/null; then
    x-terminal-emulator -e "cd backend && python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
else
    echo "Could not detect terminal emulator. Starting backend in background..."
    cd backend && python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
    cd ..
fi

echo ""
echo "Waiting 3 seconds for backend to initialize..."
sleep 3
echo ""
echo "Starting Frontend Development Server..."

# Try to detect the terminal emulator for frontend
if command -v gnome-terminal &> /dev/null; then
    gnome-terminal -- bash -c "cd frontend && npm start; exec bash"
elif command -v konsole &> /dev/null; then
    konsole --new-tab -e "cd frontend && npm start"
elif command -v xfce4-terminal &> /dev/null; then
    xfce4-terminal -e "cd frontend && npm start"
elif command -v x-terminal-emulator &> /dev/null; then
    x-terminal-emulator -e "cd frontend && npm start"
else
    echo "Could not detect terminal emulator. Starting frontend in background..."
    cd frontend && npm start &
    cd ..
fi

echo ""
echo "========================================"
echo "Both servers are starting!"
echo "Backend: http://$SERVER_IP:8000"
echo "Frontend: http://$SERVER_IP:3000"
echo "API Docs: http://$SERVER_IP:8000/docs"
echo "========================================"
