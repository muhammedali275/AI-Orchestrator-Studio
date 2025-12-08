# Test Ollama directly
$messages = @(
    @{
        role = "user"
        content = "Hello, how are you?"
    }
)

$body = @{
    model = "llama3"
    messages = $messages
    stream = $false
} | ConvertTo-Json -Depth 10

Write-Host "Testing Ollama Direct..." -ForegroundColor Cyan
Write-Host "Request Body:" -ForegroundColor Yellow
Write-Host $body

try {
    $response = Invoke-RestMethod -Uri "http://localhost:11434/api/chat" -Method Post -Body $body -ContentType "application/json"
    Write-Host "`nSuccess!" -ForegroundColor Green
    Write-Host "Response:" -ForegroundColor Yellow
    $response | ConvertTo-Json -Depth 10
} catch {
    Write-Host "`nError!" -ForegroundColor Red
    Write-Host $_.Exception.Message
}
