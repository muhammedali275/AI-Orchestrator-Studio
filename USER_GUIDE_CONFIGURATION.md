# AI Orchestrator Studio - User Configuration Guide

## 🎯 Where to Add Your Agentic AI Configuration

This guide explains exactly where in the GUI you should add your inputs for any agentic AI system, and how those changes will reflect in all configuration files.

---

## 📍 Configuration Input Locations in GUI

### 1. **LLM Configuration** (Primary AI Agent Settings)

**Location:** Navigate to **LLM Config** page in the sidebar

**What to Configure:**
- **Server Path**: Base URL of your LLM server (e.g., `http://localhost`, `http://192.168.1.100`)
- **Port**: LLM server port (e.g., `11434` for Ollama, `8000` for custom)
- **Endpoint Path**: API endpoint (e.g., `/v1/chat/completions`, `/api/generate`)
- **Model**: Select your AI model (e.g., `llama4-scout`, `gpt-4`, `claude-3-opus`)
- **Timeout**: Request timeout in seconds

**How It Works:**
1. Enter your LLM server details
2. Click "Test Connection" to verify
3. Click "Save Configuration"
4. Changes are saved to `.env` file automatically via `/api/config/env` endpoint

**Files Updated:**
- `backend/orchestrator/.env` - LLM_BASE_URL, LLM_DEFAULT_MODEL, LLM_PORT, etc.

**Example Configuration:**
```
Server Path: http://localhost
Port: 11434
Endpoint: /v1/chat/completions
Model: llama4-scout
Timeout: 60
```

---

### 2. **External Agents Configuration** (Multi-Agent Setup)

**Location:** Navigate to **Admin Panel** page → **Agents** tab

**What to Configure:**
- **Agent Name**: Identifier for the agent (e.g., `zain_agent`, `research_agent`)
- **Agent URL**: Base URL of the external agent (e.g., `http://192.168.1.50:8001`)
- **Auth Token**: Authentication token (if required)
- **Timeout**: Request timeout in seconds
- **Enabled**: Toggle to enable/disable agent

**How It Works:**
1. Click "Add Agent" button
2. Fill in agent details
3. Click "Save"
4. Changes are saved to `config/agents.json` via `/api/config/agents` endpoint

**Files Updated:**
- `backend/orchestrator/config/agents.json`

**Example Configuration:**
```json
{
  "agents": [
    {
      "name": "zain_agent",
      "url": "http://192.168.1.50:8001",
      "auth_token": "your-token-here",
      "timeout_seconds": 30,
      "enabled": true
    }
  ]
}
```

---

### 3. **Data Sources Configuration** (Knowledge Bases)

**Location:** Navigate to **Admin Panel** page → **Data Sources** tab

**What to Configure:**
- **Source Name**: Identifier (e.g., `postgres_db`, `cubejs_api`)
- **Source Type**: Type of datasource (postgres, cubejs, api, etc.)
- **URL**: Connection URL
- **Auth Token**: API key or token
- **Timeout**: Request timeout

**How It Works:**
1. Click "Add Data Source"
2. Fill in datasource details
3. Click "Save"
4. Changes are saved to `config/datasources.json` via `/api/config/datasources` endpoint

**Files Updated:**
- `backend/orchestrator/config/datasources.json`

**Example Configuration:**
```json
{
  "datasources": [
    {
      "name": "postgres_db",
      "type": "postgres",
      "url": "postgresql://user:pass@localhost:5432/dbname",
      "enabled": true
    }
  ]
}
```

---

### 4. **Tools Configuration** (Agent Capabilities)

**Location:** Navigate to **Tools Config** page

**What to Configure:**
- **Tool Name**: Identifier (e.g., `web_search`, `code_executor`)
- **Tool Type**: Type of tool (http_request, web_search, code_executor, etc.)
- **Configuration**: Tool-specific settings (API keys, endpoints, etc.)
- **Enabled**: Toggle to enable/disable tool

**How It Works:**
1. Click "Add Tool" button
2. Fill in tool details
3. Click "Save"
4. Changes are saved to `config/tools.json` via `/api/config/tools` endpoint

