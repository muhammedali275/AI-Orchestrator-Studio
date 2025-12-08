# AIPanel Application Architecture Map

## Overview

AIPanel is an enterprise AI orchestration platform that manages the execution of AI workflows through a topology-based approach. It provides a unified interface for internal testing and external integrations.

## System Components

### 1. Core Components

#### API Layer (`api/`)
- **http_api.py**: Main entry point for all API requests
  - Handles authentication and permission validation
  - Routes requests to appropriate services
  - Exposes `/api/chat` endpoint for all chat interactions

#### Topology Engine (`core/topology/`)
- **topology_engine.py**: Orchestrates the execution of nodes in a topology
  - Loads topology configuration from config service
  - Manages the execution flow between nodes
  - Handles state management during execution

#### Nodes (`core/topology/nodes/`)
- **start_node.py**: Initializes the execution context
- **intent_router_node.py**: Routes requests based on intent
- **planner_node.py**: Plans the execution steps
- **llm_agent_node.py**: Executes LLM-based agents
- **external_agent_node.py**: Interfaces with external agent APIs
- **tool_executor_node.py**: Executes tools based on agent output
- **grounding_node.py**: Ensures responses are grounded in facts
- **memory_store_node.py**: Stores conversation history
- **audit_node.py**: Logs execution for auditing
- **end_node.py**: Finalizes the execution
- **error_handler_node.py**: Handles exceptions during execution

#### Registries (`core/`)
- **llm_registry.py**: Manages LLM providers and models
- **tool_registry.py**: Manages available tools
- **agent_registry.py**: Manages agent configurations
- **planner_registry.py**: Manages planning strategies
- **router_registry.py**: Manages routing strategies

#### Memory & Caching (`core/memory_cache/`)
- **memory_service.py**: Manages conversation history
- **cache_service.py**: Caches responses for efficiency

#### Configuration (`core/config/`)
- **config_service.py**: Manages system configuration

### 2. Monitoring & Service Control

#### Monitoring (`monitoring/`)
- **monitoring_service.py**: Monitors system health
  - Checks VM health (CPU, RAM, disk)
  - Monitors external LLM VM
  - Checks service health
- **service_control.py**: Controls service lifecycle
  - Restarts services when needed
  - Executes pre-configured commands

### 3. Frontend Components

#### Pages
- **Topology.tsx**: Visualizes and manages topology execution
- **Monitoring.tsx**: Displays system health and metrics
- **ChatStudio.tsx**: Internal testing interface for chat
- **SystemConfig.tsx**: Configuration management

## Data Flow

### Main Chat Flow

```
Client (GUI or External) → /api/chat → http_api.py → topology_engine.execute() → Nodes Execution → Response
```

1. **Request Handling**:
   - Client sends request to `/api/chat`
   - http_api.py authenticates and validates permissions
   - Request is forwarded to topology_engine

2. **Topology Execution**:
   - topology_engine loads the topology configuration
   - Executes nodes in sequence:
     1. start_node
     2. intent_router_node
     3. planner_node
     4. llm_agent_node or external_agent_node
     5. tool_executor_node
     6. grounding_node
     7. memory_store_node
     8. audit_node
     9. end_node
     10. error_handler_node (on exceptions)

3. **Response Handling**:
   - Result is returned to http_api.py
   - http_api.py formats and returns response to client

### Monitoring Flow

```
Monitoring Service → Target Systems → Metrics Collection → API Endpoints → Frontend Display
```

1. **Metrics Collection**:
   - monitoring_service periodically checks targets
   - Metrics are stored and exposed via API

2. **Service Control**:
   - service_control executes commands to restart services
   - Commands are configured via config_service

## Integration with API Gateway

To share the AIPanel orchestrator with an API Gateway VM:

1. **Deployment**:
   - Deploy AIPanel on a dedicated VM
   - Configure network to allow communication between VMs

2. **API Gateway Configuration**:
   - Configure API Gateway to route requests to AIPanel's `/api/chat` endpoint
   - Set up authentication and rate limiting

3. **Client Configuration**:
   - Clients connect to API Gateway
   - API Gateway forwards requests to AIPanel
   - AIPanel processes requests and returns responses

4. **Security**:
   - Use API keys for authentication
   - Configure RBAC for access control
   - Implement TLS for secure communication

## File Structure and Dependencies

```
api/
├── http_api.py                  # Main API entry point
core/
├── config/
│   └── config_service.py        # Configuration management
├── llm/
│   └── llm_registry.py          # LLM provider management
├── tools/
│   └── tool_registry.py         # Tool management
├── agent/
│   └── agent_registry.py        # Agent management
├── planner_router/
│   ├── planner_registry.py      # Planner management
│   └── router_registry.py       # Router management
├── memory_cache/
│   ├── memory_service.py        # Conversation history
│   └── cache_service.py         # Response caching
├── topology/
│   ├── topology_engine.py       # Topology execution
│   └── nodes/
│       ├── start_node.py        # Execution initialization
│       ├── intent_router_node.py # Intent-based routing
│       ├── planner_node.py      # Execution planning
│       ├── llm_agent_node.py    # LLM agent execution
│       ├── external_agent_node.py # External agent integration
│       ├── tool_executor_node.py # Tool execution
│       ├── grounding_node.py    # Response grounding
│       ├── memory_store_node.py # Memory storage
│       ├── audit_node.py        # Execution auditing
│       ├── end_node.py          # Execution finalization
│       └── error_handler_node.py # Error handling
monitoring/
├── monitoring_service.py        # System monitoring
└── service_control.py           # Service lifecycle management
frontend/
└── src/
    └── pages/
        ├── Topology.tsx         # Topology visualization
        ├── Monitoring.tsx       # System monitoring UI
        ├── ChatStudio.tsx       # Chat testing interface
        └── SystemConfig.tsx     # Configuration UI
