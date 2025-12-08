# ZainOne Orchestrator Studio - Linux Setup Guide

This guide provides instructions for setting up and running the ZainOne Orchestrator Studio on Linux systems.

## Prerequisites

Ensure you have the following installed on your Linux system:

1. **Python 3.x**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-venv
   ```

2. **Node.js and npm**
   ```bash
   sudo apt install nodejs npm
   # Or use nvm (Node Version Manager) for better version control
   ```

## Setup Instructions

1. **Clone or download the repository**

2. **Make the shell scripts executable**
   ```bash
   chmod +x *.sh
   ```

3. **Install backend dependencies**
   ```bash
   cd backend
   python3 -m pip install -r requirements.txt
   cd ..
   ```

4. **Install frontend dependencies**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

## Running the Application

### Option 1: Using the Management Script (Recommended)

The `manage.sh` script provides a unified interface to control all aspects of the application:

```bash
# Start both backend and frontend servers
./manage.sh start

# Start only the backend server
./manage.sh start-back

# Start only the frontend server
./manage.sh start-front

# Stop all running servers
./manage.sh stop

# Restart all servers
./manage.sh restart

# Show the status of all servers
./manage.sh status

# Show help information
./manage.sh help
```

### Option 2: Using Individual Scripts

You can also use the individual scripts for specific operations:

#### Starting the Application

You have two options for starting both services:

```bash
./start-all.sh
```
or
```bash
./start-all-universal.sh
```

The universal script will automatically detect your terminal emulator and use the appropriate command. It supports:
- GNOME Terminal
- Konsole (KDE)
- XFCE Terminal
- Generic x-terminal-emulator
- Fallback to background processes if no terminal is detected

Both scripts will:
- Start the backend server on http://localhost:8000
- Start the frontend development server on http://localhost:3000
- Open new terminal windows for each service (if a supported terminal is available)

#### Starting Components Separately

Start the backend:
```bash
./start-backend.sh
```

Start the frontend (in a separate terminal):
```bash
./start-frontend.sh
```

#### Stopping the Application

Stop all running services:
```bash
./stop-all.sh
```

#### Restarting the Application

Restart all services:
```bash
./restart.sh
```

#### Checking Application Status

Check the status of all services:
```bash
./status.sh
```

## Accessing the Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Troubleshooting

### Terminal Issues
If you encounter issues with the terminal commands:

1. Try using the `start-all-universal.sh` script which automatically detects your terminal emulator.

2. If you still have issues, you can modify the scripts based on your Linux distribution and terminal emulator:

   - For KDE/Plasma users (Konsole):
     ```bash
     konsole --new-tab -e "cd backend && python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
     ```

   - For XFCE users (xfce4-terminal):
     ```bash
     xfce4-terminal -e "cd backend && python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
     ```

   - For a more universal approach, you can use `x-terminal-emulator`:
     ```bash
     x-terminal-emulator -e "cd backend && python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
     ```

3. As a last resort, you can run the services in the background:
   ```bash
   cd backend && python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
   cd frontend && npm start &
   ```

### Python Version
If you encounter issues with Python dependencies, ensure you're using Python 3.8 or newer:
```bash
python3 --version
```

### Node.js Version
If you encounter issues with the frontend, check your Node.js version:
```bash
node --version
npm --version
```
The application has been tested with Node.js 14.x and newer.
