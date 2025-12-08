# Architecture Components Location Guide

## 📍 Where Everything Exists in the Codebase

This document maps all major architectural components to their file locations.

---

## 🔗 LangChain Components

### LangChain Tools
**Location:** `app/orchestrator/langchain_tools.py`
- Custom LangChain tool implementations
- Tool wrappers for external services
- Tool registry and management

**Location:** `backend/orchestrator/app/tools/`
- `base.py` - Base tool class
- `http_tool.py` - HTTP request tool
- `web_search_tool.py` - Web search tool
- `code_executor_tool.py` - Code execution tool
- `registry.py` - Tool registry

### LangChain Integration
**Location:** `app/orchestrator/executor.py`
- LangChain execution logic
- Tool invocation
- Chain management

---

## 🕸️ LangGraph Components

### LangGraph Implementation
**Location:** `app/orchestrator/graph.py`
- LangGraph workflow definition
- Node connections
- State management
- Graph execution logic

**Location:** `backend/orchestrator/app/graph.py`
- Alternative LangGraph implementation
- Graph topology
- Workflow orchestration

### LangGraph Nodes
**Location:** `core/topology/nodes/`
- `start_node.py` - Entry point node
- `intent_router_node.py` - Intent routing
- `planner_node.py` - Planning logic
- `llm_agent_node.py` - LLM agent execution
- `external_agent_node.py` - External agent calls
- `tool_executor_node.py` - Tool execution
- `grounding_node.py` - Response grounding
- `memory_store_node.py` - Memory storage
- `audit_node.py` - Audit logging
- `end_node.py` - Termination node
- `error_handler_node.py` - Error handling

### Topology Engine
**Location:** `core/topology/topology_engine.py`
- Graph execution engine
- Node orchestration
- State transitions
- Flow control

### Topology API
**Location:** `backend/orchestrator/app/api/topology_execution.py`
- REST API for topology execution
- Graph execution endpoints
- Status monitoring

**Location:** `app/api/routes_topology.py`
- Topology management routes
- Graph configuration endpoints

---

## 💾 Caching DB (Redis/In-Memory)

### Cache Implementation
**Location:** `backend/orchestrator/app/memory/cache.py`
- Cache service implementation
- Redis integration
- In-memory fallback
- Cache operations (get, set, delete)

**Location:** `core/memory_cache/cache_service.py`
- Cache service interface
- Cache strategies
- TTL management
- Cache invalidation

### Cache Usage
**Location:** `app/orchestrator/memory.py`
- Memory and cache integration
- Cache decorators
- Cache warming

---

## 🧠 Memory DB (Conversation/State Storage)

### Memory Implementation
**Location:** `backend/orchestrator/app/memory/`
- `conversation_memory.py` - Conversation history storage
- `state_store.py` - State persistence
- `cache.py` - Caching layer

**Location:** `core/memory_cache/memory_service.py`
- Memory service interface
- Conversation management
- State management

### Memory API
**Location:** `backend/orchestrator/app/api/memory.py`
- REST API for memory operations
- Conversation endpoints
- State management endpoints

### Memory Integration
**Location:** `app/orchestrator/memory.py`
- Memory integration with LangChain
- Conversation buffer
- Memory retrieval

---

## 🗄️ Database Components

### SQLite Database
**Location:** `backend/orchestrator/app/db/`
- `database.py` - Database connection and session management
- `models.py` - SQLAlchemy models (credentials, agents, tools, etc.)
- `__init__.py` - Database initialization

**Location:** `app/db/`
- `session.py` - Database session management
- `models.py` - Data models
- `init_db.py` - Database initialization script

### Database Models
**Location:** `backend/orchestrator/app/db/models.py`
```python
# Models include:
- Credential (encrypted credentials storage)
- Agent (agent configurations)
- Tool (tool definitions)
- Datasource (data source configs)
- Conversation (chat history)
- Message (individual messages)
```

---

## 🔧 Configuration & Settings

### Configuration Service
**Location:** `core/config/config_service.py`
- Configuration management
- Settings loading
- Environment variables

**Location:** `backend/orchestrator/app/config.py`
- Application configuration
- Settings class
- Configuration validation

**Location:** `app/config.py`
- Main configuration
- Environment settings

