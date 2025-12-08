# Comprehensive GUI API Testing Script
# Simulates manual GUI testing by testing all CRUD operations

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Comprehensive GUI API Testing" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"
$testResults = @()

# Test 1: Create Agent
Write-Host "[TEST 1] POST /api/agents - Create Agent" -ForegroundColor Yellow
try {
    $agentData = @{
        name = "test_agent_001"
        url = "http://localhost:8080"
        timeout_seconds = 30
        enabled = $true
        metadata = @{
            system_prompt = "You are a helpful AI assistant"
            description = "Test agent for GUI testing"
        }
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$baseUrl/api/agents" -Method POST -Body $agentData -ContentType "application/json"
    Write-Host "✓ Success: Agent created" -ForegroundColor Green
    $testResults += @{Test="POST /api/agents"; Status="PASS"; Details="Agent created successfully"}
} catch {
    Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
    $testResults += @{Test="POST /api/agents"; Status="FAIL"; Details=$_.Exception.Message}
}
Write-Host ""

# Test 2: List Agents
Write-Host "[TEST 2] GET /api/agents - List Agents" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/agents" -Method GET
    Write-Host "✓ Success: Retrieved $($response.Count) agents" -ForegroundColor Green
    $testResults += @{Test="GET /api/agents"; Status="PASS"; Details="Retrieved agents list"}
} catch {
    Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
    $testResults += @{Test="GET /api/agents"; Status="FAIL"; Details=$_.Exception.Message}
}
Write-Host ""

# Test 3: Create Credential
Write-Host "[TEST 3] POST /api/credentials - Create Credential" -ForegroundColor Yellow
try {
    $credData = @{
        name = "test_api_key_001"
        type = "api_key"
        secret = "sk-test-key-12345678"
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$baseUrl/api/credentials" -Method POST -Body $credData -ContentType "application/json"
    Write-Host "✓ Success: Credential created with ID: $($response.id)" -ForegroundColor Green
    $script:credentialId = $response.id
    $testResults += @{Test="POST /api/credentials"; Status="PASS"; Details="Credential created"}
} catch {
    Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
    $testResults += @{Test="POST /api/credentials"; Status="FAIL"; Details=$_.Exception.Message}
}
Write-Host ""

# Test 4: List Credentials
Write-Host "[TEST 4] GET /api/credentials - List Credentials" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/credentials" -Method GET
    Write-Host "✓ Success: Retrieved $($response.total) credentials" -ForegroundColor Green
    $testResults += @{Test="GET /api/credentials"; Status="PASS"; Details="Retrieved credentials"}
} catch {
    Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
    $testResults += @{Test="GET /api/credentials"; Status="FAIL"; Details=$_.Exception.Message}
}
Write-Host ""

# Test 5: Create Datasource
Write-Host "[TEST 5] POST /api/datasources - Create Datasource" -ForegroundColor Yellow
try {
    $dsData = @{
        name = "test_cubejs_001"
        type = "cubejs"
        url = "http://localhost:4000"
        timeout_seconds = 30
        enabled = $true
        config = @{}
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$baseUrl/api/datasources" -Method POST -Body $dsData -ContentType "application/json"
    Write-Host "✓ Success: Datasource created" -ForegroundColor Green
    $testResults += @{Test="POST /api/datasources"; Status="PASS"; Details="Datasource created"}
} catch {
    Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
    $testResults += @{Test="POST /api/datasources"; Status="FAIL"; Details=$_.Exception.Message}
}
Write-Host ""

# Test 6: List Datasources
Write-Host "[TEST 6] GET /api/datasources - List Datasources" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/datasources" -Method GET
    Write-Host "✓ Success: Retrieved $($response.Count) datasources" -ForegroundColor Green
    $testResults += @{Test="GET /api/datasources"; Status="PASS"; Details="Retrieved datasources"}
} catch {
    Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
    $testResults += @{Test="GET /api/datasources"; Status="FAIL"; Details=$_.Exception.Message}
}
Write-Host ""

