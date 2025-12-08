@echo off
echo Starting ZainOne Orchestrator Studio Backend...
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
