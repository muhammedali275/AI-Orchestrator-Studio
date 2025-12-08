# WHERE is the Dummy Data? - Complete Guide

## 🎯 Current Status

The Admin Panel currently shows:
- ✅ User Management (dummy data in AdminPanel.tsx)
- ✅ System Metrics (dummy data in AdminPanel.tsx)
- ✅ Feature Flags (dummy data in AdminPanel.tsx)

**Missing tabs that need to be added:**
- ❌ External Agents Tab
- ❌ Data Sources Tab
- ❌ Databases Tab
- ❌ Application Settings Tab

---

## 📍 WHERE is the Dummy Data Located?

### **1. External Agents - WHERE?**

**Current Location:** `backend/orchestrator/config/agents.example.json`

```json
{
  "default": {
    "name": "Default External Agent",
    "url": "http://localhost:8001",
    "auth_token": "your-auth-token-here",
    "timeout_seconds": 30,
    "enabled": true,
    "metadata": {
      "description": "Default external agent for testing",
      "version": "1.0.0"
    }
  }
}
```

**To Edit:**
1. Open: `backend/orchestrator/config/agents.example.json`
2. Change:
   - `url`: Your agent IP and port
   - `auth_token`: Your authentication token
   - `name`: Your agent name
3. Save file
4. Backend auto-reloads

**OR via GUI (needs to be implemented):**
- Admin Panel → Agents Tab → Add/Edit Agent

---

### **2. Data Sources - WHERE?**

**Current Location:** `backend/orchestrator/config/datasources.example.json`

```json
{
  "default": {
    "name": "Default Data Source",
    "type": "api",
    "url": "http://localhost:4000",
    "auth_token": "your-token-here",
    "timeout_seconds": 30,
    "enabled": true,
    "config": {
      "database": "analytics",
      "schema": "public"
    }
  }
}
```

**To Edit:**
1. Open: `backend/orchestrator/config/datasources.example.json`
2. Change:
   - `url`: Your data source IP and port
   - `type`: `cubejs`, `postgres`, `api`, etc.
   - `auth_token`: Your authentication token
3. Save file
4. Backend auto-reloads

**OR via GUI (needs to be implemented):**
- Admin Panel → Data Sources Tab → Add/Edit Data Source

---

### **3. Databases - WHERE?**

**Current Location:** `backend/orchestrator/config/example.env`

```env
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=orchestrator
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password-here

# Redis
REDIS_URL=redis://localhost:6379
```

**To Edit:**
1. Open: `backend/orchestrator/config/example.env`
2. Copy to: `backend/orchestrator/.env` (if not exists)
3. Change:
   - `POSTGRES_HOST`: Your PostgreSQL IP
   - `POSTGRES_PORT`: Your PostgreSQL port
   - `POSTGRES_PASSWORD`: Your password
   - `REDIS_URL`: Your Redis connection string
4. Save file
5. Backend auto-reloads

**OR via GUI:**
- DB Management page (already exists!)
- Location: Main Menu → DB Management

---

### **4. Application Settings - WHERE?**

**Current Location:** `backend/orchestrator/config/example.env`

```env
# Application Settings
APP_NAME=ZainOne Orchestrator Studio
APP_VERSION=1.0.0
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

**To Edit:**
1. Open: `backend/orchestrator/config/example.env`
2. Copy to: `backend/orchestrator/.env` (if not exists)
3. Change:
   - `APP_NAME`: Your app name
   - `API_PORT`: Your API port
   - `CORS_ORIGINS`: Your allowed origins
   - `DEBUG`: True/False
   - `LOG_LEVEL`: DEBUG, INFO, WARNING, ERROR
4. Save file
5. Backend auto-reloads

**OR via GUI (needs to be implemented):**
- Admin Panel → Settings Tab → Edit Settings

---

## 📊 Complete File Locations Map

```
ZainOne-Orchestrator-Studio/
│
├── backend/orchestrator/
│   ├── .env ← Application Settings, Databases, LLM
│   │   (Copy from example.env if not exists)
│   │
│   └── config/
│       ├── example.env ← Template for .env
│       ├── agents.example.json ← External Agents dummy data
│       ├── datasources.example.json ← Data Sources dummy data
│       └── tools.example.json ← Tools dummy data
│
└── frontend/src/pages/
    ├── AdminPanel.tsx ← User Management, Feature Flags
    ├── LLMConfig.tsx ← LLM Configuration
    ├── DBManagement.tsx ← Database Configuration
    ├── ToolsConfig.tsx ← Tools Configuration
    └── Monitoring.tsx ← Server Monitoring
```

---

## 🔧 How to Edit Dummy Data

### **Method 1: Edit Files Directly**

#### **Step 1: External Agents**
```bash
# Open file
backend/orchestrator/config/agents.example.json

# Edit JSON
{
  "zain-agent": {
    "name": "Zain Telecom Agent",
    "url": "http://192.168.1.50:8001",
    "auth_token": "your-token-here",
    "timeout_seconds": 60,
    "enabled": true
  }
}

# Save → Backend auto-reloads
```

#### **Step 2: Data Sources**
```bash
# Open file
backend/orchestrator/config/datasources.example.json

