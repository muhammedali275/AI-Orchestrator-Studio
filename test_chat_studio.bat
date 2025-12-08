@echo off
REM Chat Studio Test Script for Windows
REM Tests all Chat Studio endpoints

echo ===================================
echo Chat Studio API Test Suite
echo ===================================
echo.

set BASE_URL=http://localhost:8000
set PASSED=0
set FAILED=0

echo 1. Backend Health Check
echo ----------------------
curl -s %BASE_URL%/health
if %ERRORLEVEL% EQU 0 (
    echo [PASSED] Health endpoint
    set /a PASSED+=1
) else (
    echo [FAILED] Health endpoint
    set /a FAILED+=1
)
echo.

echo 2. Model Detection (Ollama)
echo ---------------------------
curl -s %BASE_URL%/api/chat/ui/models
if %ERRORLEVEL% EQU 0 (
    echo [PASSED] Get available models
    set /a PASSED+=1
) else (
    echo [FAILED] Get available models
    set /a FAILED+=1
)
echo.

echo 3. Routing Profiles
echo -------------------
curl -s %BASE_URL%/api/chat/ui/profiles
if %ERRORLEVEL% EQU 0 (
    echo [PASSED] Get routing profiles
    set /a PASSED+=1
) else (
    echo [FAILED] Get routing profiles
    set /a FAILED+=1
)
echo.

echo 4. Conversation Management
echo --------------------------
curl -s -X POST %BASE_URL%/api/chat/ui/conversations -H "Content-Type: application/json" -d "{\"title\":\"Test Conversation\",\"model_id\":\"llama3:8b\",\"routing_profile\":\"direct_llm\"}"
if %ERRORLEVEL% EQU 0 (
    echo [PASSED] Create new conversation
    set /a PASSED+=1
) else (
    echo [FAILED] Create new conversation
    set /a FAILED+=1
)

curl -s %BASE_URL%/api/chat/ui/conversations
if %ERRORLEVEL% EQU 0 (
    echo [PASSED] List conversations
    set /a PASSED+=1
) else (
    echo [FAILED] List conversations
    set /a FAILED+=1
)
echo.

echo 5. Chat Functionality
echo ---------------------
curl -s -X POST %BASE_URL%/api/chat/ui/send -H "Content-Type: application/json" -d "{\"message\":\"Hello, this is a test\",\"model_id\":\"llama3:8b\",\"routing_profile\":\"direct_llm\",\"use_memory\":false}"
if %ERRORLEVEL% EQU 0 (
    echo [PASSED] Send chat message
    set /a PASSED+=1
) else (
    echo [FAILED] Send chat message
    set /a FAILED+=1
)
echo.

echo 6. Prompt Profiles
echo ------------------
curl -s %BASE_URL%/api/chat/ui/prompt-profiles
if %ERRORLEVEL% EQU 0 (
    echo [PASSED] Get prompt profiles
    set /a PASSED+=1
) else (
    echo [FAILED] Get prompt profiles
    set /a FAILED+=1
)
echo.

echo 7. Metrics
echo ----------
curl -s %BASE_URL%/api/chat/ui/metrics
if %ERRORLEVEL% EQU 0 (
    echo [PASSED] Get chat metrics
    set /a PASSED+=1
) else (
    echo [FAILED] Get chat metrics
    set /a FAILED+=1
)
echo.

echo ===================================
echo Test Summary
echo ===================================
echo Passed: %PASSED%
echo Failed: %FAILED%
echo.

if %FAILED% EQU 0 (
    echo All tests passed!
    exit /b 0
) else (
    echo Some tests failed!
    exit /b 1
)
