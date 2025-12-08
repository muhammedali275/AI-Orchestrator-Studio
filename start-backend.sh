#!/bin/bash
echo "Starting ZainOne Orchestrator Studio Backend..."
cd backend
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
