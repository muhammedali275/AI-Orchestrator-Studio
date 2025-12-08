# Credential Management System - Implementation Guide

## Overview

The ZainOne Orchestrator Studio now includes a secure credential management system that allows storing and managing authentication credentials for all targets (LLMs, agents, databases, data sources, etc.) through the GUI.

## Security Features

✅ **Encrypted Storage**: All secrets are encrypted using Fernet (AES-128) before storage  
✅ **No Plain Text**: Credentials are NEVER stored in plain text  
✅ **No API Exposure**: Secrets are NEVER returned in API responses  
✅ **No Logging**: Secrets are NEVER logged  
✅ **Master Key**: Encryption key stored only in environment variable  
✅ **Multiple Types**: Supports SSH, HTTP Basic, Bearer Token, DB DSN, API Key, and custom types  

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         GUI Layer                            │
│  (Create/Update/Delete Credentials, Link to Targets)        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Layer                               │
│  /api/credentials (CRUD endpoints)                          │
│  - POST /api/credentials (create)                           │
│  - GET /api/credentials (list)                              │
│  - GET /api/credentials/{id} (get)                          │
│  - PUT /api/credentials/{id} (update/rotate)                │
│  - DELETE /api/credentials/{id} (deactivate)                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer                             │
│  CredentialsService (business logic)                        │
│  - Validates inputs                                          │
│  - Encrypts secrets before storage                           │
│  - Decrypts secrets for internal use only                    │
│  - Returns metadata only to API                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   Security Layer                             │
│  Encryption/Decryption utilities                            │
│  - get_crypto_key() - reads ORCH_CRED_KEY from env         │
│  - encrypt_secret() - encrypts using Fernet                 │
│  - decrypt_secret() - decrypts using Fernet                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   Database Layer                             │
│  Credential Model (SQLAlchemy)                              │
│  - id, name, type, username, secret (encrypted), extra      │
│  - PostgreSQL or SQLite                                      │
└─────────────────────────────────────────────────────────────┘
```

## Setup Instructions

### 1. Generate Encryption Key

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

This will output something like:
```
xK8vZ9mN2pQ4rT6wY8aB1cD3eF5gH7iJ9kL0mN2oP4qR6sT8uV0wX2yZ4=
```

### 2. Configure Environment

Add to your `.env` file:

```env
# Credential Encryption Key
ORCH_CRED_KEY=xK8vZ9mN2pQ4rT6wY8aB1cD3eF5gH7iJ9kL0mN2oP4qR6sT8uV0wX2yZ4=
```

**CRITICAL SECURITY NOTES:**
- NEVER commit this key to version control
- NEVER share this key
- Use different keys for dev/staging/production
- Store securely in production (AWS Secrets Manager, Azure Key Vault, etc.)
- If key is lost, all encrypted credentials are unrecoverable

### 3. Install Dependencies

```bash
cd backend/orchestrator
pip install -r requirements.txt
```

New dependencies added:
- `cryptography==41.0.7` - For Fernet encryption
- `sqlalchemy==2.0.23` - For ORM
- `alembic==1.13.0` - For database migrations

### 4. Initialize Database

The database tables are automatically created on application startup.

For PostgreSQL:
```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=orchestrator
POSTGRES_PASSWORD=your_password
POSTGRES_DATABASE=orchestrator_db
```

For SQLite (development):
- If no PostgreSQL configured, SQLite is used automatically
- Database file: `credentials.db` in the application directory

### 5. Start the Application

```bash
cd backend/orchestrator
python -m app.main
```

Or use the startup script:
```bash
start-backend.bat
```

## API Usage

### Create Credential

```bash
POST /api/credentials
Content-Type: application/json

{
  "name": "Production PostgreSQL",
  "type": "db_dsn",
  "username": "admin",
  "secret": "my_secure_password_123",
  "extra": {
    "host": "db.example.com",
    "port": 5432,
    "database": "prod_db"
  }
}
```

Response (secret is NOT returned):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Production PostgreSQL",
  "type": "db_dsn",
  "username": "admin",
  "extra": {
    "host": "db.example.com",
    "port": 5432,
    "database": "prod_db"
  },
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z",
  "is_active": true
}
```

### List Credentials

```bash
GET /api/credentials?active_only=true
```

Response:
```json
{
  "credentials": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Production PostgreSQL",
      "type": "db_dsn",
      "username": "admin",
      "extra": {...},
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-01-15T10:30:00Z",
      "is_active": true
    }
  ],
  "total": 1
}
```

### Update/Rotate Credential

```bash
PUT /api/credentials/550e8400-e29b-41d4-a716-446655440000
Content-Type: application/json

{
  "secret": "new_rotated_password_456"
}
```

### Delete Credential

```bash
DELETE /api/credentials/550e8400-e29b-41d4-a716-446655440000
```

## Credential Types

### 1. SSH Credentials
```json
{
  "name": "Production Server SSH",
  "type": "ssh",
  "username": "ubuntu",
  "secret": "ssh_private_key_content_or_password",
  "extra": {
    "host": "server.example.com",
    "port": 22,
    "auth_method": "key"
  }
}
```

### 2. HTTP Basic Auth
```json
{
  "name": "API Basic Auth",
  "type": "http_basic",
  "username": "api_user",
  "secret": "api_password",
  "extra": {
    "base_url": "https://api.example.com"
  }
}
```

