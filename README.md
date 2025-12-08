# AIpanel - Enterprise AI Orchestrator

AIpanel is an enterprise-grade AI orchestration platform that enables seamless integration of LLMs, tools, and data sources for building powerful AI applications.

## Features

- **LangGraph Orchestration**: State machine-based orchestration for complex AI workflows
- **LangChain Tools**: Pre-built tools for data access, web search, and more
- **Database-Backed Memory**: Persistent conversation history and caching
- **Configurable Agents**: Create and configure agents with different capabilities
- **Secure API**: JWT and API key authentication for secure access
- **TLS Support**: Secure communication with TLS certificates
- **Topology Management**: Visual configuration of orchestration flows
- **Extensible Architecture**: Easy to add new tools, data sources, and capabilities

## Project Structure

```
app/
├── api/                  # API endpoints
│   ├── routes_chat.py    # Chat endpoints
│   ├── routes_config.py  # Configuration endpoints
│   ├── routes_certs.py   # Certificate management endpoints
│   └── routes_topology.py # Topology management endpoints
├── db/                   # Database models and session management
│   ├── models.py         # SQLAlchemy models
│   └── session.py        # Database session management
├── llm/                  # LLM integration
│   ├── client.py         # Generic LLM client
│   └── prompts.py        # System prompt management
├── orchestrator/         # Orchestration components
│   ├── executor.py       # Flow execution
│   ├── graph.py          # LangGraph orchestrator
│   ├── langchain_tools.py # LangChain tools
│   └── memory.py         # Conversation memory
├── config.py             # Configuration settings
├── main.py               # Application entry point
└── security.py           # Authentication and authorization
```

## Requirements

- Python 3.9+
- FastAPI
- SQLAlchemy
- LangChain
- LangGraph
- Redis (optional, for memory and caching)
- PostgreSQL (optional, for database)

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
