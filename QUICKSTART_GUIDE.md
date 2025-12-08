# AIPanel Quick Start Guide

This guide will help you get started with AIPanel, a generic AI orchestrator for enterprises.

## Prerequisites

- Python 3.9+
- pip
- Virtual environment (optional but recommended)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/aipanel.git
   cd aipanel
   ```

2. Create and activate a virtual environment (optional):
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

AIPanel uses configuration files to define LLMs, tools, agents, and topologies. Sample configuration files are provided in the `config` directory.

1. Copy the example configuration files:
   ```bash
   cp config/example.env .env
   ```

2. Edit the `.env` file to set your environment-specific settings:
   ```
   # Database settings
   DB_HOST=localhost
   DB_PORT=5432
   DB_USER=aipanel
   DB_PASSWORD=your_password
   DB_NAME=aipanel

   # LLM settings
   DEFAULT_LLM=ollama
   OLLAMA_HOST=localhost
   OLLAMA_PORT=11434
   OLLAMA_MODEL=llama2

   # API settings
   API_KEY_REQUIRED=false
   ```

## Running AIPanel

1. Start the AIPanel server:
   ```bash
   python -m aipanel.server
   ```

2. The server will start on http://localhost:8000 by default.

## Using the API

### Chat Endpoint

The main endpoint for interacting with AIPanel is `/api/chat`:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the capital of France?",
    "client_id": "test_client"
  }'
```

Response:
```json
{
  "message": "The capital of France is Paris.",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "run_id": "550e8400-e29b-41d4-a716-446655440001",
  "metadata": {
    "execution_time": 1.25,
    "llm": "ollama",
    "model": "llama2"
  }
}
```

### Flow Execution Endpoint

For batch processing or workflow execution, use the `/api/flow/execute` endpoint:

```bash
curl -X POST http://localhost:8000/api/flow/execute \
  -H "Content-Type: application/json" \
  -d '{
    "topology": "batch_processor",
    "input": {
      "data": ["item1", "item2", "item3"],
      "operation": "process"
    }
  }'
```

Response:
```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440002",
  "status": "queued",
  "metadata": {
    "queue_time": 1620000000.0,
    "topology": "batch_processor"
  }
}
```

### Flow Status Endpoint

Check the status of a flow execution:

```bash
curl -X GET http://localhost:8000/api/flow/status/550e8400-e29b-41d4-a716-446655440002
```

Response:
```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440002",
  "status": "completed",
  "result": {
    "processed_items": 3,
    "output": ["processed_item1", "processed_item2", "processed_item3"]
  },
  "metadata": {
    "execution_time": 2.5
  }
}
```

## Monitoring

AIPanel provides monitoring endpoints to check the health of the system:

```bash
curl -X GET http://localhost:8000/api/monitoring/summary
```

Response:
```json
{
  "status": "healthy",
  "components": {
    "llm": {
      "status": "healthy",
      "latency_ms": 150
    },
    "database": {
      "status": "healthy",
      "connections": 5
    },
    "api": {
      "status": "healthy",
      "requests_per_minute": 10
    }
  },
  "metrics": {
    "requests_total": 1000,
    "average_latency_ms": 200,
    "error_rate": 0.01
  }
}
```

## Customization

### Adding a New LLM

1. Create a new LLM configuration in the database or config file:
   ```json
   {
     "id": "my_llm",
     "type": "openai",
     "api_key": "your_api_key",
     "model": "gpt-4"
   }
   ```

2. Use the LLM in your agent configuration:
   ```json
   {
     "id": "my_agent",
     "llm": "my_llm",
     "system_prompt": "You are a helpful assistant.",
     "tools": ["web_search", "calculator"]
   }
   ```

### Adding a New Tool

1. Create a new tool configuration in the database or config file:
   ```json
   {
     "id": "weather_api",
     "type": "http",
     "endpoint": "https://api.weather.com",
     "auth_type": "api_key",
     "auth_key": "your_api_key",
     "description": "Get weather information for a location"
   }
   ```

2. Use the tool in your agent configuration:
   ```json
   {
     "id": "weather_agent",
     "llm": "gpt4",
     "system_prompt": "You are a weather assistant.",
     "tools": ["weather_api"]
   }
   ```

### Creating a New Topology

1. Create a new topology configuration in the database or config file:
   ```json
   {
     "id": "weather_topology",
     "type": "langgraph",
     "entry_point": "start",
     "nodes": [
       {
         "id": "start",
         "type": "start_node"
       },
       {
         "id": "intent_router",
         "type": "intent_router_node",
         "router_name": "default_router"
       },
       {
         "id": "weather_agent",
         "type": "llm_agent_node",
         "agent_name": "weather_agent"
       },
       {
         "id": "end",
         "type": "end_node"
       }
     ],
     "edges": [
       {
         "source": "start",
         "target": "intent_router"
       },
       {
         "source": "intent_router",
         "target": "weather_agent"
       },
       {
         "source": "weather_agent",
         "target": "end"
       }
     ]
   }
   ```

## Next Steps

- Check the [API Documentation](API_DOCUMENTATION.md) for detailed API reference
- Read the [Implementation Summary](IMPLEMENTATION_SUMMARY.md) for architecture details
- Explore the [Configuration Guide](CONFIGURATION_GUIDE.md) for advanced configuration options
