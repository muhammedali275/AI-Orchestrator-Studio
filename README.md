<div align="center">
  <img src="AOS-2.png" alt="AI Orchestrator Studio" width="200"/>
  
  # AI Orchestrator Studio
  
  **A comprehensive web-based platform for orchestrating AI workflows, managing LLM connections, and building intelligent conversational applications.**
  
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
  [![React 18.2+](https://img.shields.io/badge/react-18.2+-61dafb.svg)](https://reactjs.org/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com/)
  
</div>

---

**AI Orchestrator Studio** provides a full-stack solution with an intuitive React frontend and a powerful FastAPI backend.

---

## 🎯 Overview

AI Orchestrator Studio enables organizations to:
- Connect to multiple LLM providers (Ollama, OpenAI-compatible APIs, custom endpoints)
- Build and test conversational AI workflows with different routing strategies
- Manage tools, data sources, and external agents
- Monitor system status and performance
- Configure everything through an intuitive web interface

---

## 🏗️ Architecture

### Frontend (React + TypeScript + Material-UI)
Modern single-page application with 10+ functional pages:

**Core Pages:**
1. **Dashboard** (`/`) - System overview, quick stats, recent activity
2. **Chat Studio** (`/chat-studio`) - Interactive chat interface with model selection and routing profiles
3. **LLM Connections** (`/llm-connections`) - Manage external LLM server connections
4. **Router Planner** (`/router-planner`) - Visual workflow designer and routing configuration
5. **Data Sources** (`/datasources`) - Configure CubeJS and external data connections
6. **Tools Configuration** (`/tools`) - Manage available tools and their settings
7. **Agents Configuration** (`/agents`) - Configure external AI agents
8. **System Configuration** (`/system-config`) - Centralized system settings
9. **Upgrades** (`/upgrades`) - System updates and version management
10. **Admin Panel** (`/admin`) - User management and system monitoring

### Backend (FastAPI + Python)
RESTful API server with comprehensive functionality:

**API Endpoints:**
- `/api/chat/ui/*` - Chat streaming and conversation management
- `/api/config/*` - Configuration management (LLM, tools, datasources, agents)
- `/api/admin/*` - Administrative functions
- `/api/topology/*` - Workflow and routing management

**Core Services:**
- `ChatRouter` - Routes messages to appropriate LLM/agent/tool chain
- `LLMClient` - Unified interface for multiple LLM providers
- `ExternalAgentClient` - Integration with external AI agents
- `CredentialManager` - Secure credential storage (SQLite)

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.9+** (backend)
- **Node.js 16+** (frontend)
- **Git** (optional, for updates)

### Installation

**1. Clone or extract the project:**
```bash
git clone <repository-url>
cd AI-Orchestrator-Studio
```

**2. Start Backend:**
```bash
# Windows
.\start-backend.bat

# Linux/Mac
./start-backend.sh
```

**3. Start Frontend (in new terminal):**
```bash
# Windows
.\start-frontend.bat

# Linux/Mac
./start-frontend.sh
```

**4. Access the Application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 📁 Project Structure

```
AI-Orchestrator-Studio/
├── frontend/                  # React application
│   ├── src/
│   │   ├── pages/            # 10 main application pages
│   │   ├── components/       # Reusable UI components
│   │   ├── App.tsx           # Main app with routing
│   │   └── index.tsx         # Entry point
│   ├── public/               # Static assets
│   └── package.json          # Frontend dependencies
│
├── backend/orchestrator/      # FastAPI application
│   ├── app/
│   │   ├── api/              # API route handlers
│   │   │   ├── chat_ui.py    # Chat endpoints
│   │   │   ├── config_management.py  # Configuration APIs
│   │   │   └── admin.py      # Admin endpoints
│   │   ├── services/         # Business logic
│   │   │   ├── chat_router.py    # Message routing
│   │   │   ├── llm_client.py     # LLM integrations
│   │   │   └── credential_manager.py  # Security
│   │   ├── config.py         # Settings management
│   │   └── main.py           # FastAPI app entry
│   ├── config/               # Configuration files
│   │   ├── llm_connections.json   # LLM server configs
│   │   ├── tools.json             # Tool definitions
│   │   ├── datasources.json       # Data source configs
│   │   └── agents.json            # Agent configurations
│   └── .env                  # Environment variables
│
├── start-all.bat/sh          # Start both frontend + backend
├── start-backend.bat/sh      # Start backend only
├── start-frontend.bat/sh     # Start frontend only
└── README.md                 # This file
```

---

## 🔧 Configuration

### LLM Connections
Configure external LLM servers via GUI (`/llm-connections`) or JSON:

```json
{
  "id": "llm-1234567890",
  "name": "Production Ollama",
  "base_url": "http://10.99.70.200:11434",
  "model": "qwen2.5-72b",
  "timeout": 120,
  "max_tokens": 4096
}
```

### Routing Profiles
Two routing strategies available in Chat Studio:

1. **Direct LLM** - Send messages directly to selected LLM
2. **Tools + Data** - Full orchestration with tools, data sources, and reasoning

### Environment Variables
Key backend settings in `backend/orchestrator/.env`:

```env
APP_NAME=AI Orchestrator Studio
DEBUG=True
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000
```

---

## 🌐 Sitemap

### User Interface Navigation

```
AI Orchestrator Studio
│
├── 🏠 Dashboard (/)
│   └── System overview, stats, quick actions
│
├── 💬 Chat Studio (/chat-studio)
│   ├── Model Selection (dropdown with all LLM connections)
│   ├── Routing Profile Selection (Direct LLM / Tools+Data)
│   ├── Conversation Management
│   └── Real-time Streaming Responses
│
├── 🔌 LLM Connections (/llm-connections)
│   ├── Add New Connection
│   ├── Test Connectivity
│   ├── View Available Models
│   └── Edit/Delete Connections
│
├── 🗺️ Router Planner (/router-planner)
│   ├── Visual Workflow Designer
│   ├── Routing Logic Configuration
│   └── Topology Management
│
├── 📊 Data Sources (/datasources)
│   ├── CubeJS Configuration
│   ├── Custom API Endpoints
│   └── Database Connections
│
├── 🛠️ Tools Configuration (/tools)
│   ├── Enable/Disable Tools
│   ├── Tool Settings
│   └── Custom Tool Integration
│
├── 🤖 Agents Configuration (/agents)
│   ├── External Agent URLs
│   ├── Authentication Tokens
│   └── Agent Capabilities
│
├── ⚙️ System Configuration (/system-config)
│   ├── LLM Settings
│   ├── Database Configuration
│   ├── External Agents
│   └── Data Sources
│
├── 📦 Upgrades (/upgrades)
│   ├── Available Updates
│   ├── Version History
│   └── Rollback Options
│
└── 👤 Admin Panel (/admin)
    ├── User Management
    ├── System Metrics
    ├── Feature Flags
    └── Logs Viewer
```

### API Endpoints

```
Backend API (http://localhost:8000)
│
├── /api/chat/ui/
│   ├── POST /send/stream          # Stream chat response
│   ├── GET /conversations         # List conversations
│   ├── GET /conversations/{id}    # Get conversation history
│   └── GET /profiles              # Get routing profiles
│
├── /api/config/
│   ├── POST /llm-connections      # Add LLM connection
│   ├── GET /llm-connections       # List connections
│   ├── GET /llm-connections/{id}/models  # Get models for connection
│   ├── POST /tools                # Save tools config
│   ├── POST /datasources          # Save datasources config
│   └── POST /agents               # Save agents config
│
├── /api/admin/
│   ├── GET /users                 # List users
│   ├── GET /metrics               # System metrics
│   └── GET /feature-flags         # Feature toggles
│
└── /docs                          # OpenAPI/Swagger documentation
```

---

## 🔒 Security

- **Credential Storage**: SQLite database (`credentials.db`) for secure credential management
- **API Authentication**: Support for API keys and bearer tokens
- **Environment Variables**: Sensitive data stored in `.env` file (not in version control)
- **CORS**: Configured for frontend-backend communication

---

## 🧪 Testing

### Chat Studio Testing
1. Navigate to `/chat-studio`
2. Select an LLM from the dropdown (format: `connection-name : model-name`)
3. Choose routing profile ("Direct LLM" or "Tools + Data")
4. Send a test message
5. Verify streaming response appears correctly

### LLM Connection Testing
1. Go to `/llm-connections`
2. Click "Add Connection"
3. Enter server details (URL, model, etc.)
4. Click "Save" - connection is automatically tested
5. Check for success message with latency
6. Verify models appear in Chat Studio dropdown

---

## 📦 Production Deployment

### RHEL 9 / Linux Production Setup
See deployment scripts:
- `deploy-to-rhel9.sh` - Full automated deployment
- `start-all-universal.sh` - Cross-platform startup script

### Docker (Future)
Docker support planned for future releases.

---

## 🛠️ Development

### Frontend Development
```bash
cd frontend
npm install
npm start          # Development server on port 3000
npm run build      # Production build
```

### Backend Development
```bash
cd backend/orchestrator
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📝 License

Copyright © 2025 AI Orchestrator Studio

---

## 🤝 Support

For issues, questions, or contributions:
- Check the `/docs` endpoint for API documentation
- Review configuration files in `backend/orchestrator/config/`
- Ensure all services are running (`start-all.bat/sh`)

---

**Built with ❤️ using React, TypeScript, FastAPI, and Material-UI**

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/aipanel.git
cd aipanel
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up environment variables:

```bash
# Create a .env file with your configuration
cp .env.example .env
# Edit .env with your settings
```

4. Initialize the database:

```bash
python -m app.db.init_db
```

5. Start the server:

```bash
python -m app.main
```

## Usage

### API Endpoints

- **Chat**: `/api/chat` - Send messages to agents
- **Topology**: `/api/topology` - Manage orchestration topology
- **Configuration**: `/api/config` - Manage LLM connections, tools, agents, etc.
- **Certificates**: `/api/certs` - Manage TLS certificates

### Example: Chat with an Agent

```python
import requests

response = requests.post(
    "http://localhost:8000/api/chat",
    headers={"Authorization": "Bearer YOUR_TOKEN"},
    json={
        "prompt": "What is the status of our top contracts?",
        "agent": "zain_agent",
        "user_id": "user123"
    }
)

print(response.json())
```

## Configuration

AIpanel can be configured through environment variables or a `.env` file:

- `AIPANEL_PORT`: Port to run the server on (default: 8000)
- `TLS_ENABLED`: Enable TLS (default: false)
- `TLS_CERT_PATH`: Path to TLS certificate
- `TLS_KEY_PATH`: Path to TLS key
- `DB_CONNECTION_STRING`: Database connection string
- `DEFAULT_AGENT_NAME`: Default agent name (default: zain_agent)
- `LLM_BASE_URL`: LLM server base URL
- `LLM_API_KEY`: LLM API key
- `LLM_DEFAULT_MODEL`: Default LLM model

## Security

AIpanel includes several security features:

- JWT authentication for users
- API key authentication for services
- TLS support for secure communication
- Role-based access control
- Secure credential storage

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
