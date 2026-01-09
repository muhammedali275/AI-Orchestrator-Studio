# vLLM External Connection Setup Guide

## Quick Setup

I've configured your system to support external vLLM connections. Here's how to use it:

### 1. Configuration File Location
The LLM connections are stored in:
```
backend/orchestrator/config/llm_connections.json
```

### 2. Current Configuration

**Local Ollama (already working):**
- ID: `llm-1767854937489`
- Name: "Local Ollama"
- URL: `http://localhost:11434`

**External vLLM (newly added):**
- ID: `vllm-external`
- Name: "External vLLM Server"
- URL: `http://your-vllm-server:8000` ← **UPDATE THIS**
- Model: `your-model-name` ← **UPDATE THIS**

### 3. How to Configure Your vLLM Server

Edit `backend/orchestrator/config/llm_connections.json` and update the vLLM connection:

```json
{
  "id": "vllm-external",
  "name": "My vLLM Server",
  "base_url": "http://your-vllm-ip:8000",
  "model": "meta-llama/Llama-2-7b-chat-hf",
  "api_key": "your-api-key-if-needed",
  "timeout": 120,
  "max_tokens": 4096,
  "temperature": 0.7,
  "is_local": false
}
```

**Replace:**
- `your-vllm-ip:8000` → Your actual vLLM server address
- `meta-llama/Llama-2-7b-chat-hf` → Your model name
- `your-api-key-if-needed` → Set to `null` if no auth required

### 4. How to Get Available Models from vLLM

To see what models are available on your vLLM server, run:

```powershell
# Check models endpoint
Invoke-WebRequest -Uri "http://your-vllm-server:8000/v1/models" | Select-Object -ExpandProperty Content | ConvertFrom-Json
```

Or using curl:
```bash
curl http://your-vllm-server:8000/v1/models
```

### 5. Using vLLM in Chat Studio

Once configured:

1. **Restart the backend** to load the new connection:
   ```powershell
   .\start-backend.bat
   ```

2. **In Chat Studio UI:**
   - You'll see a dropdown to select your LLM connection
   - Choose "External vLLM Server"
   - The models from that server will be listed
   - Start chatting!

### 6. API Compatibility

vLLM uses **OpenAI-compatible API**, so the system will automatically:
- Use `/v1/chat/completions` endpoint
- Send messages in OpenAI format
- Handle streaming responses
- Parse OpenAI-style responses

### 7. Testing Your vLLM Connection

Test your vLLM server is accessible:

```powershell
# Test health endpoint
Invoke-WebRequest -Uri "http://your-vllm-server:8000/health"

# Test with a simple completion
$body = @{
    model = "your-model-name"
    messages = @(
        @{
            role = "user"
            content = "Hello, how are you?"
        }
    )
    max_tokens = 100
} | ConvertTo-Json -Depth 5

Invoke-WebRequest -Uri "http://your-vllm-server:8000/v1/chat/completions" `
    -Method POST `
    -Body $body `
    -ContentType "application/json" | Select-Object -ExpandProperty Content
```

### 8. Multiple Connections

You can add as many LLM connections as you want! Just add more entries to the `connections` array:

```json
{
  "connections": [
    { "id": "ollama-local", ... },
    { "id": "vllm-prod", ... },
    { "id": "vllm-dev", ... },
    { "id": "openai-gpt4", ... }
  ]
}
```

Each connection appears as a selectable option in the Chat Studio UI.

### 9. Authentication (if needed)

If your vLLM server requires authentication:

```json
{
  "id": "vllm-external",
  "base_url": "http://your-vllm-server:8000",
  "api_key": "your-bearer-token-here",
  ...
}
```

The system will automatically add it as `Authorization: Bearer your-bearer-token-here`

### 10. Troubleshooting

**Connection refused:**
- Check firewall rules
- Verify vLLM server is running
- Test with curl/Invoke-WebRequest first

**404 errors:**
- vLLM uses `/v1/chat/completions` (OpenAI compatible)
- Verify your vLLM server has this endpoint

**No models showing:**
- Check `/v1/models` endpoint on your server
- Verify model name matches what vLLM reports

**Timeouts:**
- Increase `timeout` value in config
- Check network latency to remote server

---

## Next Steps

1. Get your vLLM server URL and model name
2. Update `backend/orchestrator/config/llm_connections.json`
3. Restart backend: `.\start-backend.bat`
4. Open Chat Studio and select your vLLM connection
5. Start chatting!

The system automatically handles:
- ✓ Endpoint detection (Ollama vs vLLM vs OpenAI)
- ✓ Request format conversion
- ✓ Streaming responses
- ✓ Error handling
- ✓ Multiple concurrent connections
