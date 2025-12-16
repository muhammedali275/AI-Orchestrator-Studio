# Test script for Routers and Planners API

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Testing Routers & Planners API" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"

# Test 1: List Routers (should be empty initially)
Write-Host "Test 1: GET /api/routers (List Routers)" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/routers" -Method Get
    Write-Host "✓ Success: Found $($response.Count) routers" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 5
} catch {
    Write-Host "✗ Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 2: Create a Router
Write-Host "Test 2: POST /api/routers (Create Router)" -ForegroundColor Yellow
$newRouter = @{
    name = "test_keyword_router"
    type = "keyword"
    enabled = $true
    priority = 10
    rules = @{
        keywords = @{
            churn = "churn_analytics"
            query = "data_query"
            search = "web_search"
        }
        case_sensitive = $false
    }
    description = "Test keyword-based router"
} | ConvertTo-Json -Depth 5

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/routers" -Method Post -Body $newRouter -ContentType "application/json"
    Write-Host "✓ Success: Router created" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 5
} catch {
    Write-Host "✗ Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 3: Get Specific Router
Write-Host "Test 3: GET /api/routers/test_keyword_router (Get Router)" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/routers/test_keyword_router" -Method Get
    Write-Host "✓ Success: Retrieved router" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 5
} catch {
    Write-Host "✗ Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 4: Test Router
Write-Host "Test 4: POST /api/routers/test_keyword_router/test (Test Router)" -ForegroundColor Yellow
$testRequest = @{
    input_text = "Analyze customer churn patterns"
    context = @{}
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/routers/test_keyword_router/test" -Method Post -Body $testRequest -ContentType "application/json"
    Write-Host "✓ Success: Router test completed" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 5
} catch {
    Write-Host "✗ Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 5: List Planners (should be empty initially)
Write-Host "Test 5: GET /api/planners (List Planners)" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/planners" -Method Get
    Write-Host "✓ Success: Found $($response.Count) planners" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 5
} catch {
    Write-Host "✗ Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 6: Create a Planner
Write-Host "Test 6: POST /api/planners (Create Planner)" -ForegroundColor Yellow
$newPlanner = @{
    name = "test_sequential_planner"
    type = "sequential"
    enabled = $true
    strategy = "sequential"
    templates = @{
        churn_analytics = @{
            description = "Plan for churn analysis"
            steps = @(
                @{
                    id = "step_1"
                    action = "data_retrieval"
                    description = "Retrieve customer data"
                },
                @{
                    id = "step_2"
                    action = "analysis"
                    description = "Analyze churn patterns"
                    depends_on = @("step_1")
                }
            )
        }
    }
    description = "Test sequential planner"
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/planners" -Method Post -Body $newPlanner -ContentType "application/json"
    Write-Host "✓ Success: Planner created" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 5
} catch {
    Write-Host "✗ Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 7: Get Specific Planner
Write-Host "Test 7: GET /api/planners/test_sequential_planner (Get Planner)" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/planners/test_sequential_planner" -Method Get
    Write-Host "✓ Success: Retrieved planner" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 5
} catch {
    Write-Host "✗ Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 8: Test Planner
Write-Host "Test 8: POST /api/planners/test_sequential_planner/test (Test Planner)" -ForegroundColor Yellow
$plannerTestRequest = @{
    user_input = "Analyze customer churn"
    intent = "churn_analytics"
    context = @{}
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/planners/test_sequential_planner/test" -Method Post -Body $plannerTestRequest -ContentType "application/json"
    Write-Host "✓ Success: Planner test completed" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 5
} catch {
    Write-Host "✗ Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 9: Get Available Router Types
Write-Host "Test 9: GET /api/routers/types/available" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/routers/types/available" -Method Get
    Write-Host "✓ Success: Retrieved router types" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 5
} catch {
    Write-Host "✗ Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 10: Get Available Planner Types
Write-Host "Test 10: GET /api/planners/types/available" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/planners/types/available" -Method Get
    Write-Host "✓ Success: Retrieved planner types" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 5
} catch {
    Write-Host "✗ Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 11: Check if config files were created
Write-Host "Test 11: Check Persistence Files" -ForegroundColor Yellow
if (Test-Path "backend/orchestrator/config/routers.json") {
    Write-Host "✓ routers.json created" -ForegroundColor Green
    Get-Content "backend/orchestrator/config/routers.json" | Write-Host
} else {
    Write-Host "✗ routers.json not found" -ForegroundColor Red
}

if (Test-Path "backend/orchestrator/config/planners.json") {
    Write-Host "✓ planners.json created" -ForegroundColor Green
    Get-Content "backend/orchestrator/config/planners.json" | Write-Host
} else {
    Write-Host "✗ planners.json not found" -ForegroundColor Red
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Testing Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
