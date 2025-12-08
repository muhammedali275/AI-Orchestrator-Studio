# Test script for LLM Models Endpoint
# Tests the /api/chat/ui/models endpoint

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Testing LLM Models Endpoint" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8001"
$endpoint = "$baseUrl/api/chat/ui/models"

Write-Host "Testing endpoint: $endpoint" -ForegroundColor Yellow
Write-Host ""

# Test 1: Check if server is running
Write-Host "[Test 1] Checking if Chat Studio backend is running..." -ForegroundColor Green
try {
    $response = Invoke-WebRequest -Uri $endpoint -Method GET -UseBasicParsing -TimeoutSec 10
    Write-Host "✓ Server is running" -ForegroundColor Green
    Write-Host "  Status Code: $($response.StatusCode)" -ForegroundColor Gray
} catch {
    Write-Host "✗ Server is not running or not responding" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please start the Chat Studio backend first:" -ForegroundColor Yellow
    Write-Host "  cd backend/orchestrator" -ForegroundColor Gray
    Write-Host "  python -m uvicorn app.main:app --host 0.0.0.0 --port 8001" -ForegroundColor Gray
    exit 1
}

Write-Host ""

# Test 2: Parse and display response
Write-Host "[Test 2] Parsing response..." -ForegroundColor Green
try {
    $jsonResponse = $response.Content | ConvertFrom-Json
    
    Write-Host "✓ Response parsed successfully" -ForegroundColor Green
    Write-Host ""
    
    # Display response details
    Write-Host "Response Details:" -ForegroundColor Cyan
    Write-Host "  Success: $($jsonResponse.success)" -ForegroundColor Gray
    Write-Host "  Default Model: $($jsonResponse.default_model)" -ForegroundColor Gray
    Write-Host "  Source: $($jsonResponse.source)" -ForegroundColor Gray
    
    if ($jsonResponse.message) {
        Write-Host "  Message: $($jsonResponse.message)" -ForegroundColor Gray
    }
    
    Write-Host ""
    Write-Host "Models Found: $($jsonResponse.models.Count)" -ForegroundColor Cyan
    Write-Host ""
    
    # Display models
    if ($jsonResponse.models.Count -gt 0) {
        Write-Host "Available Models:" -ForegroundColor Yellow
        foreach ($model in $jsonResponse.models) {
            Write-Host "  - ID: $($model.id)" -ForegroundColor White
            Write-Host "    Name: $($model.name)" -ForegroundColor Gray
        }
    } else {
        Write-Host "  No models found" -ForegroundColor Red
    }
    
} catch {
    Write-Host "✗ Failed to parse response" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Raw Response:" -ForegroundColor Yellow
    Write-Host $response.Content -ForegroundColor Gray
}

Write-Host ""

# Test 3: Check Ollama status
Write-Host "[Test 3] Checking Ollama status..." -ForegroundColor Green
$ollamaUrl = "http://localhost:11434/api/tags"
try {
    $ollamaResponse = Invoke-WebRequest -Uri $ollamaUrl -Method GET -UseBasicParsing -TimeoutSec 5
    Write-Host "✓ Ollama is running" -ForegroundColor Green
    
    $ollamaData = $ollamaResponse.Content | ConvertFrom-Json
    Write-Host "  Ollama Models: $($ollamaData.models.Count)" -ForegroundColor Gray
    
    if ($ollamaData.models.Count -gt 0) {
        Write-Host ""
        Write-Host "Ollama Models:" -ForegroundColor Yellow
        foreach ($model in $ollamaData.models) {
            Write-Host "  - $($model.name)" -ForegroundColor White
        }
    }
    
} catch {
    Write-Host "✗ Ollama is not running or not responding" -ForegroundColor Red
    Write-Host "  This is OK - the endpoint will use fallback models" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To start Ollama:" -ForegroundColor Yellow
    Write-Host "  ollama serve" -ForegroundColor Gray
}

Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Test Complete" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Summary
Write-Host "Summary:" -ForegroundColor Cyan
if ($jsonResponse -and $jsonResponse.source) {
    if ($jsonResponse.source -eq "ollama") {
        Write-Host "  ✓ Models loaded from Ollama" -ForegroundColor Green
    } elseif ($jsonResponse.source -eq "config") {
        Write-Host "  ⚠ Using configured default model" -ForegroundColor Yellow
    } elseif ($jsonResponse.source -eq "fallback") {
        Write-Host "  ⚠ Using fallback models" -ForegroundColor Yellow
    } else {
        Write-Host "  ⚠ Unknown source: $($jsonResponse.source)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ⚠ Could not determine source" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Check backend logs for detailed information" -ForegroundColor Gray
Write-Host "  2. Open Chat Studio: http://localhost:3001" -ForegroundColor Gray
Write-Host "  3. Verify models appear in the dropdown" -ForegroundColor Gray
Write-Host ""
