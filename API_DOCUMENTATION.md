# AIpanel API Documentation

This document provides detailed information about the AIpanel API endpoints.

## Base URL

All API endpoints are relative to the base URL:

```
http://localhost:8000
```

## Authentication

Most endpoints require authentication using one of the following methods:

### API Key

Include the API key in the request header:

```
X-API-Key: your_api_key
```

### JWT Token

Include the JWT token in the request header:

```
Authorization: Bearer your_jwt_token
```

## Endpoints

### Health Check

```
GET /api/health
```

Check the health status of the API.

**Response:**

```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### User Information

```
GET /api/me
```

Get information about the authenticated user.

**Response:**

```json
{
  "username": "user123",
  "email": "user@example.com",
  "full_name": "John Doe",
  "scopes": ["admin", "user"]
}
```

### Chat

#### Send Message

```
POST /api/chat
```

Send a message to an agent.

**Request:**

```json
{
  "prompt": "What is the status of our top contracts?",
  "agent": "zain_agent",
  "user_id": "user123",
  "session_id": "session456"
}
```

**Response:**

```json
{
  "answer": "Based on the data, your top contracts by churn rate are...",
  "sources": [
    {
      "type": "cubejs",
      "name": "Churn Analytics",
      "data": "..."
    }
  ],
  "trace_id": "trace789"
}
```

#### Test Chat

```
POST /api/chat/test
```

Test chat endpoint without authentication.

**Request:**

Same as `/api/chat`.

**Response:**

Same as `/api/chat`.

#### Get Chat Sessions

```
GET /api/chat/sessions
```

Get chat sessions for the authenticated user.

**Query Parameters:**

- `user_id` (optional): Filter by user ID
- `limit` (optional): Maximum number of sessions to return (default: 10)

**Response:**

```json
{
  "sessions": [
    {
      "id": "session123",
      "user_id": "user456",
      "agent_id": "agent789",
      "title": "Conversation 2023-12-07 14:30",
      "created_at": "2023-12-07T14:30:00Z",
      "updated_at": "2023-12-07T14:45:00Z"
    }
  ]
}
```

#### Get Chat Messages

```
GET /api/chat/messages/{session_id}
```

Get chat messages for a session.

**Path Parameters:**

- `session_id`: Chat session ID

**Query Parameters:**

- `limit` (optional): Maximum number of messages to return (default: 50)

**Response:**

```json
{
  "session": {
    "id": "session123",
    "user_id": "user456",
    "agent_id": "agent789",
    "title": "Conversation 2023-12-07 14:30",
    "created_at": "2023-12-07T14:30:00Z",
    "updated_at": "2023-12-07T14:45:00Z"
  },
  "messages": [
    {
      "id": "message123",
      "chat_session_id": "session123",
      "role": "user",
      "content": "What is the status of our top contracts?",
      "created_at": "2023-12-07T14:30:00Z"
    },
    {
      "id": "message124",
      "chat_session_id": "session123",
      "role": "assistant",
      "content": "Based on the data, your top contracts by churn rate are...",
      "created_at": "2023-12-07T14:31:00Z"
    }
  ]
}
```

### Topology

#### Get Topology

```
GET /api/topology
```

Get topology configuration.

**Query Parameters:**

- `agent` (optional): Agent name (default: zain_agent)

**Response:**

```json
{
  "nodes": [
    {
      "id": "start",
      "type": "start",
      "data": {
        "label": "Start"
      }
    },
    {
      "id": "intent_router",
      "type": "router",
      "data": {
        "label": "Intent Router"
      }
    }
  ],
  "edges": [
    {
      "source": "start",
      "target": "intent_router",
      "label": "input"
    }
  ]
}
```

#### Update Topology

```
POST /api/topology
```

Update topology configuration.

**Query Parameters:**

- `agent` (optional): Agent name (default: zain_agent)

**Request:**

```json
{
  "nodes": [
    {
      "id": "start",
      "type": "start",
      "data": {
        "label": "Start"
      }
    },
    {
      "id": "intent_router",
      "type": "router",
      "data": {
        "label": "Intent Router"
      }
    }
  ],
  "edges": [
    {
      "source": "start",
      "target": "intent_router",
      "label": "input"
    }
  ]
}
```

**Response:**

```json
{
  "success": true,
  "message": "Topology updated for agent: zain_agent"
}
```

#### Get Topology Agents

```
GET /api/topology/agents
```

Get agents with topology configuration.

**Response:**

```json
[
  {
    "id": "agent123",
    "name": "zain_agent",
    "description": "Default agent for general queries",
    "has_topology": true
  },
  {
    "id": "agent456",
    "name": "data_agent",
    "description": "Specialized agent for data queries",
    "has_topology": false
  }
]
```

#### Execute Topology

```
POST /api/topology/execute
```

Execute topology with custom input.

**Query Parameters:**

- `agent` (optional): Agent name (default: zain_agent)

**Request:**

```json
{
  "input": "What is the status of our top contracts?"
}
```

**Response:**

```json
{
  "success": true,
  "result": {
    "answer": "Based on the data, your top contracts by churn rate are...",
    "sources": [
      {
        "type": "cubejs",
        "name": "Churn Analytics",
        "data": "..."
      }
    ],
    "execution_id": "exec123",
    "execution_time": 1.23,
    "timestamp": "2023-12-07T14:30:00Z"
  }
}
```

### Configuration

#### LLM Connections

```
GET /api/config/llm-connections
```

Get LLM connections.

**Response:**

```json
[
  {
    "id": "conn123",
    "name": "OpenAI",
    "provider": "openai",
    "base_url": "https://api.openai.com/v1",
    "api_key": "********",
    "default_model": "gpt-4",
    "config": {
      "timeout": 60,
      "max_retries": 3
    },
    "created_at": "2023-12-07T14:30:00Z",
    "updated_at": "2023-12-07T14:30:00Z"
  }
]
```

```
POST /api/config/llm-connections
```

Create LLM connection.

**Request:**

```json
{
  "name": "Anthropic",
  "provider": "anthropic",
  "base_url": "https://api.anthropic.com",
  "api_key": "your_api_key",
  "default_model": "claude-2",
  "config": {
    "timeout": 60,
    "max_retries": 3
  }
}
```

**Response:**

```json
{
  "id": "conn456",
  "name": "Anthropic",
  "provider": "anthropic",
  "base_url": "https://api.anthropic.com",
  "api_key": "********",
  "default_model": "claude-2",
  "config": {
    "timeout": 60,
    "max_retries": 3
  },
  "created_at": "2023-12-07T14:30:00Z",
  "updated_at": "2023-12-07T14:30:00Z"
}
```

```
GET /api/config/llm-connections/{connection_id}
```

Get LLM connection.

**Path Parameters:**

- `connection_id`: LLM connection ID

**Response:**

Same as individual connection in `GET /api/config/llm-connections`.

```
PUT /api/config/llm-connections/{connection_id}
```

Update LLM connection.

**Path Parameters:**

- `connection_id`: LLM connection ID

**Request:**

```json
{
  "name": "Anthropic Updated",
  "default_model": "claude-3"
}
```

**Response:**

```json
{
  "id": "conn456",
  "name": "Anthropic Updated",
  "provider": "anthropic",
  "base_url": "https://api.anthropic.com",
  "api_key": "********",
  "default_model": "claude-3",
  "config": {
    "timeout": 60,
    "max_retries": 3
  },
  "created_at": "2023-12-07T14:30:00Z",
  "updated_at": "2023-12-07T14:35:00Z"
}
```

```
DELETE /api/config/llm-connections/{connection_id}
```

Delete LLM connection.

**Path Parameters:**

- `connection_id`: LLM connection ID

**Response:**

```json
{
  "success": true,
  "message": "LLM connection deleted: conn456"
}
```

#### Tools

```
GET /api/config/tools
```

Get tools.

**Response:**

```json
[
  {
    "id": "tool123",
    "name": "cubejs_tool",
    "type": "data_query",
    "description": "Query Cube.js for analytics data",
    "config": {
      "timeout": 30,
      "max_retries": 3
    },
    "created_at": "2023-12-07T14:30:00Z",
    "updated_at": "2023-12-07T14:30:00Z"
  }
]
```

```
POST /api/config/tools
```

Create tool.

**Request:**

```json
{
  "name": "web_search_tool",
  "type": "web",
  "description": "Search the web for information",
  "config": {
    "timeout": 30,
    "max_retries": 3
  }
}
```

**Response:**

```json
{
  "id": "tool456",
  "name": "web_search_tool",
  "type": "web",
  "description": "Search the web for information",
  "config": {
    "timeout": 30,
    "max_retries": 3
  },
  "created_at": "2023-12-07T14:30:00Z",
  "updated_at": "2023-12-07T14:30:00Z"
}
```

#### Agents

```
GET /api/config/agents
```

Get agents.

**Response:**

```json
[
  {
    "id": "agent123",
    "name": "zain_agent",
    "description": "Default agent for general queries",
    "system_prompt": "You are a helpful AI assistant...",
    "llm_connection_id": "conn123",
    "router_config": {
      "default_route": "llm_agent",
      "routes": {
        "data_query": "tool_executor",
        "churn_analytics": "tool_executor"
      }
    },
    "planner_config": {
      "enabled": true,
      "max_iterations": 5
    },
    "created_at": "2023-12-07T14:30:00Z",
    "updated_at": "2023-12-07T14:30:00Z"
  }
]
```

```
POST /api/config/agents
```

Create agent.

**Request:**

```json
{
  "name": "data_agent",
  "description": "Specialized agent for data queries",
  "system_prompt": "You are a data analysis assistant...",
  "llm_connection_id": "conn123",
  "router_config": {
    "default_route": "tool_executor",
    "routes": {
      "general_query": "llm_agent"
    }
  },
  "planner_config": {
    "enabled": true,
    "max_iterations": 10
  },
  "tool_ids": ["tool123", "tool456"]
}
```

**Response:**

```json
{
  "id": "agent456",
  "name": "data_agent",
  "description": "Specialized agent for data queries",
  "system_prompt": "You are a data analysis assistant...",
  "llm_connection_id": "conn123",
  "router_config": {
    "default_route": "tool_executor",
    "routes": {
      "general_query": "llm_agent"
    }
  },
  "planner_config": {
    "enabled": true,
    "max_iterations": 10
  },
  "created_at": "2023-12-07T14:30:00Z",
  "updated_at": "2023-12-07T14:30:00Z"
}
```

### Certificates

```
GET /api/certs
```

Get certificate information.

**Response:**

```json
{
  "tls_enabled": true,
  "cert_path": "/path/to/cert.pem",
  "key_path": "/path/to/key.pem",
  "cert_exists": true,
  "key_exists": true
}
```

```
POST /api/certs/upload
```

Upload TLS certificates.

**Request:**

Multipart form with:
- `cert_file`: Certificate file
- `key_file`: Key file

**Response:**

```json
{
  "success": true,
  "message": "Certificates uploaded successfully",
  "cert_path": "/path/to/cert.pem",
  "key_path": "/path/to/key.pem"
}
```

```
POST /api/certs/enable
```

Enable TLS.

**Response:**

```json
{
  "success": true,
  "message": "TLS enabled successfully"
}
```

```
POST /api/certs/disable
```

Disable TLS.

**Response:**

```json
{
  "success": true,
  "message": "TLS disabled successfully"
}
```

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "detail": "Error message"
}
```

Common HTTP status codes:

- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error
