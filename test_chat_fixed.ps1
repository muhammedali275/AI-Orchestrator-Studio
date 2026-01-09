# Test the fixed chat functionality with Ollama
$url = "http://localhost:8000/v1/chat/ui/send"

$payload = @{
    message = "Hello, how are you?"
    model_id = "llama3:8b"
    routing_profile = "direct_llm"
    use_memory = $false
    use_tools = $false
} | ConvertTo-Json

Write-Host "Testing chat endpoint..." -ForegroundColor Cyan
Write-Host "URL: $url"
Write-Host "Payload: $payload"
Write-Host ""

try {
    $response = Invoke-WebRequest -Uri $url -Method POST -Body $payload -ContentType "application/json" -TimeoutSec 120
    
    Write-Host "Status Code: $($response.StatusCode)" -ForegroundColor Green
    
    if ($response.StatusCode -eq 200) {
        Write-Host "`n✓ SUCCESS!" -ForegroundColor Green
        Write-Host "`nResponse:"
        $response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
    }
    else {
        Write-Host "`n✗ FAILED!" -ForegroundColor Red
        Write-Host "Error: $($response.Content)"
    }
}
catch {
    Write-Host "`n✗ ERROR: $($_.Exception.Message)" -ForegroundColor Red
}
