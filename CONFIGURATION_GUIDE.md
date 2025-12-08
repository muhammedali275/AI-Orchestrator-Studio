# Complete Configuration Guide - AI Orchestrator Studio

## 🎯 What You Can Edit from GUI

### **Summary: ALL Configuration Data Editable from GUI**

You can configure the entire orchestrator application from the GUI without touching any code files. All changes automatically save to backend configuration files.

---

## 📋 Complete List of Editable Configuration

### **1. LLM Configuration** (Page: LLM Config)
**Saves to:** `.env` file

| Field | Description | Example |
|-------|-------------|---------|
| **Server IP** | LLM server address | `localhost` or `192.168.1.100` |
| **Server Port** | LLM server port | `11434` |
| **Endpoint Path** | API endpoint | `/v1/chat/completions` |
| **API Key** | Authentication token | `sk-abc123...` (optional) |
| **Model** | Model name | `llama4-scout` |
| **Timeout** | Request timeout (seconds) | `60` |

**Full URL Generated:** `http://{ip}:{port}{path}`

---

### **2. External Agents** (Page: Admin Panel → Agents Tab)
**Saves to:** `config/agents.json`

| Field | Description | Example |
|-------|-------------|---------|
| **Agent Name** | Identifier | `zain-agent` |
| **Agent IP** | Server address | `localhost` or `10.0.0.50` |
| **Agent Port** | Server port | `8001` |
| **Endpoint Path** | API path | `/execute` |
| **Auth Token** | Authentication | `token-abc123` |
| **Timeout** | Request timeout | `60` seconds |
| **Enabled** | Active status | `true` / `false` |

**Full URL Generated:** `http://{ip}:{port}{path}`

---

### **3. Data Sources** (Page: Admin Panel → Data Sources Tab)
**Saves to:** `config/datasources.json`

| Field | Description | Example |
|-------|-------------|---------|
| **Source Name** | Identifier | `cubejs` |
| **Source Type** | Type | `cubejs`, `postgres`, `api` |
| **Server IP** | Database/API address | `localhost` or `192.168.1.200` |
| **Server Port** | Database/API port | `4000`, `5432` |
| **Database Name** | DB name (if applicable) | `analytics` |
| **Username** | DB username | `admin` |
| **Password** | DB password | `••••••••` |
| **Auth Token** | API token | `token-xyz789` |
| **Connection String** | Full connection URL | `postgresql://user:pass@host:port/db` |

**Examples:**
- **CubeJS:** `http://192.168.1.200:4000`
- **PostgreSQL:** `postgresql://admin:pass@192.168.1.200:5432/analytics`
- **Custom API:** `https://api.example.com/data`

---

### **4. Tools Configuration** (Page: Tools Config)
**Saves to:** `config/tools.json`

| Field | Description | Example |
|-------|-------------|---------|
| **Tool Name** | Identifier | `web_search` |
| **Tool Type** | Type | `http_request`, `web_search`, `code_executor` |
| **API Endpoint** | Tool API URL | `https://api.search.com/search` |
| **API Key** | Authentication | `key-abc123` |
| **Parameters** | Tool-specific config | `{"max_results": 10}` |
| **Enabled** | Active status | `true` / `false` |

---

### **5. Database Configuration** (Page: DB Management)
**Saves to:** `.env` file

| Field | Description | Example |
|-------|-------------|---------|
| **PostgreSQL Host** | DB server IP | `localhost` or `192.168.1.150` |
| **PostgreSQL Port** | DB port | `5432` |
| **Database Name** | DB name | `orchestrator` |
| **Username** | DB user | `postgres` |
| **Password** | DB password | `••••••••` |
| **Redis Host** | Cache server IP | `localhost` or `192.168.1.160` |
| **Redis Port** | Cache port | `6379` |
| **Redis Password** | Cache password | `••••••••` (optional) |

---

### **6. Monitoring Servers** (Page: Monitoring)
**Saves to:** Database

