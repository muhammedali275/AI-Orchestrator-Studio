# Test script for Tools/DataSources/Credentials connectivity testing fix
# This script tests the new enhanced error handling and skip_connectivity feature

$BASE_URL = "http://localhost:8000"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Testing Tools/DataSources Connectivity Fix" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Test 1: Create a tool (should succeed even if endpoint not reachable)
Write-Host "Test 1: Creating a tool with unreachable endpoint..." -ForegroundColor Yellow
try {
    $toolData = @{
        name = "test_http_tool_fix"
        type = "http_request"
        enabled = $true
        description = "Test tool for connectivity fix"
        config = @{
            base_url = "http://localhost:9999"
            timeout = 30
        }
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "$BASE_URL/api/tools" -Method Post -ContentType "application/json" -Body $toolData
    
    if ($response.success) {
        Write-Host "  ✓ Tool created successfully" -ForegroundColor Green
        Write-Host "  Message: $($response.message)" -ForegroundColor Gray
    } else {
        Write-Host "  ✗ Failed to create tool" -ForegroundColor Red
    }
} catch {
    Write-Host "  ✗ Error: $_" -ForegroundColor Red
}

# Test 2: Test tool connectivity (should fail gracefully with clear message)
Write-Host "`nTest 2: Testing tool connectivity (endpoint not running)..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/tools/test_http_tool_fix/test" -Method Post
    
    Write-Host "  Configuration Valid: $($response.config_valid)" -ForegroundColor $(if ($response.config_valid) { "Green" } else { "Red" })
    Write-Host "  Configuration Saved: $($response.config_saved)" -ForegroundColor $(if ($response.config_saved) { "Green" } else { "Red" })
    Write-Host "  Connectivity Tested: $($response.connectivity_tested)" -ForegroundColor Gray
    Write-Host "  Connectivity Status: $($response.connectivity_status)" -ForegroundColor $(if ($response.connectivity_status -eq "reachable") { "Green" } else { "Yellow" })
    Write-Host "  Message: $($response.message)" -ForegroundColor Gray
    
    if ($response.suggestion) {
        Write-Host "  💡 Suggestion: $($response.suggestion)" -ForegroundColor Cyan
    }
    
    if ($response.config_saved -and $response.config_valid) {
        Write-Host "`n  ✓ SUCCESS: Configuration is valid and saved!" -ForegroundColor Green
        Write-Host "  ⚠ Connectivity failed as expected (service not running)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ✗ Error: $_" -ForegroundColor Red
}

# Test 3: Test tool with skip_connectivity=true
Write-Host "`nTest 3: Testing tool with skip_connectivity=true..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/tools/test_http_tool_fix/test?skip_connectivity=true" -Method Post
    
    Write-Host "  Configuration Valid: $($response.config_valid)" -ForegroundColor $(if ($response.config_valid) { "Green" } else { "Red" })
    Write-Host "  Configuration Saved: $($response.config_saved)" -ForegroundColor $(if ($response.config_saved) { "Green" } else { "Red" })
    Write-Host "  Connectivity Tested: $($response.connectivity_tested)" -ForegroundColor Gray
    Write-Host "  Connectivity Status: $($response.connectivity_status)" -ForegroundColor Gray
    Write-Host "  Message: $($response.message)" -ForegroundColor Gray
    
    if ($response.success -and $response.connectivity_status -eq "skipped") {
        Write-Host "`n  ✓ SUCCESS: Configuration validated without connectivity test!" -ForegroundColor Green
    }
} catch {
    Write-Host "  ✗ Error: $_" -ForegroundColor Red
}

