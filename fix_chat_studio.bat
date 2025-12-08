@echo off
echo ===================================
echo Chat Studio Fix Script
echo ===================================
echo.
echo This script will fix the Chat Studio API endpoints by ensuring
echo database tables are created and default data is seeded.
echo.
echo Press any key to continue or Ctrl+C to cancel...
pause > nul

cd backend\orchestrator
python fix_chat_studio.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ===================================
    echo Fix completed successfully!
    echo ===================================
    echo.
    echo Now restart the backend server:
    echo.
    echo   .\restart.sh   (Linux/Mac)
    echo   .\restart.bat  (Windows)
    echo.
) else (
    echo.
    echo ===================================
    echo Fix failed!
    echo ===================================
    echo.
    echo Please check the error messages above.
    echo.
)

pause