| Field | Description | Example |
|-------|-------------|---------|
| **Server Name** | Identifier | `prod-server-1` |
| **Server IP** | Target server | `192.168.1.50` |
| **Server Port** | SSH/API port | `22`, `443` |
| **Protocol** | Connection type | `SSH`, `HTTP`, `SNMP` |
| **Username** | Login username | `admin` |
| **Password** | Login password | `••••••••` |
| **SSH Key** | SSH private key | `-----BEGIN RSA PRIVATE KEY-----` |
| **Metrics Interval** | Collection frequency | `60` seconds |

---

### **7. Application Settings** (Page: Admin Panel → Settings)
**Saves to:** `.env` file

| Field | Description | Example |
|-------|-------------|---------|
| **App Name** | Application name | `AI Orchestrator Studio` |
| **App Version** | Version number | `1.0.0` |
| **API Host** | Backend host | `0.0.0.0` (all interfaces) |
| **API Port** | Backend port | `8000` |
| **Frontend URL** | Frontend address | `http://localhost:3000` |
| **CORS Origins** | Allowed origins | `http://localhost:3000` |
| **Log Level** | Logging level | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| **Debug Mode** | Debug flag | `True` / `False` |

---

### **8. Memory & Cache** (Page: Memory & Cache)
**Saves to:** `.env` file

| Field | Description | Example |
|-------|-------------|---------|
| **Redis URL** | Cache connection | `redis://localhost:6379` |
| **Cache TTL** | Time to live (seconds) | `3600` |
| **Max Memory** | Max cache size (MB) | `512` |
| **Eviction Policy** | Cache eviction | `allkeys-lru` |

---

### **9. Security & Credentials** (Page: Admin Panel → Credentials)
**Saves to:** Database (encrypted)

| Field | Description | Example |
|-------|-------------|---------|
| **Credential Name** | Identifier | `prod-db-creds` |
| **Credential Type** | Type | `api_key`, `ssh`, `database`, `oauth` |
| **Value** | Secret value | `••••••••` (encrypted) |
| **Metadata** | Additional info | `{"environment": "production"}` |

---

## 🔄 How Configuration Flows

```
┌─────────────────────────────────────────────────────────────┐
│                    USER EDITS IN GUI                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              React Component State Update                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         Click "Save" → POST to Backend API                   │
│         /api/config/env or /api/config/agents               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│           Backend API Receives Request                       │
│           (config_management.py)                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         ConfigWriter Writes to Files                         │
│         - .env file                                          │
│         - agents.json                                        │
│         - datasources.json                                   │
│         - tools.json                                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         WatchFiles Detects Change                            │
│         "WARNING: WatchFiles detected changes..."            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         Backend Auto-Reloads (2-3 seconds)                   │
│         New configuration active!                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 Configuration Files Updated by GUI

### **1. `.env` File**
**Edited from:** LLM Config, DB Management, Admin Panel

```env
# Application (Admin Panel)
APP_NAME=AI Orchestrator Studio
API_PORT=8000

# LLM (LLM Config Page)
LLM_BASE_URL=http://192.168.1.100:11434
LLM_DEFAULT_MODEL=llama4-scout
LLM_API_KEY=sk-abc123

# Database (DB Management Page)
POSTGRES_HOST=192.168.1.150
POSTGRES_PORT=5432
REDIS_URL=redis://192.168.1.160:6379