### 3. Bearer Token
```json
{
  "name": "GitHub API Token",
  "type": "bearer_token",
  "secret": "ghp_xxxxxxxxxxxxxxxxxxxx",
  "extra": {
    "api_url": "https://api.github.com"
  }
}
```

### 4. Database DSN
```json
{
  "name": "Production Database",
  "type": "db_dsn",
  "username": "db_admin",
  "secret": "db_password",
  "extra": {
    "host": "db.example.com",
    "port": 5432,
    "database": "prod_db",
    "driver": "postgresql"
  }
}
```

### 5. API Key
```json
{
  "name": "OpenAI API Key",
  "type": "api_key",
  "secret": "sk-xxxxxxxxxxxxxxxxxxxx",
  "extra": {
    "provider": "openai",
    "model": "gpt-4"
  }
}
```

### 6. Custom
```json
{
  "name": "Custom Service Credential",
  "type": "custom",
  "username": "service_account",
  "secret": "custom_secret_value",
  "extra": {
    "service_type": "custom_api",
    "endpoint": "https://custom.example.com"
  }
}
```

## Integration with Targets

### Next Steps (Phase 4-5)

The configuration models need to be updated to reference credentials:

```python
class LLMConfig(BaseModel):
    base_url: str
    default_model: str
    credential_id: Optional[str]  # Link to credential

class DataSourceConfig(BaseModel):
    name: str
    url: str
    credential_id: Optional[str]  # Link to credential

class ExternalAgentConfig(BaseModel):
    name: str
    url: str
    credential_id: Optional[str]  # Link to credential
```

Clients will use credentials like this:

```python
# In LLM client
if config.credential_id:
    cred = credentials_service.get_credential_for_use(config.credential_id)
    if cred["type"] == "bearer_token":
        headers["Authorization"] = f"Bearer {cred['secret']}"
    elif cred["type"] == "http_basic":
        auth = (cred["username"], cred["secret"])
```

## GUI Integration

The frontend should:

1. **Credential Management Page**:
   - List all credentials (without secrets)
   - Create new credentials
   - Edit/rotate credentials
   - Delete/deactivate credentials
   - Test credential connectivity

2. **Target Configuration Pages**:
   - Show dropdown of available credentials
   - Allow linking credential to target
   - Show credential name (not secret) when linked

3. **Security Indicators**:
   - Show lock icon for secured targets
   - Show warning for targets without credentials
   - Show last rotation date

## Security Best Practices

### DO:
✅ Generate unique encryption keys for each environment  
✅ Store keys in secure secret management systems  
✅ Rotate credentials regularly  
✅ Use least-privilege credentials  
✅ Monitor credential usage  
✅ Audit credential access  

### DON'T:
❌ Commit encryption keys to version control  
❌ Share encryption keys  
❌ Log decrypted secrets  
❌ Return secrets in API responses  
❌ Store secrets in plain text  
❌ Use the same key across environments  

## Troubleshooting

### Error: "Credential encryption key not configured"

**Solution**: Set `ORCH_CRED_KEY` in your `.env` file

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Copy output to .env
```

### Error: "Invalid credential encryption key format"

**Solution**: The key must be a valid Fernet key (44 bytes, base64-encoded). Generate a new one.

### Error: "Failed to decrypt secret: Invalid encryption key or corrupted data"

**Causes**:
- Wrong encryption key
- Key was changed after credentials were encrypted
- Database corruption

**Solution**: 
- Verify `ORCH_CRED_KEY` is correct
- If key was lost, credentials must be recreated

### Database Connection Issues

**For PostgreSQL**:
```bash
# Test connection
psql -h localhost -U orchestrator -d orchestrator_db
```

**For SQLite**:
- Check file permissions on `credentials.db`
- Ensure directory is writable

## Migration from Plain Text

If you have existing configurations with plain text credentials:

1. Create credentials via API for each target
2. Update target configurations to reference credential IDs
3. Remove plain text credentials from configs
4. Restart application

## Monitoring

Check credential usage in logs:
```
[INFO] Created credential: Production PostgreSQL (type: db_dsn)
[INFO] Updated credential: Production PostgreSQL
[INFO] Rotated secret for credential: Production PostgreSQL
```

## Support

For issues or questions:
- Check logs for detailed error messages
- Verify environment configuration
- Ensure database is accessible
- Confirm encryption key is valid

## Files Created

```
backend/orchestrator/app/
├── db/
│   ├── __init__.py
│   ├── database.py          # Database connection
│   └── models.py            # Credential model
├── security/
│   ├── __init__.py
│   └── credentials.py       # Encryption utilities
├── services/
│   ├── __init__.py
│   └── credentials_service.py  # Business logic
└── api/
    └── credentials.py       # REST API endpoints
```

## Next Implementation Steps

1. ✅ Phase 1-3: Core credential system (COMPLETE)
2. ⏳ Phase 4: Update config models to reference credentials
3. ⏳ Phase 5: Update clients to use credentials
4. ⏳ Phase 6: Update monitoring to use credentials
5. ⏳ Frontend integration

---

**Version**: 1.0.0  
**Last Updated**: 2025-01-15  
**Status**: Core Implementation Complete
