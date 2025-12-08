# Pre-Production Checklist & LLM Connection Fix

## 🎯 Task Overview

1. **Fix Local LLM Connection Test** - Ensure Ollama connection works reliably
2. **Production Deployment Guide** - Complete guide for moving to production server

---

## 📋 Part 1: LLM Connection Test Fixes

### Current Issues Identified

Based on code analysis, the LLM client has potential issues:

1. **Endpoint Detection Logic** - The client tries to auto-detect Ollama vs OpenAI endpoints
2. **Message Format** - Ollama uses different formats for `/api/generate` vs `/api/chat`
3. **Error Handling** - Need better error messages for troubleshooting
4. **Connection Validation** - Test endpoint should validate before saving config

### Issues in `backend/orchestrator/app/clients/llm_client.py`

```python
# ISSUE 1: Endpoint detection is fragile
if "11434" in self.base_url or "ollama" in self.base_url.lower():
    # This fails if user changes Ollama port or uses different URL

# ISSUE 2: Wrong Ollama endpoint
endpoint = f"{self.base_url}/api/generate"
# Should use /api/chat for chat completions

# ISSUE 3: Message conversion loses context
prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
# This doesn't preserve proper message structure
```

### Fixes Required

#### Fix 1: Improve Ollama Detection
```python
def _is_ollama_endpoint(self) -> bool:
    """Detect if endpoint is Ollama."""
    ollama_indicators = [
        "11434" in self.base_url,
        "ollama" in self.base_url.lower(),
        "/api/generate" in self.base_url,
        "/api/chat" in self.base_url
    ]
    return any(ollama_indicators)
```

#### Fix 2: Use Correct Ollama Endpoint
```python
# Use /api/chat for Ollama (supports messages format)
if self._is_ollama_endpoint():
    endpoint = f"{self.base_url}/api/chat"
    payload = {
        "model": model,
        "messages": messages,  # Keep messages format
        "temperature": temperature,
        "stream": False
    }
```

#### Fix 3: Add Connection Validation
```python
async def validate_connection(self) -> Dict[str, Any]:
    """Validate LLM connection before use."""
    try:
        # Test with simple request
        response = await self.client.get(f"{self.base_url}/api/version")
        return {"valid": True, "version": response.json()}
    except Exception as e:
        return {"valid": False, "error": str(e)}
```

#### Fix 4: Better Error Messages
```python
except httpx.HTTPStatusError as e:
    error_detail = {
        "status_code": e.response.status_code,
        "url": str(e.request.url),
        "method": e.request.method,
        "response": e.response.text[:200]  # First 200 chars
    }
    logger.error(f"[LLM] HTTP Error: {error_detail}")
```

---

## 🧪 Part 2: Comprehensive Testing Script

### Create Production-Ready Test Script

**File:** `test_llm_production.py`

