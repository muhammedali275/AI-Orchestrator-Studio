#!/bin/bash

# ZainOne Orchestrator Studio Management Script
# This script provides a unified interface to manage the application

# Display help information
show_help() {
    echo "ZainOne Orchestrator Studio Management Script"
    echo ""
    echo "Usage: ./manage.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start       Start both backend and frontend servers"
    echo "  start-back  Start only the backend server"
    echo "  start-front Start only the frontend server"
    echo "  stop        Stop all running servers"
    echo "  restart     Restart all servers"
    echo "  status      Show the status of all servers"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./manage.sh start      # Start both servers"
    echo "  ./manage.sh stop       # Stop all servers"
    echo "  ./manage.sh restart    # Restart all servers"
    echo "  ./manage.sh status     # Show server status"
}

# Check if lsof is installed
check_dependencies() {
    if ! command -v lsof &> /dev/null; then
        echo "Warning: 'lsof' command not found. Some features may not work correctly."
        echo "You can install it using: sudo apt install lsof"
        echo ""
    fi
}

# Start the backend server
start_backend() {
    echo "Starting Backend Server..."
    
    # Check if backend is already running
    if lsof -i:8000 &> /dev/null; then
        echo "Backend server is already running on port 8000."
        return
    fi
    
    cd backend
    python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
    cd ..
    
    echo "Backend server started on http://localhost:8000"
}

# Start the frontend server
start_frontend() {
    echo "Starting Frontend Server..."
    
    # Check if frontend is already running
    if lsof -i:3000 &> /dev/null; then
        echo "Frontend server is already running on port 3000."
        return
    fi
    
    cd frontend
    npm start &
    cd ..
    
    echo "Frontend server started on http://localhost:3000"
}

# Start both servers
start_all() {
    echo "========================================"
    echo "Starting ZainOne Orchestrator Studio"
    echo "========================================"
    echo ""
    
    start_backend
    
    echo ""
    echo "Waiting 3 seconds for backend to initialize..."
    sleep 3
    echo ""
    
    start_frontend
    
    echo ""
    echo "========================================"
    echo "Both servers are starting!"
    echo "Backend: http://localhost:8000"
    echo "Frontend: http://localhost:3000"
    echo "API Docs: http://localhost:8000/docs"
    echo "========================================"
}

# Stop all servers
stop_all() {
    echo "========================================"
    echo "Stopping ZainOne Orchestrator Studio"
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
}

# Restart all servers
restart_all() {
    echo "========================================"
    echo "Restarting ZainOne Orchestrator Studio"
    echo "========================================"
    echo ""
    
    stop_all
    echo ""
    echo "Waiting 3 seconds before starting services again..."
    sleep 3
    echo ""
    start_all
}

# Show status of all servers
show_status() {
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
}

# Check dependencies
check_dependencies

# Process command line arguments
case "$1" in
    start)
        start_all
        ;;
    start-back)
        start_backend
        ;;
    start-front)
        start_frontend
        ;;
    stop)
        stop_all
        ;;
    restart)
        restart_all
        ;;
    status)
        show_status
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac

exit 0