---

## 🤖 LLM Integration

### LLM Client
**Location:** `backend/orchestrator/app/clients/llm_client.py`
- LLM API client
- Ollama integration
- OpenAI-compatible API support
- Retry logic
- Error handling

**Location:** `app/llm/client.py`
- Alternative LLM client
- Model management

### LLM Registry
**Location:** `core/llm/llm_registry.py`
- LLM model registry
- Model configuration
- Model selection

### LLM API
**Location:** `backend/orchestrator/app/api/llm.py`
- REST API for LLM operations
- Model testing
- Configuration management

### LLM Prompts
**Location:** `app/llm/prompts.py`
- System prompts
- Prompt templates
- Prompt management

---

## 🎯 Routing & Planning

### Router
**Location:** `backend/orchestrator/app/reasoning/router_prompt.py`
- Intent routing logic
- Route selection
- Router prompts

**Location:** `core/planner_router/router_registry.py`
- Router registry
- Router configurations

### Planner
**Location:** `backend/orchestrator/app/reasoning/planner.py`
- Planning logic
- Task decomposition
- Plan execution

**Location:** `core/planner_router/planner_registry.py`
- Planner registry
- Planner configurations

---

## 🔌 Agent Components

### Agent Registry
**Location:** `core/agent/agent_registry.py`
- Agent registration
- Agent management
- Agent discovery

### Agent API
**Location:** `backend/orchestrator/app/api/agents.py`
- REST API for agent operations
- Agent CRUD operations
- Agent testing

### External Agent Client
**Location:** `backend/orchestrator/app/clients/external_agent_client.py`
- External agent communication
- Agent API calls
- Health checks

---

## 🛠️ Tool Components

### Tool Registry
**Location:** `core/tools/tool_registry.py`
- Tool registration
- Tool discovery
- Tool management

**Location:** `backend/orchestrator/app/tools/registry.py`
- Tool registry implementation
- Tool loading

### Tool API
**Location:** `backend/orchestrator/app/api/tools.py`
- REST API for tool operations
- Tool CRUD operations
- Tool testing

---

## 📊 Monitoring & Services

### Monitoring Service
**Location:** `monitoring/monitoring_service.py`
- System monitoring
- Health checks
- Metrics collection

### Service Control
**Location:** `monitoring/service_control.py`
- Service management
- Service restart
- Service status

### Monitoring API
**Location:** `backend/orchestrator/app/api/monitoring.py`
- REST API for monitoring
- Health endpoints
- Metrics endpoints

---

## 🔐 Security Components

### Credentials
**Location:** `backend/orchestrator/app/security/credentials.py`
- Credential encryption
- Fernet encryption
- Key management

**Location:** `app/security.py`
- Security utilities
- Authentication
- Authorization

### Credentials Service
**Location:** `backend/orchestrator/app/services/credentials_service.py`
- Credential CRUD operations
- Encryption/decryption
- Credential validation

### Credentials API
**Location:** `backend/orchestrator/app/api/credentials.py`
- REST API for credentials
- Secure credential management

---

## 🌐 API Layer

### Main API
**Location:** `backend/orchestrator/app/main.py`
- FastAPI application
- Router registration
- CORS configuration
- Middleware setup

**Location:** `app/main.py`
- Alternative main application

### HTTP API
**Location:** `api/http_api.py`
- HTTP API implementation
- Request handling

### API Routes
**Location:** `app/api/`
- `routes_chat.py` - Chat endpoints
- `routes_topology.py` - Topology endpoints
- `routes_config.py` - Configuration endpoints
- `routes_certs.py` - Certificate endpoints

---

## 💬 Chat Components

### Chat Router
**Location:** `backend/orchestrator/app/services/chat_router.py`
- Chat message routing
- Conversation management
- Response generation

### Chat API
**Location:** `backend/orchestrator/app/api/chat.py`
- REST API for chat
- Message endpoints
- Conversation endpoints

**Location:** `backend/orchestrator/app/api/chat_ui.py`
- Chat UI specific endpoints
- Streaming support

---

## 📁 Data Sources

### Datasource Client
**Location:** `backend/orchestrator/app/clients/datasource_client.py`
- Datasource connections
- Query execution
- Health checks

