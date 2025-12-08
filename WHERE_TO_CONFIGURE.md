# WHERE to Configure IPs, Ports, and Credentials in GUI

## 🎯 Quick Navigation Guide

### **1. LLM Server Configuration**
📍 **Location:** Main Menu → **LLM Config**
🔧 **What to Configure:**
- ✅ Server IP: `localhost` or `192.168.1.100`
- ✅ Server Port: `11434`
- ✅ Endpoint Path: `/v1/chat/completions`
- ✅ API Key: (optional)
- ✅ Model: `llama4-scout`
- ✅ Timeout: `60` seconds

**Saves to:** `.env` file → Backend auto-reloads

---

### **2. External Agents (Zain Agent, Custom Agents)**
📍 **Location:** Main Menu → **Admin Panel** → **Agents Tab**
🔧 **What to Configure:**
- ✅ Agent Name: `zain-agent`
- ✅ Agent IP: `192.168.1.50`
- ✅ Agent Port: `8001`
- ✅ Endpoint Path: `/execute`
- ✅ Auth Token: `your-token-here`
- ✅ Timeout: `60` seconds

**Saves to:** `config/agents.json` → Backend auto-reloads

---

### **3. Data Sources (CubeJS, Databases, APIs)**
📍 **Location:** Main Menu → **Admin Panel** → **Data Sources Tab**
🔧 **What to Configure:**
- ✅ Source Name: `cubejs`
- ✅ Source Type: `cubejs`, `postgres`, `api`
- ✅ Server IP: `192.168.1.200`
- ✅ Server Port: `4000` (CubeJS) or `5432` (PostgreSQL)
- ✅ Database Name: `analytics`
- ✅ Username: `admin`
- ✅ Password: `••••••••`
- ✅ Auth Token: (for APIs)

**Saves to:** `config/datasources.json` → Backend auto-reloads

---

### **4. Tools (Web Search, HTTP, Code Executor)**
📍 **Location:** Main Menu → **Tools Config**
🔧 **What to Configure:**
- ✅ Tool Name: `web_search`
- ✅ Tool Type: `web_search`, `http_request`, `code_executor`
- ✅ API Endpoint: `https://api.search.com/search`
- ✅ API Key: `search-key-123`
- ✅ Parameters: `{"max_results": 10}`

**Saves to:** `config/tools.json` → Backend auto-reloads

---

### **5. Database Connections (PostgreSQL, Redis)**
📍 **Location:** Main Menu → **DB Management**
🔧 **What to Configure:**

**PostgreSQL:**
- ✅ Host: `192.168.1.150`
- ✅ Port: `5432`
- ✅ Database: `orchestrator`
- ✅ Username: `postgres`
- ✅ Password: `••••••••`

**Redis:**
- ✅ Host: `192.168.1.160`
- ✅ Port: `6379`
- ✅ Password: `••••••••` (optional)

**Saves to:** `.env` file → Backend auto-reloads

---

### **6. Monitoring Servers (Production Servers)**
📍 **Location:** Main Menu → **Monitoring**
🔧 **What to Configure:**
- ✅ Server Name: `prod-server-1`
- ✅ Server IP: `192.168.1.10`
- ✅ Server Port: `22` (SSH) or `443` (HTTPS)
- ✅ Protocol: `SSH`, `HTTP`, `SNMP`
- ✅ Username: `admin`
- ✅ Password: `••••••••`
- ✅ SSH Key: (paste private key)

**Saves to:** Database

---

### **7. Application Settings**
📍 **Location:** Main Menu → **Admin Panel** → **Settings Tab**
🔧 **What to Configure:**
- ✅ App Name: `AI Orchestrator Studio`
- ✅ API Port: `8000`
- ✅ Frontend URL: `http://localhost:3000`
- ✅ CORS Origins: `http://localhost:3000`
- ✅ Log Level: `INFO`, `DEBUG`, `WARNING`, `ERROR`
- ✅ Debug Mode: `True` / `False`

**Saves to:** `.env` file → Backend auto-reloads

---

### **8. Credentials Management**
📍 **Location:** Main Menu → **Admin Panel** → **Credentials Tab**
🔧 **What to Configure:**
- ✅ Credential Name: `prod-db-password`
- ✅ Credential Type: `api_key`, `ssh`, `database`, `oauth`
- ✅ Value: `••••••••` (encrypted)
- ✅ Metadata: `{"environment": "production"}`

**Saves to:** Database (encrypted)

---

### **9. API Keys (External Access)**
📍 **Location:** Main Menu → **Admin Panel** → **API Keys Tab**
🔧 **What to Configure:**
- ✅ Key Name: `External App`
- ✅ Permissions: `read`, `write`, `admin`
- ✅ Expiry: `365` days

**Saves to:** Database

---

## 📊 Visual Menu Structure

