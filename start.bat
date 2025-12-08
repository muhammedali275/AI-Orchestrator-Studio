@echo off
echo Starting AIpanel...

REM Create virtual environment if it doesn't exist
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Initialize database
echo Initializing database...
python -m app.db.session

REM Start server
echo Starting server...
python -m app.main

REM Deactivate virtual environment on exit
deactivate