# Test 7: Create Tool
Write-Host "[TEST 7] POST /api/tools - Create Tool" -ForegroundColor Yellow
try {
    $toolData = @{
        name = "test_http_tool"
        type = "http_request"
        enabled = $true
        config = @{
            base_url = "http://localhost:8080"
            timeout = 30
        }
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$baseUrl/api/tools" -Method POST -Body $toolData -ContentType "application/json"
    Write-Host "✓ Success: Tool created" -ForegroundColor Green
    $testResults += @{Test="POST /api/tools"; Status="PASS"; Details="Tool created"}
} catch {
    Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
    $testResults += @{Test="POST /api/tools"; Status="FAIL"; Details=$_.Exception.Message}
}
Write-Host ""

# Test 8: List Tools
Write-Host "[TEST 8] GET /api/tools - List Tools" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/tools" -Method GET
    Write-Host "✓ Success: Retrieved $($response.Count) tools" -ForegroundColor Green
    $testResults += @{Test="GET /api/tools"; Status="PASS"; Details="Retrieved tools"}
} catch {
    Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
    $testResults += @{Test="GET /api/tools"; Status="FAIL"; Details=$_.Exception.Message}
}
Write-Host ""

# Test 9: Get Certificate Info
Write-Host "[TEST 9] GET /api/certs - Get Certificate Info" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/certs" -Method GET
    Write-Host "✓ Success: TLS Enabled: $($response.tls_enabled)" -ForegroundColor Green
    $testResults += @{Test="GET /api/certs"; Status="PASS"; Details="Certificate info retrieved"}
} catch {
    Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
    $testResults += @{Test="GET /api/certs"; Status="FAIL"; Details=$_.Exception.Message}
}
Write-Host ""

# Test 10: Get LLM Config
Write-Host "[TEST 10] GET /api/llm/config - Get LLM Config" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/llm/config" -Method GET
    Write-Host "✓ Success: LLM Base URL: $($response.base_url)" -ForegroundColor Green
    $testResults += @{Test="GET /api/llm/config"; Status="PASS"; Details="LLM config retrieved"}
} catch {
    Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
    $testResults += @{Test="GET /api/llm/config"; Status="FAIL"; Details=$_.Exception.Message}
}
Write-Host ""

# Test 11: Get Monitoring Health
Write-Host "[TEST 11] GET /api/monitoring/health - Get Health Status" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/monitoring/health" -Method GET
    Write-Host "✓ Success: Status: $($response.status)" -ForegroundColor Green
    $testResults += @{Test="GET /api/monitoring/health"; Status="PASS"; Details="Health status retrieved"}
} catch {
    Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
    $testResults += @{Test="GET /api/monitoring/health"; Status="FAIL"; Details=$_.Exception.Message}
}
Write-Host ""

# Test 12: Get Topology Graph
Write-Host "[TEST 12] GET /api/topology/graph - Get Topology" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/topology/graph" -Method GET
    Write-Host "✓ Success: Nodes: $($response.nodes.Count)" -ForegroundColor Green
    $testResults += @{Test="GET /api/topology/graph"; Status="PASS"; Details="Topology retrieved"}
} catch {
    Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
    $testResults += @{Test="GET /api/topology/graph"; Status="FAIL"; Details=$_.Exception.Message}
}
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
$passed = ($testResults | Where-Object { $_.Status -eq "PASS" }).Count
$failed = ($testResults | Where-Object { $_.Status -eq "FAIL" }).Count
Write-Host "Total Tests: $($testResults.Count)" -ForegroundColor White
Write-Host "Passed: $passed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor Red
Write-Host ""

if ($failed -eq 0) {
    Write-Host "✓ All CRUD operations working!" -ForegroundColor Green
} else {
    Write-Host "✗ Some tests failed. Review the output above." -ForegroundColor Red
}

# Display detailed results
Write-Host "`nDetailed Results:" -ForegroundColor Cyan
$testResults | ForEach-Object {
    $color = if ($_.Status -eq "PASS") { "Green" } else { "Red" }
    Write-Host "  $($_.Test): $($_.Status) - $($_.Details)" -ForegroundColor $color
}
