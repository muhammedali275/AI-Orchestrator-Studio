# exampleOne Orchestrator Studio - Backend

A modular, graph-based orchestration backend for AI agents and tools.

## Architecture Overview

The orchestrator implements a clean, modular flow:

```
Client (Web UI / n8n)
  ↓
Orchestrator API (/v1/chat)
  ↓
Intent Router (classify request)
  ↓
Planner (decompose complex tasks)
  ↓
Execution Layer:
  - LLM Agent
  - External Agent (e.g., example_agent)
  - Tool Executor
  - Grounding/RAG
  ↓
Memory & Cache
  ↓
Final Response
```

## Key Design Principles

1. **No Hard-Coded Values**: All connectivity (IPs, ports, URLs, credentials) comes from environment variables via `Settings`
2. **Separation of Concerns**: Orchestration logic is separate from infrastructure
3. **Modular Architecture**: Each component is independently testable
4. **Configuration-Driven**: Tools, agents, and data sources are configured via GUI/config files
5. **Async-First**: Built on FastAPI with async/await throughout

## Directory Structure

```
backend/orchestrator/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Pydantic Settings (NO hard-coded values)
│   ├── graph.py             # Orchestration graph/state machine
│   │
│   ├── api/                 # REST API endpoints
│   │   ├── __init__.py
│   │   ├── chat.py          # /v1/chat endpoint
│   │   ├── llm.py           # LLM management
│   │   ├── tools.py         # Tools management
│   │   ├── monitoring.py    # Metrics and monitoring
│   │   ├── memory.py        # Memory management
│   │   └── db.py            # Database management
│   │
│   ├── clients/             # External service clients
│   │   ├── __init__.py
│   │   ├── llm_client.py    # Generic LLM client
│   │   ├── external_agent_client.py  # External agent HTTP client
│   │   └── datasource_client.py      # Data source client
│   │
│   ├── memory/              # Memory and state management
│   │   ├── __init__.py
│   │   ├── conversation_memory.py  # Conversation history
│   │   ├── cache.py                # Response caching
│   │   └── state_store.py          # Graph state persistence
│   │
│   ├── tools/               # Tool framework
│   │   ├── __init__.py
│   │   ├── base.py          # Base tool abstractions
│   │   ├── http_tool.py     # Generic HTTP tool
│   │   ├── web_search_tool.py     # Web search
│   │   ├── code_executor_tool.py  # Code execution
│   │   └── registry.py      # Dynamic tool registration
│   │
│   └── reasoning/           # Intent and planning logic
│       ├── __init__.py
│       ├── router_prompt.py # Intent classification
│       └── planner.py       # Task decomposition
│
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
└── README.md               # This file
```

## Installation

1. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Configuration

All configuration is managed through environment variables (see `.env.example`).

### Required Configuration

The orchestrator requires at minimum:
- `LLM_BASE_URL` and `LLM_DEFAULT_MODEL` for LLM functionality
- `REDIS_URL` or `REDIS_HOST` for memory/cache (optional, falls back to in-memory)

### Optional Configuration

- **External Agent**: `EXTERNAL_AGENT_BASE_URL`, `EXTERNAL_AGENT_AUTH_TOKEN`
- **Data Source**: `DATASOURCE_BASE_URL`, `DATASOURCE_AUTH_TOKEN`
- **PostgreSQL**: `POSTGRES_DSN` or individual connection params
- **Vector DB**: `VECTOR_DB_URL`, `VECTOR_DB_API_KEY`
- **Tools**: Configure via `TOOLS_CONFIG_PATH` or GUI

## Running the Application

### Development Mode

```bash
cd backend/orchestrator
python -m app.main
```

Or with uvicorn directly:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### Main Orchestration

- `POST /v1/chat` - Main chat/orchestration endpoint
  ```json
  {
    "prompt": "Analyze customer churn",
    "user_id": "user123",
    "metadata": {}
  }
  ```

### Health & Status

- `GET /health` - Health check with configuration status
- `GET /` - API information

### Additional Endpoints (to be implemented)

- `GET /v1/llm/models` - List available LLM models
- `POST /v1/llm/test-connection` - Test LLM connection
- `GET /v1/tools/list` - List registered tools
- `POST /v1/tools/register` - Register new tool
- `GET /v1/memory/stats` - Memory statistics
- `POST /v1/memory/clear` - Clear memory

## Graph Execution Flow

The orchestration graph implements a state machine with the following nodes:

1. **start** → Initialize execution
2. **intent_router** → Classify user intent
3. **planner** → Decompose complex tasks (optional)
4. **llm_agent** → Call configured LLM
5. **external_agent** → Call external specialized agent
6. **tool_executor** → Execute registered tools
7. **grounding** → Retrieve/RAG data fusion
8. **memory_store** → Save conversation and results
9. **end** → Finalize and return response

## Extending the Orchestrator

### Adding New Tools

1. Create tool class inheriting from `BaseTool`:
   ```python
   from app.tools.base import BaseTool, ToolResult, ToolStatus
   
   class MyTool(BaseTool):
       async def execute(self, **kwargs) -> ToolResult:
           # Implementation
           pass
       
       def get_schema(self) -> Dict[str, Any]:
           # Return JSON schema
           pass
   ```

2. Register in `ToolRegistry.TOOL_CLASSES`

3. Configure via GUI or config file

### Adding New API Endpoints

1. Create router in `app/api/`:
   ```python
   from fastapi import APIRouter
   
   router = APIRouter(prefix="/v1/myfeature", tags=["myfeature"])
   
   @router.get("/endpoint")
   async def my_endpoint():
       return {"status": "ok"}
   ```

2. Include in `app/main.py`:
   ```python
   from .api.myfeature import router as myfeature_router
   app.include_router(myfeature_router)
   ```

### Customizing the Graph

Modify `app/graph.py` to add new nodes or change routing logic:

```python
async def my_custom_node(self, state: GraphState) -> GraphState:
    # Custom logic
    state.current_node = "next_node"
    return state

# Register in __init__
self.nodes["my_custom"] = self.my_custom_node
```

## Testing

```bash
# Run tests (when implemented)
pytest tests/

# Test specific module
pytest tests/test_graph.py

# With coverage
pytest --cov=app tests/
```

## Monitoring

The orchestrator provides:
- Execution state persistence (Redis)
- Conversation history tracking
- Response caching
- Metrics export (when monitoring enabled)

## Security Considerations

1. **Never commit `.env` file** - Contains sensitive credentials
2. **Use environment variables** - All secrets via env vars
3. **Enable authentication** - Set `AUTH_ENABLED=true` in production
4. **CORS configuration** - Restrict `CORS_ORIGINS` in production
5. **Rate limiting** - Implement at reverse proxy level

## Troubleshooting

### LLM Connection Issues
- Verify `LLM_BASE_URL` is accessible
- Check `LLM_API_KEY` if required
- Test with `/v1/llm/test-connection` endpoint

### Redis Connection Issues
- Verify `REDIS_URL` or `REDIS_HOST`
- Check Redis is running: `redis-cli ping`
- Falls back to in-memory if Redis unavailable

### Tool Execution Failures
- Check tool configuration in GUI
- Verify tool endpoints are accessible
- Review logs for detailed error messages

## Contributing

1. Follow the modular architecture
2. No hard-coded values - use Settings
3. Add type hints to all functions
4. Write docstrings for public APIs
5. Test new features

## License

[Your License Here]

## Support

For issues and questions:
- GitHub Issues: [Your Repo]
- Documentation: [Your Docs]
- Email: [Your Email]
