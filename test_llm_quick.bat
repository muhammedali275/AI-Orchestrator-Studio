@echo off
REM Quick LLM Connection Test for Windows
REM Tests if Ollama is running and accessible

echo ========================================
echo Quick LLM Connection Test
echo ========================================
echo.

REM Test 1: Check if Ollama is running
echo [1/3] Testing Ollama server...
curl -s http://localhost:11434/api/version
if %ERRORLEVEL% EQU 0 (
    echo [OK] Ollama server is running
) else (
    echo [FAIL] Ollama server is not accessible
    echo Please start Ollama first
    pause
    exit /b 1
)
echo.

REM Test 2: List available models
echo [2/3] Listing available models...
curl -s http://localhost:11434/api/tags
echo.

REM Test 3: Test simple completion
echo [3/3] Testing chat completion...
curl -s -X POST http://localhost:11434/api/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"model\":\"llama3:8b\",\"messages\":[{\"role\":\"user\",\"content\":\"Say 'test successful'\"}],\"stream\":false}"
echo.

echo ========================================
echo Test Complete!
echo ========================================
echo.
echo If all tests passed, your LLM is ready for production.
echo Run 'python test_llm_production.py http://localhost:11434 llama3:8b' for detailed tests.
echo.
pause
