#!/bin/bash

echo "==================================="
echo "Chat Studio Fix Script"
echo "==================================="
echo ""
echo "This script will fix the Chat Studio API endpoints by ensuring"
echo "database tables are created and default data is seeded."
echo ""
echo "Press Enter to continue or Ctrl+C to cancel..."
read

cd backend/orchestrator
python fix_chat_studio.py

if [ $? -eq 0 ]; then
    echo ""
    echo "==================================="
    echo "Fix completed successfully!"
    echo "==================================="
    echo ""
    echo "Now restart the backend server:"
    echo ""
    echo "  ./restart.sh   (Linux/Mac)"
    echo "  ./restart.bat  (Windows)"
    echo ""
else
    echo ""
    echo "==================================="
    echo "Fix failed!"
    echo "==================================="
    echo ""
    echo "Please check the error messages above."
    echo ""
fi

echo "Press Enter to exit..."
read
