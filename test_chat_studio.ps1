# Chat Studio Test Script (PowerShell)
# Tests all Chat Studio endpoints with proper error handling

$ErrorActionPreference = "Continue"

Write-Host "===================================" -ForegroundColor Cyan
Write-Host "Chat Studio API Test Suite" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

$BASE_URL = "http://localhost:8000"
$PASSED = 0
$FAILED = 0
$CONVERSATION_ID = $null
$CONNECTION_ID = $null

function Test-Endpoint {
    param(
        [string]$Method,
        [string]$Endpoint,
        [string]$Description,
        [string]$Data = "",
        [int]$ExpectedCode = 200
    )
    
    Write-Host "Testing: $Description... " -NoNewline
    
    try {
        $uri = "$BASE_URL$Endpoint"
        $params = @{
            Uri = $uri
            Method = $Method
            TimeoutSec = 30
        }
        
        if ($Data) {
            $params.Body = $Data
            $params.ContentType = "application/json"
        }
        
        $response = Invoke-WebRequest @params
        
        if ($response.StatusCode -ge $ExpectedCode -and $response.StatusCode -lt ($ExpectedCode + 100)) {
            Write-Host "✓ PASSED" -ForegroundColor Green -NoNewline
            Write-Host " (HTTP $($response.StatusCode))"
            $script:PASSED++
            
            # Try to parse and display JSON
            if ($response.Content) {
                try {
                    $json = $response.Content | ConvertFrom-Json
                    $json | ConvertTo-Json -Depth 2 | Select-Object -First 10 | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
                } catch {
                    Write-Host "  $($response.Content.Substring(0, [Math]::Min(200, $response.Content.Length)))" -ForegroundColor Gray
                }
            }
            
            return $response.Content
        } else {
            Write-Host "✗ FAILED" -ForegroundColor Red -NoNewline
            Write-Host " (HTTP $($response.StatusCode), expected $ExpectedCode)"
            $script:FAILED++
            return $null
        }
    } catch {
        Write-Host "✗ FAILED" -ForegroundColor Red -NoNewline
        Write-Host " (Error: $($_.Exception.Message))"
        if ($_.Exception.Response) {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $responseBody = $reader.ReadToEnd()
            Write-Host "  Response: $responseBody" -ForegroundColor Yellow
        }
        $script:FAILED++
        return $null
    }
}

# 0. Connectivity Check
Write-Host "0. Connectivity Check" -ForegroundColor Yellow
Write-Host "---------------------"
try {
    $health = Invoke-RestMethod -Uri "$BASE_URL/health" -TimeoutSec 5
    Write-Host "✓ Server is reachable" -ForegroundColor Green
} catch {
    Write-Host "✗ Cannot connect to $BASE_URL" -ForegroundColor Red
    Write-Host "Please ensure the Chat Studio server is running."
    exit 1
}
Write-Host ""

# 1. Backend Health Check
Write-Host "1. Backend Health Check" -ForegroundColor Yellow
Write-Host "----------------------"
Test-Endpoint -Method GET -Endpoint "/health" -Description "Health endpoint"
Write-Host ""

# 2. LLM Connections Check
Write-Host "2. LLM Connections Check" -ForegroundColor Yellow
Write-Host "-------------------------"
$connectionsResponse = Test-Endpoint -Method GET -Endpoint "/api/config/llm-connections" -Description "Get LLM connections"

if ($connectionsResponse) {
    try {
        $connections = ($connectionsResponse | ConvertFrom-Json).connections
        if ($connections -and $connections.Count -gt 0) {
            $script:CONNECTION_ID = $connections[0].id
            Write-Host "ℹ Found connection ID: $CONNECTION_ID" -ForegroundColor Cyan
            
            # Test fetching models from this connection
            $modelsResponse = Test-Endpoint -Method GET -Endpoint "/api/config/llm-connections/$CONNECTION_ID/models" -Description "Get models from connection"
            
            if ($modelsResponse) {
                $models = ($modelsResponse | ConvertFrom-Json).models
                if ($models) {
                    Write-Host "ℹ Available models:" -ForegroundColor Cyan
                    $models | ForEach-Object {
                        Write-Host "  - $($_.id): $($_.name)" -ForegroundColor Gray
                    }
                }
            }
        }
    } catch {
        Write-Host "  Warning: Could not parse connections response" -ForegroundColor Yellow
    }
}
Write-Host ""

# 3. Model Detection
Write-Host "3. Model Detection (Ollama)" -ForegroundColor Yellow
Write-Host "---------------------------"
Test-Endpoint -Method GET -Endpoint "/api/chat/ui/models" -Description "Get available models"
Write-Host ""

# 4. Routing Profiles
Write-Host "4. Routing Profiles" -ForegroundColor Yellow
Write-Host "-------------------"
Test-Endpoint -Method GET -Endpoint "/api/chat/ui/profiles" -Description "Get routing profiles"
Write-Host ""

# 5. Prompt Profiles
Write-Host "5. Prompt Profiles" -ForegroundColor Yellow
Write-Host "------------------"
Test-Endpoint -Method GET -Endpoint "/api/chat/ui/prompt-profiles" -Description "Get prompt profiles"
Write-Host ""

# 6. Conversation Management
Write-Host "6. Conversation Management" -ForegroundColor Yellow
Write-Host "--------------------------"