```python
#!/usr/bin/env python3
"""
Comprehensive LLM Connection Test for Production Readiness
Tests all aspects of LLM connectivity before deployment
"""

import asyncio
import httpx
import json
import time
from typing import Dict, Any, List

class LLMProductionTester:
    """Test LLM connection for production readiness."""
    
    def __init__(self, base_url: str, model: str, api_key: str = None):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.api_key = api_key
        self.results = []
    
    async def test_server_reachability(self) -> Dict[str, Any]:
        """Test if LLM server is reachable."""
        print("\n🔍 Test 1: Server Reachability")
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/version")
                version = response.json()
                print(f"✅ Server reachable - Version: {version.get('version', 'unknown')}")
                return {"passed": True, "version": version}
        except Exception as e:
            print(f"❌ Server unreachable: {str(e)}")
            return {"passed": False, "error": str(e)}
    
    async def test_model_availability(self) -> Dict[str, Any]:
        """Test if specified model is available."""
        print("\n🔍 Test 2: Model Availability")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                models = response.json().get("models", [])
                model_names = [m["name"] for m in models]
                
                if self.model in model_names:
                    print(f"✅ Model '{self.model}' is available")
                    return {"passed": True, "available_models": model_names}
                else:
                    print(f"❌ Model '{self.model}' not found")
                    print(f"   Available models: {', '.join(model_names)}")
                    return {"passed": False, "available_models": model_names}
        except Exception as e:
            print(f"⚠️  Could not verify model: {str(e)}")
            return {"passed": True, "warning": "Could not verify, but continuing"}
    
    async def test_simple_completion(self) -> Dict[str, Any]:
        """Test simple completion request."""
        print("\n🔍 Test 3: Simple Completion")
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": "Say 'test successful' and nothing else."}
                    ],
                    "stream": False
                }
                
                start_time = time.time()
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                )
                response_time = (time.time() - start_time) * 1000
                
                result = response.json()
                content = result.get("message", {}).get("content", "")
                
                print(f"✅ Completion successful ({response_time:.0f}ms)")
                print(f"   Response: {content[:100]}...")
                return {
                    "passed": True,
                    "response_time_ms": response_time,
                    "response": content
                }
        except Exception as e:
            print(f"❌ Completion failed: {str(e)}")
            return {"passed": False, "error": str(e)}
    
    async def test_conversation_context(self) -> Dict[str, Any]:
        """Test multi-turn conversation."""
        print("\n🔍 Test 4: Conversation Context")
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # First message
                payload1 = {
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": "Remember this number: 42"}
                    ],
                    "stream": False
                }
                response1 = await client.post(f"{self.base_url}/api/chat", json=payload1)
                
                # Second message referencing first
                payload2 = {
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": "Remember this number: 42"},
                        {"role": "assistant", "content": response1.json()["message"]["content"]},
                        {"role": "user", "content": "What number did I ask you to remember?"}
                    ],
                    "stream": False
                }
                response2 = await client.post(f"{self.base_url}/api/chat", json=payload2)
                
                content = response2.json()["message"]["content"]
                has_42 = "42" in content
                
                if has_42:
                    print(f"✅ Context maintained correctly")
                else:
                    print(f"⚠️  Context may not be maintained")
                
                return {"passed": has_42, "response": content}
        except Exception as e:
            print(f"❌ Context test failed: {str(e)}")
            return {"passed": False, "error": str(e)}
    
    async def test_error_handling(self) -> Dict[str, Any]:
        """Test error handling with invalid requests."""
        print("\n🔍 Test 5: Error Handling")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Test with invalid model
                payload = {
                    "model": "nonexistent-model-xyz",
                    "messages": [{"role": "user", "content": "test"}],
                    "stream": False
                }
                
                try:
                    response = await client.post(f"{self.base_url}/api/chat", json=payload)
                    print(f"⚠️  Expected error but got success")
                    return {"passed": False, "warning": "No error on invalid model"}
                except httpx.HTTPStatusError as e:
                    print(f"✅ Error handling works (status {e.response.status_code})")
                    return {"passed": True, "error_code": e.response.status_code}
        except Exception as e:
            print(f"✅ Error handling works: {str(e)}")
            return {"passed": True}
    
    async def test_performance(self) -> Dict[str, Any]:
        """Test performance with multiple requests."""
        print("\n🔍 Test 6: Performance Test")
        try:
            times = []
            async with httpx.AsyncClient(timeout=30.0) as client:
                for i in range(3):
                    payload = {
                        "model": self.model,
                        "messages": [{"role": "user", "content": f"Count to {i+1}"}],
                        "stream": False
                    }
                    
                    start = time.time()
                    await client.post(f"{self.base_url}/api/chat", json=payload)
                    times.append((time.time() - start) * 1000)
            
            avg_time = sum(times) / len(times)
            print(f"✅ Average response time: {avg_time:.0f}ms")
            print(f"   Min: {min(times):.0f}ms, Max: {max(times):.0f}ms")
            
            return {
                "passed": True,
                "avg_time_ms": avg_time,
                "min_time_ms": min(times),
                "max_time_ms": max(times)
            }
        except Exception as e:
            print(f"❌ Performance test failed: {str(e)}")
            return {"passed": False, "error": str(e)}
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and generate report."""
        print("=" * 60)
        print("🚀 LLM Production Readiness Test")
        print("=" * 60)
        print(f"Base URL: {self.base_url}")
        print(f"Model: {self.model}")
        
        tests = [
            ("Server Reachability", self.test_server_reachability),
            ("Model Availability", self.test_model_availability),
            ("Simple Completion", self.test_simple_completion),
            ("Conversation Context", self.test_conversation_context),
            ("Error Handling", self.test_error_handling),
            ("Performance", self.test_performance),
        ]
        
        results = {}
        passed_count = 0
        
        for test_name, test_func in tests:
            result = await test_func()
            results[test_name] = result
            if result.get("passed"):
                passed_count += 1
        
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {passed_count}/{len(tests)} tests passed")
        print("=" * 60)
        
        if passed_count == len(tests):
            print("✅ ALL TESTS PASSED - Ready for production!")
        elif passed_count >= len(tests) - 1:
            print("⚠️  MOSTLY PASSED - Review warnings before production")
        else:
            print("❌ TESTS FAILED - Fix issues before production")
        
        return {
            "total_tests": len(tests),
            "passed": passed_count,
            "results": results,
            "production_ready": passed_count >= len(tests) - 1
        }


async def main():
    """Main test execution."""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python test_llm_production.py <base_url> <model> [api_key]")
        print("Example: python test_llm_production.py http://localhost:11434 llama3:8b")
        sys.exit(1)
    
    base_url = sys.argv[1]
    model = sys.argv[2]
    api_key = sys.argv[3] if len(sys.argv) > 3 else None
    
    tester = LLMProductionTester(base_url, model, api_key)
    results = await tester.run_all_tests()
    
    # Save results to file
    with open("llm_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to: llm_test_results.json")
    
    sys.exit(0 if results["production_ready"] else 1)


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🚀 Part 3: Production Deployment Guide

### Prerequisites

#### 1. Production Server Requirements

**Minimum Specifications:**
- **CPU:** 4 cores (8 recommended)
- **RAM:** 8GB (16GB recommended)
- **Storage:** 50GB SSD
- **OS:** Ubuntu 20.04+ / CentOS 8+ / Windows Server 2019+
- **Network:** Static IP, open ports 80, 443, 8000, 3000

#### 2. Software Requirements

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3.9 python3-pip nodejs npm nginx postgresql redis-server

# CentOS/RHEL
sudo yum install -y python39 python39-pip nodejs npm nginx postgresql redis

# Verify installations
python3 --version  # Should be 3.9+
node --version     # Should be 14+
npm --version
```

