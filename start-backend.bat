@echo off
echo Starting AI Orchestrator Studio Backend...
cd backend\orchestrator
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