# External Agents (Admin Panel)
EXTERNAL_AGENT_BASE_URL=http://192.168.1.50:8001
```

### **2. `config/agents.json`**
**Edited from:** Admin Panel → Agents Tab

```json
{
  "zain-agent": {
    "name": "Zain Telecom Agent",
    "url": "http://192.168.1.50:8001",
    "auth_token": "token-abc123",
    "timeout_seconds": 60,
    "enabled": true
  },
  "custom-agent": {
    "name": "Custom Agent",
    "url": "http://10.0.0.100:8002",
    "auth_token": "token-xyz789",
    "timeout_seconds": 30,
    "enabled": true
  }
}
```

### **3. `config/datasources.json`**
**Edited from:** Admin Panel → Data Sources Tab

```json
{
  "cubejs": {
    "name": "CubeJS Analytics",
    "type": "cubejs",
    "url": "http://192.168.1.200:4000",
    "auth_token": "cubejs-token",
    "enabled": true
  },
  "postgres-analytics": {
    "name": "Analytics Database",
    "type": "postgres",
    "url": "postgresql://admin:pass@192.168.1.150:5432/analytics",
    "enabled": true
  }
}
```

### **4. `config/tools.json`**
**Edited from:** Tools Config Page

```json
{
  "web_search": {
    "name": "Web Search",
    "type": "web_search",
    "config": {
      "api_endpoint": "https://api.search.com/search",
      "api_key": "search-key-123",
      "max_results": 10
    },
    "enabled": true
  },
  "http_request": {
    "name": "HTTP Request Tool",
    "type": "http_request",
    "config": {
      "timeout": 30,
      "max_retries": 3
    },
    "enabled": true
  }
}
```

---

## 🎯 Quick Configuration Checklist

### **Minimum Required Configuration:**
- [ ] **LLM Server** (LLM Config page)
  - [ ] IP address
  - [ ] Port
  - [ ] Model name

### **Optional But Recommended:**
- [ ] **External Agent** (Admin Panel)
  - [ ] Zain Agent IP & port
  - [ ] Auth token
- [ ] **Database** (DB Management)
  - [ ] PostgreSQL connection
  - [ ] Redis connection
- [ ] **Tools** (Tools Config)
  - [ ] Web search API
  - [ ] Custom tools

### **For Production:**
- [ ] **Monitoring** (Monitoring page)
  - [ ] Add production servers
  - [ ] Configure credentials
  - [ ] Set up alerts
- [ ] **Security** (Admin Panel)
  - [ ] API keys for external access
  - [ ] Credential encryption

---

## 💡 Best Practices

### **1. Use IP Addresses for Production**
```
✅ Good: 192.168.1.100
❌ Avoid: localhost (only for development)
```

### **2. Always Set Timeouts**
```
✅ Good: 60 seconds (allows for slow responses)
❌ Avoid: No timeout (can hang forever)
```

### **3. Secure Credentials**
```
✅ Good: Use API keys, store in encrypted fields
❌ Avoid: Hardcoding passwords in code
```

### **4. Test After Configuration**
```
✅ Always click "Test Connection" button
✅ Verify green checkmark before saving
✅ Check logs for errors
```

---

## 🔧 Configuration Workflow

### **For a New Project:**

#### **Step 1: Configure LLM** (Required)
1. Go to **LLM Config** page
2. Enter:
   - Server IP: `192.168.1.100`
   - Port: `11434`
   - Model: `llama4-scout`
   - API Key: (if needed)
3. Click **"Test Connection"**
4. Click **"Save Configuration"**
5. ✅ Saves to `.env` → Backend auto-reloads

#### **Step 2: Add External Agents** (Optional)
1. Go to **Admin Panel** → **Agents** tab
2. Click **"Add Agent"**
3. Enter:
   - Name: `zain-agent`
   - URL: `http://192.168.1.50:8001`
   - Auth Token: `your-token`
4. Click **"Save"**
5. ✅ Saves to `agents.json` → Backend auto-reloads

#### **Step 3: Configure Data Sources** (Optional)
1. Go to **Admin Panel** → **Data Sources** tab
2. Click **"Add Data Source"**
3. Enter:
   - Name: `cubejs`
   - Type: `cubejs`
   - URL: `http://192.168.1.200:4000`
   - Token: `cubejs-token`
4. Click **"Save"**
5. ✅ Saves to `datasources.json` → Backend auto-reloads

#### **Step 4: Add Tools** (Optional)
1. Go to **Tools Config** page
2. Click **"Add Tool"**
3. Enter:
   - Name: `web_search`
   - Type: `web_search`
   - API Endpoint: `https://api.search.com`
   - API Key: `search-key`
