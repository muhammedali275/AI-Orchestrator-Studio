# Tool Connectivity Testing Script
# Tests the improved tool connectivity checking functionality

Write-Host "=== Tool Connectivity Testing ===" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"
$headers = @{
    "Content-Type" = "application/json"
}

# Test 1: Create a tool pointing to a non-existent service
Write-Host "Test 1: Testing connection to non-existent service..." -ForegroundColor Yellow
$tool1 = @{
    name = "test_nonexistent"
    type = "http_request"
    config = @{
        base_url = "http://localhost:9999"
        timeout = 30
    }
    enabled = $true
    description = "Test tool for non-existent service"
} | ConvertTo-Json

try {
    # Create tool
    $response = Invoke-RestMethod -Uri "$baseUrl/api/tools" -Method Post -Headers $headers -Body $tool1
    Write-Host "✓ Tool created: $($response.message)" -ForegroundColor Green
    
    # Test connection
    Write-Host "  Testing connectivity..." -ForegroundColor Gray
    $testResult = Invoke-RestMethod -Uri "$baseUrl/api/tools/test_nonexistent/test" -Method Post -Headers $headers
    
    Write-Host "  Status: $($testResult.connectivity_status)" -ForegroundColor $(if ($testResult.success) { "Green" } else { "Red" })
    Write-Host "  Message: $($testResult.message)" -ForegroundColor Gray
    if ($testResult.suggestion) {
        Write-Host "  Suggestion: $($testResult.suggestion)" -ForegroundColor Cyan
    }
    Write-Host ""
} catch {
    Write-Host "✗ Test 1 failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}

# Test 2: Create a tool pointing to the backend itself (should succeed)
Write-Host "Test 2: Testing connection to running service (backend)..." -ForegroundColor Yellow
$tool2 = @{
    name = "test_backend"
    type = "http_request"
    config = @{
        base_url = "http://localhost:8000"
        timeout = 30
    }
    enabled = $true
    description = "Test tool for backend service"
} | ConvertTo-Json

try {
    # Create tool
    $response = Invoke-RestMethod -Uri "$baseUrl/api/tools" -Method Post -Headers $headers -Body $tool2
    Write-Host "✓ Tool created: $($response.message)" -ForegroundColor Green
    
    # Test connection
    Write-Host "  Testing connectivity..." -ForegroundColor Gray
    $testResult = Invoke-RestMethod -Uri "$baseUrl/api/tools/test_backend/test" -Method Post -Headers $headers
    
    Write-Host "  Status: $($testResult.connectivity_status)" -ForegroundColor $(if ($testResult.success) { "Green" } else { "Red" })
    Write-Host "  Message: $($testResult.message)" -ForegroundColor Gray
    if ($testResult.response_time_ms) {
        Write-Host "  Response Time: $($testResult.response_time_ms)ms" -ForegroundColor Cyan
    }
    if ($testResult.host -and $testResult.port) {
        Write-Host "  Endpoint: $($testResult.host):$($testResult.port)" -ForegroundColor Gray
    }
    Write-Host ""
} catch {
    Write-Host "✗ Test 2 failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}

# Test 3: Test with invalid hostname (DNS error)
Write-Host "Test 3: Testing connection with invalid hostname..." -ForegroundColor Yellow
$tool3 = @{
    name = "test_invalid_host"
    type = "http_request"
    config = @{
        base_url = "http://this-host-does-not-exist-12345.com"
        timeout = 30
    }
    enabled = $true
    description = "Test tool for invalid hostname"
} | ConvertTo-Json

try {
    # Create tool
    $response = Invoke-RestMethod -Uri "$baseUrl/api/tools" -Method Post -Headers $headers -Body $tool3
    Write-Host "✓ Tool created: $($response.message)" -ForegroundColor Green
    
    # Test connection
    Write-Host "  Testing connectivity..." -ForegroundColor Gray
    $testResult = Invoke-RestMethod -Uri "$baseUrl/api/tools/test_invalid_host/test" -Method Post -Headers $headers
    
    Write-Host "  Status: $($testResult.connectivity_status)" -ForegroundColor $(if ($testResult.success) { "Green" } else { "Red" })
    Write-Host "  Message: $($testResult.message)" -ForegroundColor Gray
    if ($testResult.suggestion) {
        Write-Host "  Suggestion: $($testResult.suggestion)" -ForegroundColor Cyan
    }
    Write-Host ""
} catch {
    Write-Host "✗ Test 3 failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}

# Test 4: Skip connectivity test
Write-Host "Test 4: Testing with skip_connectivity=true..." -ForegroundColor Yellow
$tool4 = @{
    name = "test_skip_connectivity"
    type = "http_request"
    config = @{
        base_url = "http://localhost:9999"
        timeout = 30
    }
    enabled = $true
    description = "Test tool with skipped connectivity"
} | ConvertTo-Json

try {
    # Create tool
    $response = Invoke-RestMethod -Uri "$baseUrl/api/tools" -Method Post -Headers $headers -Body $tool4
    Write-Host "✓ Tool created: $($response.message)" -ForegroundColor Green
    
    # Test connection with skip_connectivity
    Write-Host "  Testing with skip_connectivity=true..." -ForegroundColor Gray
    $testResult = Invoke-RestMethod -Uri "$baseUrl/api/tools/test_skip_connectivity/test?skip_connectivity=true" -Method Post -Headers $headers
    
    Write-Host "  Status: $($testResult.connectivity_status)" -ForegroundColor $(if ($testResult.success) { "Green" } else { "Red" })
    Write-Host "  Message: $($testResult.message)" -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "✗ Test 4 failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}

# Test 5: Test with custom timeout
Write-Host "Test 5: Testing with custom timeout (60 seconds)..." -ForegroundColor Yellow
$tool5 = @{
    name = "test_custom_timeout"
    type = "http_request"
    config = @{
        base_url = "http://localhost:8000"
        timeout = 60
    }
    enabled = $true
    description = "Test tool with custom timeout"
} | ConvertTo-Json

try {
    # Create tool
    $response = Invoke-RestMethod -Uri "$baseUrl/api/tools" -Method Post -Headers $headers -Body $tool5
    Write-Host "✓ Tool created: $($response.message)" -ForegroundColor Green
    
    # Test connection
    Write-Host "  Testing connectivity with 60s timeout..." -ForegroundColor Gray
    $testResult = Invoke-RestMethod -Uri "$baseUrl/api/tools/test_custom_timeout/test" -Method Post -Headers $headers
    
    Write-Host "  Status: $($testResult.connectivity_status)" -ForegroundColor $(if ($testResult.success) { "Green" } else { "Red" })
    Write-Host "  Message: $($testResult.message)" -ForegroundColor Gray
    if ($testResult.timeout_seconds) {
        Write-Host "  Timeout Used: $($testResult.timeout_seconds)s" -ForegroundColor Cyan
    }
    Write-Host ""
} catch {
    Write-Host "✗ Test 5 failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}

# Cleanup - Delete test tools
Write-Host "Cleaning up test tools..." -ForegroundColor Yellow
$testTools = @("test_nonexistent", "test_backend", "test_invalid_host", "test_skip_connectivity", "test_custom_timeout")

foreach ($toolName in $testTools) {
    try {
        Invoke-RestMethod -Uri "$baseUrl/api/tools/$toolName" -Method Delete -Headers $headers | Out-Null
        Write-Host "✓ Deleted: $toolName" -ForegroundColor Green
    } catch {
        Write-Host "  Could not delete $toolName (may not exist)" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "=== Testing Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Summary of Improvements:" -ForegroundColor Yellow
Write-Host "  ✓ TCP port checking before HTTP request" -ForegroundColor Green
Write-Host "  ✓ Dynamic timeout from tool configuration" -ForegroundColor Green
Write-Host "  ✓ Detailed error messages with suggestions" -ForegroundColor Green
Write-Host "  ✓ DNS error detection" -ForegroundColor Green
Write-Host "  ✓ Response time measurement" -ForegroundColor Green
Write-Host "  ✓ Skip connectivity option" -ForegroundColor Green
Write-Host ""
