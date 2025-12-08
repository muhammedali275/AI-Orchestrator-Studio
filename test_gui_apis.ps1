# GUI API Testing Script
# Tests all API endpoints for the new GUI pages

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "GUI API Comprehensive Testing" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"
$testResults = @()

# Test 1: GET Agents
Write-Host "[TEST 1] GET /api/agents" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/agents" -Method GET
    Write-Host "✓ Success: Returned $($response.Count) agents" -ForegroundColor Green
    $testResults += @{Test="GET /api/agents"; Status="PASS"}
} catch {
    Write-Host "✗ Failed: $_" -ForegroundColor Red
    $testResults += @{Test="GET /api/agents"; Status="FAIL"}
}
Write-Host ""

# Test 2: POST Agent
Write-Host "[TEST 2] POST /api/agents" -ForegroundColor Yellow
try {
    $agentData = @{
        name = "test_agent"
        url = "http://localhost:8080"
        timeout_seconds = 30
        enabled = $true
        metadata = @{
            system_prompt = "You are a helpful assistant"
            llm_connection = "local_ollama"
        }
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$baseUrl/api/agents" -Method POST -Body $agentData -ContentType "application/json"
    Write-Host "✓ Success: Agent created" -ForegroundColor Green
    $testResults += @{Test="POST /api/agents"; Status="PASS"}
} catch {
    Write-Host "✗ Failed: $_" -ForegroundColor Red
    $testResults += @{Test="POST /api/agents"; Status="FAIL"}
}
Write-Host ""

# Test 3: GET Credentials
Write-Host "[TEST 3] GET /api/credentials" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/credentials" -Method GET
    Write-Host "✓ Success: Returned $($response.total) credentials" -ForegroundColor Green
    $testResults += @{Test="GET /api/credentials"; Status="PASS"}
} catch {
    Write-Host "✗ Failed: $_" -ForegroundColor Red
    $testResults += @{Test="GET /api/credentials"; Status="FAIL"}
}
Write-Host ""

# Test 4: POST Credential
Write-Host "[TEST 4] POST /api/credentials" -ForegroundColor Yellow
try {
    $credData = @{
        name = "test_api_key"
        type = "api_key"
        secret = "sk-test123456789"
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$baseUrl/api/credentials" -Method POST -Body $credData -ContentType "application/json"
    Write-Host "✓ Success: Credential created with ID: $($response.id)" -ForegroundColor Green
    $testResults += @{Test="POST /api/credentials"; Status="PASS"}
    $script:credentialId = $response.id
} catch {
    Write-Host "✗ Failed: $_" -ForegroundColor Red
    $testResults += @{Test="POST /api/credentials"; Status="FAIL"}
}
Write-Host ""

# Test 5: GET Datasources
Write-Host "[TEST 5] GET /api/datasources" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/datasources" -Method GET
    Write-Host "✓ Success: Returned $($response.Count) datasources" -ForegroundColor Green
    $testResults += @{Test="GET /api/datasources"; Status="PASS"}
} catch {
    Write-Host "✗ Failed: $_" -ForegroundColor Red
    $testResults += @{Test="GET /api/datasources"; Status="FAIL"}
}
Write-Host ""

# Test 6: POST Datasource
Write-Host "[TEST 6] POST /api/datasources" -ForegroundColor Yellow
try {
    $dsData = @{
        name = "test_cubejs"
        type = "cubejs"
        url = "http://localhost:4000"
        timeout_seconds = 30
        enabled = $true
        config = @{}
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$baseUrl/api/datasources" -Method POST -Body $dsData -ContentType "application/json"
    Write-Host "✓ Success: Datasource created" -ForegroundColor Green
    $testResults += @{Test="POST /api/datasources"; Status="PASS"}
} catch {
    Write-Host "✗ Failed: $_" -ForegroundColor Red
    $testResults += @{Test="POST /api/datasources"; Status="FAIL"}
}
Write-Host ""

# Test 7: GET LLM Config
Write-Host "[TEST 7] GET /api/llm/config" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/llm/config" -Method GET
    Write-Host "✓ Success: LLM config retrieved" -ForegroundColor Green
    Write-Host "  Base URL: $($response.base_url)" -ForegroundColor Gray
    Write-Host "  Model: $($response.default_model)" -ForegroundColor Gray
    $testResults += @{Test="GET /api/llm/config"; Status="PASS"}
} catch {
    Write-Host "✗ Failed: $_" -ForegroundColor Red
    $testResults += @{Test="GET /api/llm/config"; Status="FAIL"}
}
Write-Host ""

# Test 8: GET Monitoring Health
Write-Host "[TEST 8] GET /api/monitoring/health" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/monitoring/health" -Method GET
    Write-Host "✓ Success: Health status: $($response.status)" -ForegroundColor Green
    $testResults += @{Test="GET /api/monitoring/health"; Status="PASS"}
} catch {
    Write-Host "✗ Failed: $_" -ForegroundColor Red
    $testResults += @{Test="GET /api/monitoring/health"; Status="FAIL"}
}
Write-Host ""

# Test 9: GET Monitoring Metrics
Write-Host "[TEST 9] GET /api/monitoring/metrics" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/monitoring/metrics" -Method GET
    Write-Host "✓ Success: Metrics retrieved" -ForegroundColor Green
    Write-Host "  CPU: $($response.system.cpu.percent)%" -ForegroundColor Gray
    Write-Host "  Memory: $($response.system.memory.percent)%" -ForegroundColor Gray
    $testResults += @{Test="GET /api/monitoring/metrics"; Status="PASS"}
} catch {
    Write-Host "✗ Failed: $_" -ForegroundColor Red
    $testResults += @{Test="GET /api/monitoring/metrics"; Status="FAIL"}
}
Write-Host ""

# Test 10: GET Topology
Write-Host "[TEST 10] GET /api/topology/graph" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/topology/graph" -Method GET
    Write-Host "✓ Success: Topology graph retrieved" -ForegroundColor Green
    Write-Host "  Nodes: $($response.nodes.Count)" -ForegroundColor Gray
    $testResults += @{Test="GET /api/topology/graph"; Status="PASS"}
} catch {
    Write-Host "✗ Failed: $_" -ForegroundColor Red
    $testResults += @{Test="GET /api/topology/graph"; Status="FAIL"}
}
Write-Host ""

# Summary
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
$passed = ($testResults | Where-Object { $_.Status -eq "PASS" }).Count
$failed = ($testResults | Where-Object { $_.Status -eq "FAIL" }).Count
Write-Host "Total Tests: $($testResults.Count)" -ForegroundColor White
Write-Host "Passed: $passed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor Red
Write-Host ""

if ($failed -eq 0) {
    Write-Host "✓ All tests passed!" -ForegroundColor Green
} else {
    Write-Host "✗ Some tests failed. Review the output above." -ForegroundColor Red
}