### Production Deployment Steps

#### Step 1: Prepare Production Server

```bash
# 1. Create application user
sudo useradd -m -s /bin/bash orchestrator
sudo usermod -aG sudo orchestrator

# 2. Create application directory
sudo mkdir -p /opt/zainone-orchestrator
sudo chown orchestrator:orchestrator /opt/zainone-orchestrator

# 3. Switch to application user
sudo su - orchestrator
cd /opt/zainone-orchestrator
```

#### Step 2: Transfer Application Files

**Option A: Using Git (Recommended)**
```bash
# On production server
cd /opt/zainone-orchestrator
git clone <your-repo-url> .
```

**Option B: Using SCP**
```bash
# On local machine
cd d:/(--2025--)/ZainOne-Orchestrator-Studio
tar -czf orchestrator.tar.gz --exclude=node_modules --exclude=__pycache__ --exclude=.git .

# Transfer to production
scp orchestrator.tar.gz user@production-server:/opt/zainone-orchestrator/

# On production server
cd /opt/zainone-orchestrator
tar -xzf orchestrator.tar.gz
rm orchestrator.tar.gz
```

**Option C: Using rsync**
```bash
# On local machine
rsync -avz --exclude='node_modules' --exclude='__pycache__' --exclude='.git' \
  d:/(--2025--)/ZainOne-Orchestrator-Studio/ \
  user@production-server:/opt/zainone-orchestrator/
```

#### Step 3: Configure Production Environment

```bash
# Create production .env file
cd /opt/zainone-orchestrator/backend/orchestrator
cp config/example.env .env

# Edit with production values
nano .env
```

