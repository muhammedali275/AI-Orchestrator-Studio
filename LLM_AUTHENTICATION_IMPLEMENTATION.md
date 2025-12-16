# LLM API Key Authentication Implementation

## Overview

Comprehensive API key authentication system for production LLM integration, supporting both cloud APIs (OpenAI, Anthropic, Azure, etc.) and on-premise LLM authentication servers.

## Problem Statement

The system was accepting API keys but not validating or enforcing authentication requirements for production LLM services. Users could accidentally deploy without proper authentication for:
- Cloud LLM services (OpenAI, Anthropic, Cohere, Azure, HuggingFace)
- Remote on-premise LLM servers (vLLM, TextGen WebUI, custom deployments)

## Solution Implemented

### 1. Enhanced LLM Client (`backend/orchestrator/app/clients/llm_client.py`)

#### New Features:
- **Provider Detection**: Automatically detects LLM provider from base URL
- **Authentication Type Detection**: Identifies required authentication method
- **Authentication Validation**: Validates API key format and requirements
- **Security**: Masks API keys in logs and error messages

#### Supported Providers:
**Cloud Providers:**
- OpenAI (api.openai.com)
- Anthropic (api.anthropic.com)
- Azure OpenAI (openai.azure.com)
- Cohere (api.cohere.ai)
- HuggingFace (huggingface.co)

**On-Premise Providers:**
- Ollama (port 11434)
- vLLM (port 8000)
- TextGen WebUI (ports 5000, 7860)
- llama.cpp (port 8080)
- Custom deployments

#### Authentication Types:
```python
class AuthType(Enum):
    NONE = "none"           # No authentication
    BEARER = "bearer"       # Bearer token (most common)
    API_KEY = "api_key"     # X-API-Key header
    BASIC = "basic"         # Basic authentication
    CUSTOM = "custom"       # Custom authentication
```

#### Key Methods:

**`_detect_provider()`**
- Analyzes base URL to identify LLM provider
- Returns LLMProvider enum value

**`_check_auth_required()`**
- Determines if authentication is required
- Cloud providers: ALWAYS required
- Local servers (localhost/127.0.0.1): Optional
- Remote servers: Recommended

**`validate_authentication()`**
- Validates API key is provided when required
- Checks API key format for known providers:
  - OpenAI: Must start with `sk-`
  - Anthropic: Must start with `sk-ant-`
  - Cohere: Minimum length validation
- Returns (is_valid, message) tuple

**`_mask_api_key()`**
- Masks API keys in logs: `sk-1234...7890`
- Prevents accidental exposure in error messages

### 2. New API Endpoints (`backend/orchestrator/app/api/llm.py`)

#### `/api/llm/auth-requirements` (GET)
Get authentication requirements for configured LLM provider.

**Response:**
```json
{
  "requires_auth": true,
  "provider": "openai",
  "auth_type": "bearer",
  "has_api_key": false,
  "is_valid": false,
  "message": "API key is REQUIRED for OPENAI. Please provide a valid API key.",
  "recommendations": [
    "⚠️ CRITICAL: OPENAI requires an API key for production use",
    "📝 Obtain an API key from OPENAI dashboard",
    "🔒 Store API key securely using credential management",
    "💡 OpenAI API keys start with 'sk-'",
    "📊 Monitor usage at https://platform.openai.com/usage"
  ]
}
```

#### `/api/llm/validate-auth` (POST)
Validate authentication configuration with optional test request.

**Response:**
```json
{
  "valid": true,
  "message": "Authentication configured correctly",
  "provider": "openai",
  "auth_type": "bearer",
  "requires_auth": true,
  "test_result": {
    "success": true,
    "message": "Authentication test successful"
  }
}
```

**Error Response (Invalid API Key):**
```json
{
  "valid": false,
  "message": "OpenAI API key should start with 'sk-'",
  "provider": "openai",
  "auth_type": "bearer",
  "requires_auth": true,
  "test_result": null
}
```

### 3. Authentication Recommendations System

Provides context-aware recommendations based on provider and configuration:

**Cloud Providers (Missing API Key):**
- ⚠️ CRITICAL: API key required
- 📝 How to obtain API key
- 🔒 Security best practices
- 💡 API key format requirements
- 📊 Usage monitoring links

**On-Premise Servers (Remote, No Auth):**
- ⚠️ WARNING: Remote server without authentication
- 🔒 Consider adding authentication
- 🛡️ Use reverse proxy with authentication

**Configured Authentication:**
- ✅ Authentication configured
- 🔄 Test before production deployment
- 📝 Document key rotation procedures

## Usage Examples

### Example 1: OpenAI Configuration

```python
# Configuration
settings.llm_base_url = "https://api.openai.com/v1"
settings.llm_api_key = "sk-proj-abc123..."
settings.llm_default_model = "gpt-4"

# Client automatically detects:
# - Provider: OpenAI
# - Auth Type: Bearer
# - Requires Auth: True
# - Validates: API key starts with 'sk-'
```

### Example 2: On-Premise vLLM Server

```python
# Configuration
settings.llm_base_url = "http://192.168.1.100:8000"
settings.llm_api_key = "custom-token-123"
settings.llm_default_model = "llama-2-70b"

# Client automatically detects:
# - Provider: vLLM
# - Auth Type: Bearer
# - Requires Auth: True (remote server)
# - Recommends: Authentication for production
```

### Example 3: Local Ollama