# Test 4: Create a datasource
Write-Host "`nTest 4: Creating a datasource with unreachable endpoint..." -ForegroundColor Yellow
try {
    $dsData = @{
        name = "test_datasource_fix"
        type = "api"
        url = "http://localhost:8888"
        enabled = $true
        timeout_seconds = 30
        config = @{}
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "$BASE_URL/api/datasources" -Method Post -ContentType "application/json" -Body $dsData
    
    if ($response.success) {
        Write-Host "  ✓ DataSource created successfully" -ForegroundColor Green
        Write-Host "  Message: $($response.message)" -ForegroundColor Gray
    } else {
        Write-Host "  ✗ Failed to create datasource" -ForegroundColor Red
    }
} catch {
    Write-Host "  ✗ Error: $_" -ForegroundColor Red
}

# Test 5: Test datasource connectivity
Write-Host "`nTest 5: Testing datasource connectivity (endpoint not running)..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/datasources/test_datasource_fix/test" -Method Post
    
    Write-Host "  Configuration Valid: $($response.config_valid)" -ForegroundColor $(if ($response.config_valid) { "Green" } else { "Red" })
    Write-Host "  Configuration Saved: $($response.config_saved)" -ForegroundColor $(if ($response.config_saved) { "Green" } else { "Red" })
    Write-Host "  Connectivity Tested: $($response.connectivity_tested)" -ForegroundColor Gray
    Write-Host "  Connectivity Status: $($response.connectivity_status)" -ForegroundColor $(if ($response.connectivity_status -eq "reachable") { "Green" } else { "Yellow" })
    Write-Host "  Message: $($response.message)" -ForegroundColor Gray
    
    if ($response.suggestion) {
        Write-Host "  💡 Suggestion: $($response.suggestion)" -ForegroundColor Cyan
    }
    
    if ($response.config_saved -and $response.config_valid) {
        Write-Host "`n  ✓ SUCCESS: Configuration is valid and saved!" -ForegroundColor Green
        Write-Host "  ⚠ Connectivity failed as expected (service not running)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ✗ Error: $_" -ForegroundColor Red
}

# Test 6: Test datasource with skip_connectivity=true
Write-Host "`nTest 6: Testing datasource with skip_connectivity=true..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/datasources/test_datasource_fix/test?skip_connectivity=true" -Method Post
    
    Write-Host "  Configuration Valid: $($response.config_valid)" -ForegroundColor $(if ($response.config_valid) { "Green" } else { "Red" })
    Write-Host "  Configuration Saved: $($response.config_saved)" -ForegroundColor $(if ($response.config_saved) { "Green" } else { "Red" })
    Write-Host "  Connectivity Tested: $($response.connectivity_tested)" -ForegroundColor Gray
    Write-Host "  Connectivity Status: $($response.connectivity_status)" -ForegroundColor Gray
    Write-Host "  Message: $($response.message)" -ForegroundColor Gray
    
    if ($response.success -and $response.connectivity_status -eq "skipped") {
        Write-Host "`n  ✓ SUCCESS: Configuration validated without connectivity test!" -ForegroundColor Green
    }
} catch {
    Write-Host "  ✗ Error: $_" -ForegroundColor Red
}

# Cleanup
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Cleanup: Removing test resources..." -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

try {
    Invoke-RestMethod -Uri "$BASE_URL/api/tools/test_http_tool_fix" -Method Delete | Out-Null
    Write-Host "  ✓ Removed test tool" -ForegroundColor Green
} catch {
    Write-Host "  ⚠ Could not remove test tool (may not exist)" -ForegroundColor Yellow
}

try {
    Invoke-RestMethod -Uri "$BASE_URL/api/datasources/test_datasource_fix" -Method Delete | Out-Null
    Write-Host "  ✓ Removed test datasource" -ForegroundColor Green
} catch {
    Write-Host "  ⚠ Could not remove test datasource (may not exist)" -ForegroundColor Yellow
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Testing Complete!" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Summary:" -ForegroundColor White
Write-Host "  • Tools and datasources can be created even if endpoints are unreachable" -ForegroundColor Gray
Write-Host "  • Clear error messages distinguish between config and connectivity issues" -ForegroundColor Gray
Write-Host "  • skip_connectivity parameter allows saving without testing" -ForegroundColor Gray
Write-Host "  • Detailed status fields provide complete information" -ForegroundColor Gray
Write-Host "`n"