**Files Updated:**
- `backend/orchestrator/config/tools.json`

**Example Configuration:**
```json
{
  "tools": [
    {
      "name": "web_search",
      "type": "web_search",
      "config": {
        "api_key": "your-search-api-key",
        "max_results": 10
      },
      "enabled": true
    }
  ]
}
```

---

### 5. **Monitoring Servers** (Destination Server Monitoring)

**Location:** Navigate to **Monitoring** page → **Servers** tab

**What to Configure:**
- **Server Name**: Friendly name (e.g., `Production Server`)
- **Host/IP**: Server address (e.g., `192.168.1.100`)
- **Port**: Connection port (e.g., `22` for SSH, `443` for HTTPS)
- **Connection Type**: SSH, API, or SNMP
- **Credentials**: Username/password or API key

**How It Works:**
1. Click "Add Server" button
2. Fill in server details
3. Add credentials in the **Credentials** tab
4. Click "Save"
5. Server will be monitored in real-time

**Files Updated:**
- `backend/orchestrator/config/monitoring_servers.json` (future implementation)
- Credentials stored securely in database

---

## 🔄 How Configuration Changes Reflect in Files

### Automatic File Updates

When you save any configuration in the GUI:

1. **Frontend** sends data to backend API
2. **Backend API** validates the data
3. **ConfigWriter Service** creates a backup of existing file
4. **New configuration** is written to the file
5. **Settings cache** is cleared
6. **Configuration reloads** automatically

### File Locations

All configuration files are stored in:
```
backend/orchestrator/
├── .env                          # Environment variables (LLM, ports, etc.)
├── config/
│   ├── agents.json              # External agents configuration
│   ├── datasources.json         # Data sources configuration
│   ├── tools.json               # Tools configuration
│   └── *.backup                 # Automatic backups
```

### Backup System

Before any update:
- Automatic backup created with `.backup` extension
- Original file preserved
- Can rollback if needed

---

## 🧪 How to Test the Flow

### Step 1: Configure Your AI Agent

**Go to: LLM Config Page**

1. Enter your LLM server details:
   ```
   Server Path: http://localhost
   Port: 11434
   Endpoint: /v1/chat/completions
   Model: llama4-scout
   ```

2. Click **"Test Connection"** button
   - ✅ Green checkmark = Connected
   - ❌ Red X = Connection failed

3. Click **"Save Configuration"**
   - Configuration saved to `.env` file
   - Success message appears

---

### Step 2: Start Topology Flow

**Go to: Topology Page**

1. Click **"Start Flow"** button (green button at top)
   
2. **Watch Real-time Execution:**
   - Progress bar shows 0-100%
   - Current node highlights in blue
   - Status chip shows: RUNNING → COMPLETED/FAILED
   - Each node changes color as it processes:
     - 🔵 Blue border = Currently processing
     - 🟢 Green border = Completed successfully
     - 🔴 Red border = Failed with error

3. **Monitor Progress:**
   - Progress percentage updates every second
   - Current node name displayed
   - Execution logs captured

4. **View Logs:**
   - Click **"View Logs"** button
   - See detailed execution logs
   - Timestamps, node names, log levels
   - Error messages if any

5. **Stop Execution** (if needed):
   - Click **"Stop Flow"** button (red button)
   - Execution stops immediately
   - Status changes to STOPPED

---

### Step 3: Test Individual Components

**On Topology Page:**

1. Find any component card (e.g., "LLM Agent", "Tool Executor")

2. Click the **🐛 Test icon** button on the right side of the card

3. **Test Results Dialog** appears showing:
   - ✅ Component health status
   - Configuration details
   - Error messages (if any)
   - Connection status

4. **Example Test Results:**
   ```
   Component: llm_agent
   Status: healthy
   Message: LLM agent is configured and ready
   Config:
   {
     "endpoint": "http://localhost:11434",
     "model": "llama4-scout"
   }
   ```

---

### Step 4: Monitor Destination Servers

**Go to: Monitoring Page**

