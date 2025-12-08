# Test script for Tools & Data Sources functionality
# Run this after starting the backend to verify all fixes

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Tools & Data Sources Test Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"

# Test 1: List Tools (should return empty array initially)
Write-Host "Test 1: Listing Tools..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/tools" -Method Get
    Write-Host "✓ Success: Retrieved tools list" -ForegroundColor Green
    Write-Host "  Tools count: $($response.Count)" -ForegroundColor Gray
} catch {
    Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 2: List Datasources (should return empty array initially)
Write-Host "Test 2: Listing Datasources..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/datasources" -Method Get
    Write-Host "✓ Success: Retrieved datasources list" -ForegroundColor Green
    Write-Host "  Datasources count: $($response.Count)" -ForegroundColor Gray
} catch {
    Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 3: Create HTTP Request Tool
Write-Host "Test 3: Creating HTTP Request Tool..." -ForegroundColor Yellow
$toolData = @{
    name = "github_api"
    type = "http_request"
    enabled = $true
    description = "GitHub API tool for testing"
    config = @{
        base_url = "https://api.github.com"
        timeout = "30"
    }
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/tools" -Method Post -Body $toolData -ContentType "application/json"
    Write-Host "✓ Success: Created tool 'github_api'" -ForegroundColor Green
    Write-Host "  Response: $($response.message)" -ForegroundColor Gray
} catch {
    if ($_.Exception.Response.StatusCode -eq 409) {
        Write-Host "⚠ Tool already exists (this is OK)" -ForegroundColor Yellow
    } else {
        Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}
Write-Host ""

# Test 4: Get Specific Tool
Write-Host "Test 4: Getting Tool Details..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/tools/github_api" -Method Get
    Write-Host "✓ Success: Retrieved tool details" -ForegroundColor Green
    Write-Host "  Name: $($response.name)" -ForegroundColor Gray
    Write-Host "  Type: $($response.type)" -ForegroundColor Gray
    Write-Host "  Enabled: $($response.enabled)" -ForegroundColor Gray
} catch {
    Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 5: Test Tool Connection
Write-Host "Test 5: Testing Tool Connection..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/tools/github_api/test" -Method Post -Body "{}" -ContentType "application/json"
    Write-Host "✓ Success: Tool test completed" -ForegroundColor Green
    Write-Host "  Success: $($response.success)" -ForegroundColor Gray
    Write-Host "  Message: $($response.message)" -ForegroundColor Gray
} catch {
    Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 6: Create Datasource
Write-Host "Test 6: Creating Datasource..." -ForegroundColor Yellow
$dsData = @{
    name = "test_api"
    type = "api"
    url = "https://jsonplaceholder.typicode.com"
    timeout_seconds = 30
    enabled = $true
    config = @{}
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/datasources" -Method Post -Body $dsData -ContentType "application/json"
    Write-Host "✓ Success: Created datasource 'test_api'" -ForegroundColor Green
    Write-Host "  Response: $($response.message)" -ForegroundColor Gray
} catch {
    if ($_.Exception.Response.StatusCode -eq 409) {
        Write-Host "⚠ Datasource already exists (this is OK)" -ForegroundColor Yellow
    } else {
        Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}
Write-Host ""

# Test 7: Get Specific Datasource
Write-Host "Test 7: Getting Datasource Details..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/datasources/test_api" -Method Get
    Write-Host "✓ Success: Retrieved datasource details" -ForegroundColor Green
    Write-Host "  Name: $($response.name)" -ForegroundColor Gray
    Write-Host "  Type: $($response.type)" -ForegroundColor Gray
    Write-Host "  URL: $($response.url)" -ForegroundColor Gray
} catch {
    Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 8: Test Datasource Connection
Write-Host "Test 8: Testing Datasource Connection..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/datasources/test_api/test" -Method Post -Body "{}" -ContentType "application/json"
    Write-Host "✓ Success: Datasource test completed" -ForegroundColor Green
    Write-Host "  Success: $($response.success)" -ForegroundColor Gray
    Write-Host "  Message: $($response.message)" -ForegroundColor Gray
} catch {
    Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 9: Get Tool Types
Write-Host "Test 9: Getting Available Tool Types..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/tools/types/available" -Method Get
    Write-Host "✓ Success: Retrieved tool types" -ForegroundColor Green
    Write-Host "  Available types:" -ForegroundColor Gray
    foreach ($type in $response.tool_types) {
        Write-Host "    - $($type.type): $($type.description)" -ForegroundColor Gray
    }
} catch {
    Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "All tests completed!" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Open the frontend: http://localhost:3000" -ForegroundColor White
Write-Host "2. Navigate to 'Tools & Data Sources' page" -ForegroundColor White
Write-Host "3. Verify the created tool and datasource appear" -ForegroundColor White
Write-Host "4. Try creating new tools with different types" -ForegroundColor White
Write-Host "5. Test the connection buttons" -ForegroundColor White
Write-Host "6. Try the 'Test Query' feature for datasources" -ForegroundColor White
Write-Host ""