```python
# Configuration
settings.llm_base_url = "http://localhost:11434"
settings.llm_api_key = None
settings.llm_default_model = "llama3:8b"

# Client automatically detects:
# - Provider: Ollama
# - Auth Type: None
# - Requires Auth: False (localhost)
# - Status: Authentication optional
```

## Frontend Integration (To Be Implemented)

### Recommended UI Enhancements:

1. **Real-time Authentication Status**
   - Call `/api/llm/auth-requirements` when URL changes
   - Display provider detection and requirements
   - Show visual warnings for missing authentication

2. **Authentication Validation Button**
   - Separate "Test Authentication" button
   - Calls `/api/llm/validate-auth`
   - Shows detailed validation results

3. **Provider-Specific Help**
   - Display recommendations from API
   - Link to provider documentation
   - Show API key format requirements

4. **Visual Indicators**
   - 🔒 Secure (authenticated cloud/remote)
   - ⚠️ Warning (remote without auth)
   - ✅ OK (local without auth)
   - ❌ Error (cloud without auth)

## Security Features

### 1. API Key Masking
```python
# Original: sk-proj-abc123def456ghi789
# Logged:   sk-p...i789
```

### 2. Validation Before Requests
- Checks authentication before making API calls
- Prevents unnecessary failed requests
- Provides clear error messages

### 3. Provider-Specific Validation
- OpenAI: Validates `sk-` prefix
- Anthropic: Validates `sk-ant-` prefix
- Cohere: Validates minimum length

### 4. Secure Storage Recommendations
- Recommends using credential management system
- Warns against exposing keys in logs
- Documents key rotation procedures

## Production Deployment Checklist

### Cloud LLM Services:
- [ ] API key obtained from provider
- [ ] API key format validated
- [ ] API key stored securely (credential management)
- [ ] Authentication tested successfully
- [ ] Usage monitoring configured
- [ ] Key rotation procedure documented

### On-Premise LLM Servers:
- [ ] Server accessibility verified
- [ ] Authentication method determined
- [ ] API key/token configured (if remote)
- [ ] Network security reviewed
- [ ] Reverse proxy configured (if needed)
- [ ] Authentication tested successfully

### General:
- [ ] Provider correctly detected
- [ ] Authentication requirements understood
- [ ] Test connection successful
- [ ] Error handling verified
- [ ] Logs reviewed (no exposed keys)
- [ ] Production configuration documented

## Testing

### Test Authentication Detection:
```bash
# Get authentication requirements
curl http://localhost:8000/api/llm/auth-requirements

# Expected response shows:
# - Provider detection
# - Authentication requirements
# - Recommendations
```

### Test Authentication Validation:
```bash
# Validate authentication
curl -X POST http://localhost:8000/api/llm/validate-auth

# Expected response shows:
# - Validation result
# - Test request result (if applicable)
# - Detailed feedback
```

### Test with Different Providers:

**OpenAI:**
```bash
# Set configuration
curl -X PUT http://localhost:8000/api/llm/config \
  -H "Content-Type: application/json" \
  -d '{
    "base_url": "https://api.openai.com/v1",
    "api_key": "sk-test-key",
    "default_model": "gpt-4"
  }'

# Check requirements
curl http://localhost:8000/api/llm/auth-requirements
```

**Local Ollama:**
```bash
# Set configuration
curl -X PUT http://localhost:8000/api/llm/config \
  -H "Content-Type: application/json" \
  -d '{
    "base_url": "http://localhost:11434",
    "default_model": "llama3:8b"
  }'

# Check requirements (should show auth optional)
curl http://localhost:8000/api/llm/auth-requirements
```

## Error Handling

### Missing API Key (Cloud Provider):
```json
{
  "valid": false,
  "message": "API key is REQUIRED for OPENAI. Please provide a valid API key.",
  "provider": "openai",
  "requires_auth": true
}
```

### Invalid API Key Format:
```json
{
  "valid": false,
  "message": "OpenAI API key should start with 'sk-'",
  "provider": "openai",
  "requires_auth": true
}
```

### Authentication Test Failed:
```json
{
  "valid": true,
  "message": "Authentication configured correctly",
  "test_result": {
    "success": false,
    "message": "Authentication failed - API key may be invalid",
    "error": "401 Unauthorized: Invalid API key"
  }
}
```

## Benefits

1. **Prevents Production Errors**: Catches missing authentication before deployment
2. **Provider-Aware**: Automatically detects and validates based on provider
3. **Security**: Masks API keys in logs and error messages
4. **User-Friendly**: Provides clear recommendations and error messages
5. **Flexible**: Supports both cloud and on-premise deployments
6. **Comprehensive**: Covers all major LLM providers

## Future Enhancements

1. **Credential Management Integration**: Store API keys in secure credential vault
2. **API Key Rotation**: Automated key rotation with zero downtime
3. **Usage Monitoring**: Track API usage and costs
4. **Multi-Key Support**: Support multiple API keys for load balancing
5. **OAuth Support**: Add OAuth 2.0 authentication for enterprise deployments
6. **Certificate-Based Auth**: Support mTLS for on-premise servers

## Summary

This implementation provides comprehensive API key authentication for both cloud and on-premise LLM services, ensuring:
- ✅ Automatic provider detection
- ✅ Authentication requirement validation
- ✅ API key format validation
- ✅ Security (key masking)
- ✅ Clear error messages and recommendations
- ✅ Production-ready deployment support

The system prevents accidental deployment without proper authentication while remaining flexible for local development scenarios.