1. **Add a Server:**
   - Click **"Add Server"** button
   - Fill in:
     - Name: `Production Server`
     - Host: `192.168.1.100`
     - Port: `22`
     - Type: `SSH`
     - Username: `admin`
     - Password: `your-password`
   - Click **"Add Server"**

2. **View Metrics:**
   - Click **"View Metrics"** icon for the server
   - Switch to **"Metrics"** tab
   - See real-time:
     - CPU Usage
     - Memory Usage
     - Disk Usage
     - Network Traffic

3. **Test Connection:**
   - Click **"Test Connection"** icon
   - Verify server is reachable

---

## 🎨 Visual Indicators

### Status Colors

| Color | Meaning | Where You'll See It |
|-------|---------|---------------------|
| 🟢 Green | Success/Healthy/Connected | Completed nodes, healthy components |
| 🔵 Blue | Running/Active | Currently executing node |
| 🔴 Red | Error/Failed/Disconnected | Failed nodes, connection errors |
| 🟡 Yellow | Warning | Warnings in logs |
| ⚪ Gray | Idle/Not Started | Nodes waiting to execute |

### Component Status

- **Idle**: Gray - Not yet processed
- **Active**: Blue border + pulsing - Currently processing
- **Completed**: Green border - Successfully processed
- **Failed**: Red border - Error occurred

---

## 📊 Complete Configuration Workflow

### For a New Agentic AI System:

1. **LLM Config Page**
   - Add LLM server URL, port, model
   - Test connection
   - Save → Updates `.env`

2. **Admin Panel → Agents Tab**
   - Add external agents (if any)
   - Configure URLs and auth
   - Save → Updates `agents.json`

3. **Admin Panel → Data Sources Tab**
   - Add knowledge bases
   - Configure connections
   - Save → Updates `datasources.json`

4. **Tools Config Page**
   - Add tools/capabilities
   - Configure tool settings
   - Save → Updates `tools.json`

5. **Monitoring Page**
   - Add destination servers
   - Add credentials
   - Start monitoring

6. **Topology Page**
   - Click "Start Flow"
   - Watch execution
   - Test components
   - View logs

---

## 🔍 Testing Checklist

### ✅ Pre-Flight Checks

Before starting flow execution:

- [ ] LLM server configured and tested (green checkmark)
- [ ] Model selected
- [ ] External agents added (if needed)
- [ ] Data sources configured (if needed)
- [ ] Tools enabled (if needed)

### ✅ Flow Execution Test

- [ ] Click "Start Flow" button
- [ ] Progress bar appears and updates
- [ ] Nodes change color as they process
- [ ] Status shows RUNNING
- [ ] Progress reaches 100%
- [ ] Status changes to COMPLETED
- [ ] No errors in logs

### ✅ Component Testing

- [ ] Test each component individually
- [ ] All components show "healthy" status
- [ ] Configuration details displayed
- [ ] No connection errors

### ✅ Monitoring Test

- [ ] Add a server
- [ ] Test connection successful
- [ ] Metrics display correctly
- [ ] Real-time updates working

---

## 🚨 Troubleshooting

### If Flow Fails:

1. **Check LLM Connection:**
   - Go to LLM Config
   - Click "Test Connection"
   - Verify green checkmark

2. **Check Component Health:**
   - Go to Topology
   - Click test icon on failed component
   - Read error message

3. **View Execution Logs:**
   - Click "View Logs" button
   - Look for ERROR level messages
   - Check which node failed

4. **Common Issues:**
   - ❌ LLM not configured → Configure in LLM Config page
   - ❌ Port not accessible → Check firewall/port settings
   - ❌ Model not found → Verify model name is correct
   - ❌ Timeout → Increase timeout in settings

---

## 📝 Configuration Examples

### Example 1: Local Ollama Setup

**LLM Config:**
```
Server Path: http://localhost
Port: 11434
Endpoint: /v1/chat/completions
Model: llama4-scout
Timeout: 60
```

**Test Flow:**
1. Save configuration
2. Go to Topology
3. Click "Start Flow"
4. Watch execution complete

---

