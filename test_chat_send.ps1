# Test Chat Studio Send Endpoint
$body = @{
    message = "Hello, how are you?"
    model_id = "llama3"
    routing_profile = "direct_llm"
    use_memory = $false
    use_tools = $false
} | ConvertTo-Json

Write-Host "Testing Chat Studio Send Endpoint..." -ForegroundColor Cyan
Write-Host "Request Body:" -ForegroundColor Yellow
Write-Host $body

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/chat/ui/send" -Method Post -Body $body -ContentType "application/json"
    Write-Host "`nSuccess!" -ForegroundColor Green
    Write-Host "Response:" -ForegroundColor Yellow
    $response | ConvertTo-Json -Depth 10
} catch {
    Write-Host "`nError!" -ForegroundColor Red
    Write-Host $_.Exception.Message
    Write-Host $_.Exception.Response
}