$createConvData = @{
    title = "Test Conversation"
    model_id = "sqlcoder:7b"
    routing_profile = "direct_llm"
} | ConvertTo-Json

$createResponse = Test-Endpoint -Method POST -Endpoint "/api/chat/ui/conversations" -Description "Create new conversation" -Data $createConvData

if ($createResponse) {
    try {
        $conv = $createResponse | ConvertFrom-Json
        $script:CONVERSATION_ID = $conv.id ?? $conv.conversation_id
        if ($CONVERSATION_ID) {
            Write-Host "ℹ Created conversation ID: $CONVERSATION_ID" -ForegroundColor Cyan
        }
    } catch {
        Write-Host "  Warning: Could not extract conversation ID" -ForegroundColor Yellow
    }
}

Test-Endpoint -Method GET -Endpoint "/api/chat/ui/conversations" -Description "List conversations"

if ($CONVERSATION_ID) {
    Test-Endpoint -Method GET -Endpoint "/api/chat/ui/conversations/$CONVERSATION_ID" -Description "Get specific conversation"
}
Write-Host ""

# 7. Chat Functionality
Write-Host "7. Chat Functionality" -ForegroundColor Yellow
Write-Host "---------------------"

Write-Host "ℹ Testing with explicit connection_id and model_id (Ollama)" -ForegroundColor Cyan

$chatData = @{
    message = "Hello, this is a test. Please respond briefly."
    model_id = "sqlcoder:7b"
    connection_id = if ($CONNECTION_ID) { $CONNECTION_ID } else { "llm-1767854937489" }
    routing_profile = "direct_llm"
    use_memory = $false
} | ConvertTo-Json

Test-Endpoint -Method POST -Endpoint "/api/chat/ui/send" -Description "Send chat message" -Data $chatData

# Test streaming endpoint
Write-Host "ℹ Testing streaming endpoint..." -ForegroundColor Cyan
Write-Host "Testing: Chat streaming... " -NoNewline

$streamData = @{
    message = "Say hello in 3 words"
    model_id = "sqlcoder:7b"
    connection_id = if ($CONNECTION_ID) { $CONNECTION_ID } else { "llm-1767854937489" }
    routing_profile = "direct_llm"
    use_memory = $false
    stream = $true
} | ConvertTo-Json

try {
    $streamResponse = Invoke-WebRequest -Uri "$BASE_URL/api/chat/ui/send/stream" -Method POST -Body $streamData -ContentType "application/json" -TimeoutSec 30
    
    if ($streamResponse.StatusCode -eq 200) {
        Write-Host "✓ PASSED" -ForegroundColor Green
        $preview = $streamResponse.Content.Substring(0, [Math]::Min(200, $streamResponse.Content.Length))
        Write-Host "  First 200 chars: $preview" -ForegroundColor Gray
        $script:PASSED++
    } else {
        Write-Host "✗ FAILED (HTTP $($streamResponse.StatusCode))" -ForegroundColor Red
        $script:FAILED++
    }
} catch {
    Write-Host "✗ FAILED ($($_.Exception.Message))" -ForegroundColor Red
    $script:FAILED++
}

if ($CONVERSATION_ID) {
    $followUpData = @{
        message = "Follow up message"
        conversation_id = $CONVERSATION_ID
        model_id = "sqlcoder:7b"
        connection_id = if ($CONNECTION_ID) { $CONNECTION_ID } else { "llm-1767854937489" }
        routing_profile = "direct_llm"
    } | ConvertTo-Json
    
    Test-Endpoint -Method POST -Endpoint "/api/chat/ui/send" -Description "Send message to specific conversation" -Data $followUpData
}
Write-Host ""

# 8. Message History
Write-Host "8. Message History" -ForegroundColor Yellow
Write-Host "------------------"
if ($CONVERSATION_ID) {
    Test-Endpoint -Method GET -Endpoint "/api/chat/ui/conversations/$CONVERSATION_ID/messages" -Description "Get conversation messages"
} else {
    Write-Host "ℹ Skipping - no conversation ID available" -ForegroundColor Cyan
}
Write-Host ""

# 9. Metrics
Write-Host "9. Metrics" -ForegroundColor Yellow
Write-Host "----------"
Test-Endpoint -Method GET -Endpoint "/api/chat/ui/metrics" -Description "Get chat metrics"
Write-Host ""

# 10. Cleanup
Write-Host "10. Cleanup (Optional)" -ForegroundColor Yellow
Write-Host "---------------------"
if ($CONVERSATION_ID) {
    $response = Read-Host "Delete test conversation? (y/n)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        Test-Endpoint -Method DELETE -Endpoint "/api/chat/ui/conversations/$CONVERSATION_ID" -Description "Delete test conversation"
    } else {
        Write-Host "ℹ Keeping test conversation: $CONVERSATION_ID" -ForegroundColor Cyan
    }
}
Write-Host ""

# Summary
Write-Host "===================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host "Passed: $PASSED" -ForegroundColor Green
Write-Host "Failed: $FAILED" -ForegroundColor Red
Write-Host "Total: $($PASSED + $FAILED)"
Write-Host ""

if ($FAILED -eq 0) {
    Write-Host "All tests passed! ✓" -ForegroundColor Green
    exit 0
} else {
    Write-Host "Some tests failed! ✗" -ForegroundColor Red
    Write-Host "Review the output above for details." -ForegroundColor Yellow
    exit 1
}