### Example 2: Remote AI Server

**LLM Config:**
```
Server Path: http://192.168.1.50
Port: 8000
Endpoint: /v1/chat/completions
Model: ossgpt-70b
Timeout: 120
```

**External Agent:**
```
Name: zain_agent
URL: http://192.168.1.51:8001
Auth Token: your-token-here
```

**Test Flow:**
1. Configure LLM
2. Add external agent in Admin Panel
3. Go to Topology
4. Click "Start Flow"
5. Monitor execution

---

### Example 3: Multi-Agent with Monitoring

**LLM Config:** (as above)

**Agents:**
- Agent 1: Research Agent (port 8001)
- Agent 2: Analysis Agent (port 8002)

**Monitoring:**
- Server 1: Production (192.168.1.100:22)
- Server 2: Staging (192.168.1.101:22)

**Test Flow:**
1. Configure all components
2. Test each component individually
3. Start flow execution
4. Monitor server metrics
5. View execution logs

---

## 🎯 Quick Start Guide

### For First-Time Setup:

1. **Configure LLM** (2 minutes)
   - LLM Config page
   - Enter server details
   - Test & Save

2. **Test Topology** (1 minute)
   - Topology page
   - Click "Start Flow"
   - Watch execution

3. **Add Monitoring** (3 minutes)
   - Monitoring page
   - Add servers
   - Add credentials
   - View metrics

**Total Time: ~6 minutes to full setup!**

---

## 📊 Configuration Flow Diagram

```
┌─────────────────┐
│   LLM Config    │ → .env file
│  (Server, Port) │
└─────────────────┘
         ↓
┌─────────────────┐
│  Admin Panel    │ → agents.json
│  (Add Agents)   │
└─────────────────┘
         ↓
┌─────────────────┐
│  Tools Config   │ → tools.json
│  (Add Tools)    │
└─────────────────┘
         ↓
┌─────────────────┐
│   Monitoring    │ → monitoring_servers.json
│  (Add Servers)  │
└─────────────────┘
         ↓
┌─────────────────┐
│    Topology     │ → Execute & Test
│  (Start Flow)   │
└─────────────────┘
```

---

## 🔐 Security Notes

### Credentials Storage

- **Passwords**: Encrypted before storage
- **API Keys**: Stored securely in database
- **Tokens**: Never logged or displayed in plain text

### File Permissions

- Configuration files: Read/Write by application only
- Backup files: Automatic creation before updates
- Sensitive data: Encrypted in database

---

## 💡 Best Practices

### 1. Always Test Before Saving
- Use "Test Connection" buttons
- Verify green checkmarks
- Check error messages

### 2. Use Descriptive Names
- Agent names: `research_agent`, `analysis_agent`
- Server names: `Production Server`, `Staging DB`
- Tool names: `web_search_google`, `code_executor_python`

### 3. Monitor Regularly
- Check server metrics daily
- Review execution logs
- Test components weekly

### 4. Backup Configurations
- Automatic backups created
- Manual export available
- Keep external backups

---

## 🎉 Summary

### Where to Add Inputs:

| Configuration Type | GUI Location | File Updated |
|-------------------|--------------|--------------|
| LLM Server | **LLM Config** page | `.env` |
| External Agents | **Admin Panel** → Agents | `agents.json` |
| Data Sources | **Admin Panel** → Data Sources | `datasources.json` |
| Tools | **Tools Config** page | `tools.json` |
| Monitoring Servers | **Monitoring** page | `monitoring_servers.json` |

### How to Test Flow:

1. ✅ Configure LLM in **LLM Config**
2. ✅ Add agents in **Admin Panel** (optional)
3. ✅ Go to **Topology** page
4. ✅ Click **"Start Flow"** button
5. ✅ Watch real-time execution
6. ✅ Test individual components
7. ✅ View execution logs
8. ✅ Monitor server metrics in **Monitoring** page

---

**That's it!** Your agentic AI configuration is now complete and all changes are automatically saved to the appropriate configuration files.

**Next:** Click "Start Flow" on the Topology page to see your AI system in action! 🚀