### Datasource API
**Location:** `backend/orchestrator/app/api/datasources.py`
- REST API for datasources
- Datasource CRUD operations
- Query testing

---

## 🎨 Frontend Components

### React Pages
**Location:** `frontend/src/pages/`
- `Dashboard.tsx` - Main dashboard with Kuwait map
- `LLMConnections.tsx` - LLM configuration
- `AgentsConfig.tsx` - Agent management
- `ToolsDataSources.tsx` - Tools and datasources
- `Topology.tsx` - LangGraph visualization
- `CredentialsSecurity.tsx` - Credential management
- `Certificates.tsx` - TLS certificates
- `MonitoringServices.tsx` - Monitoring dashboard
- `ChatStudio.tsx` - Chat interface

### React Components
**Location:** `frontend/src/components/`
- `Sidebar.tsx` - Navigation sidebar
- `chat/ChatMessage.tsx` - Chat message component
- `chat/ChatInput.tsx` - Chat input component
- `chat/ConversationList.tsx` - Conversation list

---

## 📦 Dependencies

### Backend Requirements
**Location:** `backend/orchestrator/requirements.txt`
```
fastapi
uvicorn
sqlalchemy
langchain
langgraph
redis (optional)
cryptography
httpx
pydantic
```

### Frontend Dependencies
**Location:** `frontend/package.json`
```
react
react-router-dom
@mui/material
axios
```

---

## 🗺️ Architecture Flow

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                      │
│  Dashboard | LLM | Agents | Tools | Topology | Chat    │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP/REST API
┌────────────────────────▼────────────────────────────────┐
│              FastAPI Backend (main.py)                   │
│  ┌──────────┬──────────┬──────────┬──────────────────┐ │
│  │ LLM API  │Agent API │Tool API  │ Topology API     │ │
│  └────┬─────┴────┬─────┴────┬─────┴────┬─────────────┘ │
└───────┼──────────┼──────────┼──────────┼───────────────┘
        │          │          │          │
┌───────▼──────────▼──────────▼──────────▼───────────────┐
│              Core Services Layer                         │
│  ┌──────────┬──────────┬──────────┬──────────────────┐ │
│  │LLM Client│  Agents  │  Tools   │  LangGraph       │ │
│  └────┬─────┴────┬─────┴────┬─────┴────┬─────────────┘ │
└───────┼──────────┼──────────┼──────────┼───────────────┘
        │          │          │          │
┌───────▼──────────▼──────────▼──────────▼───────────────┐
│           Data & Memory Layer                            │
│  ┌──────────┬──────────┬──────────┬──────────────────┐ │
│  │ SQLite   │  Redis   │ Memory   │  Cache           │ │
│  │   DB     │  Cache   │  Store   │  Service         │ │
│  └──────────┴──────────┴──────────┴──────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 Quick Reference

### To Configure LangChain:
- Edit: `app/orchestrator/langchain_tools.py`
- Configure: `backend/orchestrator/app/tools/`

### To Configure LangGraph:
- Edit: `app/orchestrator/graph.py`
- Configure nodes: `core/topology/nodes/`
- Manage topology: Frontend → Topology page

### To Configure Cache:
- Edit: `backend/orchestrator/app/memory/cache.py`
- Configure: Environment variable `REDIS_URL`
- Manage: Frontend → Memory & Cache page

### To Configure Memory:
- Edit: `backend/orchestrator/app/memory/conversation_memory.py`
- Database: SQLite at `./credentials.db`
- Manage: Frontend → Memory & Cache page

### To Configure Database:
- Models: `backend/orchestrator/app/db/models.py`
- Connection: `backend/orchestrator/app/db/database.py`
- Initialize: `backend/orchestrator/scripts/init_db.py`

---

## 📝 Summary

All components are organized in a modular architecture:

- **LangChain**: `app/orchestrator/` and `backend/orchestrator/app/tools/`
- **LangGraph**: `app/orchestrator/graph.py` and `core/topology/`
- **Cache DB**: `backend/orchestrator/app/memory/cache.py` and `core/memory_cache/`
- **Memory DB**: `backend/orchestrator/app/memory/` (SQLite-based)
- **Configuration**: All manageable through the GUI

The GUI provides full access to configure and manage all these components without touching code!
