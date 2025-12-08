@echo off
echo ===================================
echo Chat Studio Server
echo ===================================
echo.
echo This script will start the Chat Studio API server on port 8001.
echo.
echo Press any key to continue or Ctrl+C to cancel...
pause > nul

cd backend\orchestrator
python chat_ui_server.py

pause
