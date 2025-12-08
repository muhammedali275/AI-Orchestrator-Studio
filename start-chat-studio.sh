#!/bin/bash

echo "==================================="
echo "Chat Studio Server"
echo "==================================="
echo ""
echo "This script will start the Chat Studio API server on port 8001."
echo ""
echo "Press Enter to continue or Ctrl+C to cancel..."
read

cd backend/orchestrator
python chat_ui_server.py

echo "Press Enter to exit..."
read