# Edit JSON
{
  "cubejs": {
    "name": "CubeJS Analytics",
    "type": "cubejs",
    "url": "http://192.168.1.200:4000",
    "auth_token": "cubejs-token",
    "enabled": true
  }
}

# Save → Backend auto-reloads
```

#### **Step 3: Databases & App Settings**
```bash
# Open file
backend/orchestrator/config/example.env

# Copy to .env if not exists
cp backend/orchestrator/config/example.env backend/orchestrator/.env

# Edit .env
POSTGRES_HOST=192.168.1.150
POSTGRES_PORT=5432
POSTGRES_PASSWORD=your-password

APP_NAME=AI Orchestrator Studio
API_PORT=8000

# Save → Backend auto-reloads
```

---

### **Method 2: Use GUI (Recommended)**

#### **✅ Already Working:**
1. **LLM Config** → Main Menu → LLM Config
2. **DB Management** → Main Menu → DB Management
3. **Tools Config** → Main Menu → Tools Config
4. **Monitoring** → Main Menu → Monitoring

#### **❌ Need to Add to Admin Panel:**
1. **External Agents Tab** → Admin Panel → Agents (needs implementation)
2. **Data Sources Tab** → Admin Panel → Data Sources (needs implementation)
3. **Settings Tab** → Admin Panel → Settings (needs implementation)

---

## 🎯 Current Admin Panel Structure

```
Admin Panel (frontend/src/pages/AdminPanel.tsx)
│
├── System Metrics (dummy data in file)
│   └── getMockMetrics() function
│
├── User Management (dummy data in file)
│   └── getMockUsers() function
│
└── Feature Flags (dummy data in file)
    └── getMockFeatureFlags() function
```

**Dummy data is hardcoded in these functions:**
- Line 95: `getMockUsers()`
- Line 110: `getMockMetrics()`
- Line 145: `getMockFeatureFlags()`

---

## 📝 To Add Missing Tabs to Admin Panel

### **Need to implement:**

1. **Agents Tab**
   - Read from: `config/agents.json`
   - API: `/api/agents`
   - CRUD operations: Add, Edit, Delete agents

2. **Data Sources Tab**
   - Read from: `config/datasources.json`
   - API: `/api/datasources`
   - CRUD operations: Add, Edit, Delete data sources

3. **Settings Tab**
   - Read from: `.env` file
   - API: `/api/config/settings`
   - Edit: App name, port, CORS, debug mode, etc.

---

## 🚀 Quick Edit Guide

### **To Change External Agent:**
```bash
# File: backend/orchestrator/config/agents.example.json
# Line: 3-10
"url": "http://YOUR_IP:YOUR_PORT"  # Change this
"auth_token": "YOUR_TOKEN"          # Change this
```

### **To Change Data Source:**
```bash
# File: backend/orchestrator/config/datasources.example.json
# Line: 3-10
"url": "http://YOUR_IP:YOUR_PORT"  # Change this
"type": "YOUR_TYPE"                 # Change this (cubejs, postgres, api)
```

### **To Change Database:**
```bash
# File: backend/orchestrator/.env (or example.env)
# Line: 15-20
POSTGRES_HOST=YOUR_IP               # Change this
POSTGRES_PORT=YOUR_PORT             # Change this
POSTGRES_PASSWORD=YOUR_PASSWORD     # Change this
```

### **To Change App Settings:**
```bash
# File: backend/orchestrator/.env (or example.env)
# Line: 1-10
APP_NAME=YOUR_APP_NAME              # Change this
API_PORT=YOUR_PORT                  # Change this
DEBUG=True                          # Change this
```

---

## ✅ Summary

### **WHERE is the dummy data?**

| Configuration | File Location | Line Numbers |
|--------------|---------------|--------------|
| **External Agents** | `config/agents.example.json` | All |
| **Data Sources** | `config/datasources.example.json` | All |
| **Databases** | `.env` or `config/example.env` | 15-25 |
| **App Settings** | `.env` or `config/example.env` | 1-14 |
| **User Management** | `frontend/src/pages/AdminPanel.tsx` | 95-110 (getMockUsers) |
| **System Metrics** | `frontend/src/pages/AdminPanel.tsx` | 110-145 (getMockMetrics) |
| **Feature Flags** | `frontend/src/pages/AdminPanel.tsx` | 145-170 (getMockFeatureFlags) |

### **How to edit?**

**Option 1: Edit files directly** (works now)
- Open file → Change values → Save → Backend auto-reloads

**Option 2: Use GUI** (partially working)
- ✅ LLM Config page
- ✅ DB Management page
- ✅ Tools Config page
- ✅ Monitoring page
- ❌ Admin Panel → Agents Tab (needs implementation)
- ❌ Admin Panel → Data Sources Tab (needs implementation)
- ❌ Admin Panel → Settings Tab (needs implementation)

### **What needs to be added?**

To make Admin Panel complete, need to add 3 tabs:
1. **Agents Tab** - Manage external agents
2. **Data Sources Tab** - Manage data sources
3. **Settings Tab** - Manage app settings

These tabs should read/write to the JSON and .env files mentioned above.