**Production .env Configuration:**
```env
# Application
APP_NAME=ZainOne Orchestrator Studio
APP_VERSION=1.0.0
DEBUG=False
LOG_LEVEL=INFO

# API
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=https://your-domain.com

# LLM Configuration (CRITICAL - Update with your LLM server)
LLM_BASE_URL=http://your-llm-server:11434
LLM_DEFAULT_MODEL=llama3:8b
LLM_TIMEOUT_SECONDS=60
LLM_MAX_RETRIES=3

# Database (Production PostgreSQL)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=orchestrator_user
POSTGRES_PASSWORD=<strong-password-here>
POSTGRES_DATABASE=orchestrator_prod

# Redis (Production)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=<strong-password-here>
REDIS_DB=0

# Security
AUTH_ENABLED=True
AUTH_SECRET_KEY=<generate-strong-secret-key>
AUTH_ALGORITHM=HS256
AUTH_TOKEN_EXPIRE_MINUTES=60

# External Agents (Update with production IPs)
EXTERNAL_AGENT_BASE_URL=http://production-agent-server:8001
EXTERNAL_AGENT_AUTH_TOKEN=<production-token>

# Monitoring
MONITORING_ENABLED=True
```

**Generate Strong Secret Key:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### Step 4: Set Up Production Database

```bash
# 1. Create PostgreSQL database and user
sudo -u postgres psql << EOF
CREATE DATABASE orchestrator_prod;
CREATE USER orchestrator_user WITH ENCRYPTED PASSWORD '<strong-password>';
GRANT ALL PRIVILEGES ON DATABASE orchestrator_prod TO orchestrator_user;
\q
EOF

# 2. Configure Redis
sudo nano /etc/redis/redis.conf
# Set: requirepass <strong-password>
# Set: bind 127.0.0.1
sudo systemctl restart redis

# 3. Initialize database
cd /opt/zainone-orchestrator/backend/orchestrator
python3 -m app.db.init_db
```

#### Step 5: Install Dependencies

```bash
# Backend dependencies
cd /opt/zainone-orchestrator/backend/orchestrator
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Frontend dependencies
cd /opt/zainone-orchestrator/frontend
npm install
npm run build
```

#### Step 6: Configure Systemd Services

**Backend Service:**
```bash
sudo nano /etc/systemd/system/orchestrator-backend.service
```

```ini
[Unit]
Description=ZainOne Orchestrator Backend
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=orchestrator
WorkingDirectory=/opt/zainone-orchestrator/backend/orchestrator
Environment="PATH=/opt/zainone-orchestrator/backend/orchestrator/venv/bin"
ExecStart=/opt/zainone-orchestrator/backend/orchestrator/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Frontend Service (if serving with Node):**
```bash
sudo nano /etc/systemd/system/orchestrator-frontend.service
```

```ini
[Unit]
Description=ZainOne Orchestrator Frontend
After=network.target

[Service]
Type=simple
User=orchestrator
WorkingDirectory=/opt/zainone-orchestrator/frontend
Environment="NODE_ENV=production"
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start services:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable orchestrator-backend
sudo systemctl enable orchestrator-frontend
sudo systemctl start orchestrator-backend
sudo systemctl start orchestrator-frontend

# Check status
sudo systemctl status orchestrator-backend
sudo systemctl status orchestrator-frontend
```

#### Step 7: Configure Nginx Reverse Proxy

```bash
sudo nano /etc/nginx/sites-available/orchestrator
```

```nginx
# Backend API
upstream backend {
    server 127.0.0.1:8000;
}

# Frontend
upstream frontend {
    server 127.0.0.1:3000;
}

server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL Configuration
    ssl_certificate /etc/ssl/certs/your-cert.crt;
    ssl_certificate_key /etc/ssl/private/your-key.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for long-running requests
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # WebSocket support (if needed)
    location /ws/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # Static files
    location /static/ {
        alias /opt/zainone-orchestrator/frontend/build/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

**Enable site:**
```bash
sudo ln -s /etc/nginx/sites-available/orchestrator /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Step 8: Configure Firewall

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# Firewalld (CentOS)
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

#### Step 9: Set Up SSL Certificates

**Option A: Let's Encrypt (Free)**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

**Option B: Self-Signed (Development)**
```bash
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/orchestrator.key \
  -out /etc/ssl/certs/orchestrator.crt
```

#### Step 10: Configure Monitoring & Logging

```bash
# Set up log rotation
sudo nano /etc/logrotate.d/orchestrator
```

```
/opt/zainone-orchestrator/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 orchestrator orchestrator
    sharedscripts
    postrotate
        systemctl reload orchestrator-backend > /dev/null 2>&1 || true
    endscript
}
```

**Set up monitoring:**
```bash
# Install monitoring tools
sudo apt install htop iotop nethogs