4. Click **"Save"**
5. ✅ Saves to `tools.json` → Backend auto-reloads

#### **Step 5: Configure Monitoring** (Optional)
1. Go to **Monitoring** page
2. Click **"Add Server"**
3. Enter:
   - Server Name: `prod-server-1`
   - IP: `192.168.1.10`
   - Port: `22` (SSH) or `443` (HTTPS)
   - Credentials: Username/password or SSH key
4. Click **"Save"**
5. ✅ Saves to database

---

## 📊 Configuration Summary Table

| Configuration | GUI Page | Saves To | Fields | Auto-Reload |
|--------------|----------|----------|--------|-------------|
| **LLM** | LLM Config | `.env` | IP, Port, Path, API Key, Model, Timeout | ✅ Yes |
| **Agents** | Admin Panel | `agents.json` | Name, IP, Port, Path, Token, Timeout | ✅ Yes |
| **Data Sources** | Admin Panel | `datasources.json` | Name, Type, IP, Port, DB, User, Pass, Token | ✅ Yes |
| **Tools** | Tools Config | `tools.json` | Name, Type, Endpoint, API Key, Config | ✅ Yes |
| **Database** | DB Management | `.env` | Postgres (IP, Port, DB, User, Pass), Redis (IP, Port, Pass) | ✅ Yes |
| **Monitoring** | Monitoring | Database | Server Name, IP, Port, Protocol, Credentials | ❌ No |
| **App Settings** | Admin Panel | `.env` | Name, Version, Port, CORS, Debug, Logs | ✅ Yes |
| **Credentials** | Admin Panel | Database | Name, Type, Value (encrypted) | ❌ No |
| **API Keys** | Admin Panel | Database | Name, Permissions, Expiry | ❌ No |

**Auto-Reload:** Configuration files (.env, .json) trigger automatic backend reload in 2-3 seconds.

---

## 🎯 What You Need to Configure (Minimum)

### **For Basic Usage:**
1. ✅ **LLM Server** (IP, Port, Model) - REQUIRED
2. ✅ **Nothing else!** - Everything else is optional

### **For Full Features:**
1. ✅ **LLM Server** - Required
2. ✅ **External Agents** - For domain-specific AI (Zain Agent)
3. ✅ **Data Sources** - For data grounding (CubeJS, databases)
4. ✅ **Tools** - For web search, code execution, etc.
5. ✅ **Monitoring** - For server health monitoring
6. ✅ **Database** - For persistence (PostgreSQL, Redis)

---

## 📁 Files Modified by GUI

### **Configuration Files:**
```
backend/orchestrator/
├── .env                      ← LLM, DB, App settings
├── config/
│   ├── agents.json           ← External agents
│   ├── datasources.json      ← Data sources
│   └── tools.json            ← Tools
└── credentials.db            ← Encrypted credentials
```

### **What Happens When You Save:**
1. GUI sends data to backend API
2. Backend validates data
3. Backend writes to file (with backup)
4. WatchFiles detects change
5. Backend auto-reloads (2-3 seconds)
6. New configuration active!

---

## ✅ Summary

**Total Editable Fields:** 50+
**Configuration Files:** 4 (.env, agents.json, datasources.json, tools.json)
**GUI Pages:** 6 (LLM Config, Admin Panel, Tools Config, DB Management, Monitoring, File Explorer)
**Auto-Reload:** ✅ Enabled for all file changes
**No Code Required:** ✅ Everything configurable from GUI

**You can configure:**
- ✅ IPs (LLM, agents, databases, monitoring servers)
- ✅ Ports (all services)
- ✅ Paths (API endpoints)
- ✅ Links (full URLs)
- ✅ Credentials (passwords, tokens, SSH keys)
- ✅ Timeouts (all services)
- ✅ Models (LLM models)
- ✅ Permissions (API keys)

**Everything saves to files and triggers automatic backend reload!**