```
AI Orchestrator Studio
│
├── 📊 Dashboard
│
├── 📁 File Explorer
│
├── 💬 Chat Studio
│
├── 🔀 Topology ← View workflow
│
├── ⚙️ LLM Config ← ✨ Configure LLM (IP, Port, Model)
│
├── 🔧 Tools Config ← ✨ Configure Tools (APIs, Keys)
│
├── 💾 Memory & Cache
│
├── 🗄️ DB Management ← ✨ Configure Databases (PostgreSQL, Redis)
│
├── 📈 Monitoring ← ✨ Configure Servers (IPs, Credentials)
│
├── 🔄 Upgrades
│
└── 👤 Admin Panel ← ✨ Configure Everything Else
    ├── Agents Tab ← ✨ Configure External Agents
    ├── Data Sources Tab ← ✨ Configure Data Sources
    ├── Credentials Tab ← ✨ Manage Credentials
    ├── API Keys Tab ← ✨ Manage API Keys
    └── Settings Tab ← ✨ App Settings
```

---

## 🎯 Quick Start: Where to Go First

### **For Basic Setup (5 minutes):**
1. **LLM Config** → Configure LLM server (REQUIRED)
2. Done! Everything else is optional.

### **For Full Setup (15 minutes):**
1. **LLM Config** → Configure LLM server
2. **Admin Panel → Agents** → Add Zain Agent
3. **Admin Panel → Data Sources** → Add CubeJS/Database
4. **Tools Config** → Add web search tool
5. **DB Management** → Configure PostgreSQL & Redis
6. **Monitoring** → Add production servers
7. Done!

---

## 📝 Configuration Checklist

### **Minimum Required:**
- [ ] **LLM Config** page
  - [ ] Server IP
  - [ ] Server Port
  - [ ] Model name
  - [ ] Click "Test Connection"
  - [ ] Click "Save Configuration"

### **Recommended:**
- [ ] **Admin Panel → Agents** tab
  - [ ] Add Zain Agent (IP, Port, Token)
- [ ] **Admin Panel → Data Sources** tab
  - [ ] Add CubeJS or Database
- [ ] **Tools Config** page
  - [ ] Add web search tool

### **For Production:**
- [ ] **DB Management** page
  - [ ] Configure PostgreSQL
  - [ ] Configure Redis
- [ ] **Monitoring** page
  - [ ] Add production servers
  - [ ] Add credentials
- [ ] **Admin Panel → API Keys** tab
  - [ ] Create API keys for external apps

---

## 🔍 How to Find Configuration Pages

### **Method 1: Use Sidebar Menu**
Look at the left sidebar - all configuration pages are listed there.

### **Method 2: Use Search**
Press `Ctrl+F` and search for:
- "LLM Config" → LLM server settings
- "Admin Panel" → Agents, Data Sources, Credentials
- "Tools Config" → Tools settings
- "DB Management" → Database settings
- "Monitoring" → Server monitoring

### **Method 3: Follow This Order**
1. Start at **Dashboard**
2. Click **LLM Config** (configure LLM)
3. Click **Admin Panel** (configure agents, data sources)
4. Click **Tools Config** (configure tools)
5. Click **DB Management** (configure databases)
6. Click **Monitoring** (configure servers)

---

## 💡 Tips

### **Tip 1: Test Before Saving**
Every configuration page has a "Test Connection" button. Always test before saving!

### **Tip 2: Watch for Auto-Reload**
After saving, watch the terminal. You'll see:
```
WARNING: WatchFiles detected changes in 'config/agents.json'. Reloading...
```
This means your configuration is active!

### **Tip 3: Use Full URLs**
The GUI automatically builds full URLs from IP + Port + Path:
- Input: IP=`192.168.1.100`, Port=`11434`, Path=`/v1/chat`
- Result: `http://192.168.1.100:11434/v1/chat`

### **Tip 4: Save Credentials Securely**
Use the **Admin Panel → Credentials** tab to store sensitive data. It's encrypted in the database.

---

## 📍 Summary: Where to Configure What

| What to Configure | Where to Go | Page Name |
|-------------------|-------------|-----------|
| **LLM Server** | Main Menu | **LLM Config** |
| **External Agents** | Main Menu → Admin Panel | **Agents Tab** |
| **Data Sources** | Main Menu → Admin Panel | **Data Sources Tab** |
| **Tools** | Main Menu | **Tools Config** |
| **Databases** | Main Menu | **DB Management** |
| **Monitoring Servers** | Main Menu | **Monitoring** |
| **App Settings** | Main Menu → Admin Panel | **Settings Tab** |
| **Credentials** | Main Menu → Admin Panel | **Credentials Tab** |
| **API Keys** | Main Menu → Admin Panel | **API Keys Tab** |

---

## 🚀 Start Here

1. Open browser: `http://localhost:3000`
2. Click **LLM Config** in sidebar
3. Enter your LLM server details
4. Click "Test Connection"
5. Click "Save Configuration"
6. ✅ Done! Backend auto-reloads with new config

**Everything else is optional and can be configured later as needed.**

---

## 📖 Need More Help?

- **Complete Configuration Guide:** See `CONFIGURATION_GUIDE.md`
- **API Documentation:** See `API_DOCUMENTATION.md`
- **Quick Start:** See `QUICKSTART.md`
- **Troubleshooting:** See `TROUBLESHOOTING_EMPTY_PAGES.md`