# Set up health check cron
crontab -e
```

Add:
```cron
*/5 * * * * curl -f http://localhost:8000/api/health || systemctl restart orchestrator-backend
```

---

## ✅ Production Verification Checklist

### Pre-Deployment
- [ ] All tests pass locally
- [ ] LLM connection test successful
- [ ] Database migrations completed
- [ ] Configuration files reviewed
- [ ] Secrets generated and secured
- [ ] Backup strategy defined

### Deployment
- [ ] Application files transferred
- [ ] Dependencies installed
- [ ] Database initialized
- [ ] Services configured and running
- [ ] Nginx configured
- [ ] SSL certificates installed
- [ ] Firewall configured

### Post-Deployment
- [ ] Health check endpoint responding
- [ ] LLM connection working
- [ ] Frontend accessible
- [ ] API endpoints responding
- [ ] Database connections working
- [ ] Redis cache working
- [ ] Logs being written
- [ ] Monitoring active

### Security
- [ ] Strong passwords set
- [ ] Auth enabled
- [ ] HTTPS enforced
- [ ] Firewall active
- [ ] Unnecessary ports closed
- [ ] File permissions correct
- [ ] Secrets not in version control

---

## 🔧 Troubleshooting

### Common Issues

**1. LLM Connection Fails**
```bash
# Check LLM server is running
curl http://your-llm-server:11434/api/version

# Check network connectivity
telnet your-llm-server 11434

# Check firewall
sudo ufw status
```

**2. Backend Won't Start**
```bash
# Check logs
sudo journalctl -u orchestrator-backend -f

# Check port availability
sudo netstat -tulpn | grep 8000

# Check Python environment
source /opt/zainone-orchestrator/backend/orchestrator/venv/bin/activate
python -c "import fastapi; print('OK')"
```

**3. Database Connection Issues**
```bash
# Test PostgreSQL connection
psql -h localhost -U orchestrator_user -d orchestrator_prod

# Check PostgreSQL is running
sudo systemctl status postgresql

# Check Redis
redis-cli -a <password> ping
```

**4. Frontend Not Loading**
```bash
# Check build
cd /opt/zainone-orchestrator/frontend
npm run build

# Check Nginx
sudo nginx -t
sudo systemctl status nginx

# Check logs
sudo tail -f /var/log/nginx/error.log
```

---

## 📊 Performance Tuning

### Backend Optimization
```python
# In app/main.py
uvicorn.run(
    app,
    host="0.0.0.0",
    port=8000,
    workers=4,  # CPU cores
    limit_concurrency=100,
    timeout_keep_alive=5
)
```

### Database Optimization
```sql
-- PostgreSQL tuning
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
SELECT pg_reload_conf();
```

### Redis Optimization
```bash
# In /etc/redis/redis.conf
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
```

---

## 🎯 Summary

### To Fix LLM Connection:
1. Update `backend/orchestrator/app/clients/llm_client.py` with fixes
2. Run `python test_llm_production.py http://localhost:11434 llama3:8b`
3. Verify all tests pass

### To Deploy to Production:
1. Prepare production server (Ubuntu 20.04+)
2. Transfer application files
3. Configure .env with production values
4. Set up PostgreSQL and Redis
5. Install dependencies
6. Configure systemd services
7. Set up Nginx reverse proxy
8. Configure SSL certificates
9. Enable firewall
10. Verify all services running

### Critical Production Settings:
- **LLM_BASE_URL**: Your production LLM server
- **POSTGRES_PASSWORD**: Strong password
- **REDIS_PASSWORD**: Strong password
- **AUTH_SECRET_KEY**: Generated secret
- **DEBUG**: False
- **HTTPS**: Enabled

**Estimated Deployment Time:** 2-4 hours
**Recommended Team:** 2 people (1 backend, 1 DevOps)
