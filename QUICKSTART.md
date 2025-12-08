# AIpanel Quickstart Guide

This guide will help you quickly set up and start using AIpanel, the enterprise AI orchestrator.

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git (optional, for cloning the repository)

## Installation

### 1. Get the Code

Clone the repository or download the source code:

```bash
git clone https://github.com/yourusername/aipanel.git
cd aipanel
```

### 2. Set Up Environment

Create and activate a virtual environment:

#### On Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

#### On macOS/Linux:

```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

Install the required packages:

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file based on the example:

```bash
cp .env.example .env
```

Edit the `.env` file to set your configuration:

- Set `AIPANEL_PORT` to your desired port (default: 8000)
- Set `LLM_BASE_URL` and `LLM_API_KEY` for your LLM provider
- Adjust other settings as needed

### 5. Initialize Database

Initialize the database with default data:

```bash
python -m app.db.init_db
```

### 6. Start the Server

#### On Windows:

```bash
start.bat
```

#### On macOS/Linux:

```bash
chmod +x start.sh
./start.sh
```

The server will start on the configured port (default: 8000).

## Quick Test

### Test the API

You can test the API using the included test script:

```bash
python test_api.py --test all
```

Or test specific endpoints:

```bash
python test_api.py --test health
python test_api.py --test chat --prompt "What is the status of our top contracts?"
```

### Using the API

#### Send a Chat Message

```bash
curl -X POST http://localhost:8000/api/chat/test \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is the status of our top contracts?",
    "agent": "zain_agent",
    "user_id": "test_user"
  }'
```

#### Get Topology

```bash
curl -X GET http://localhost:8000/api/topology
```

## Next Steps

### Configure LLM Connections

1. Access the API at `/api/config/llm-connections`
2. Add your LLM provider credentials
3. Set the default model

### Create Custom Agents

1. Access the API at `/api/config/agents`
2. Create a new agent with your desired system prompt
3. Configure the agent's tools and routing

### Add Data Sources

1. Access the API at `/api/config/datasources`
2. Add your data sources with credentials
3. Configure the tools to use these data sources

### Customize Topology

1. Access the API at `/api/topology`
2. Customize the orchestration flow
3. Test the updated topology

## Troubleshooting

### Server Won't Start

- Check if the port is already in use
- Verify that all dependencies are installed
- Check the log output for errors

### LLM Connection Issues

- Verify your API key is correct
- Check the base URL for your LLM provider
- Ensure your network can reach the LLM provider

### Database Issues

- Check if the database file exists
- Try reinitializing the database
- Check file permissions

## Getting Help

If you encounter any issues or have questions, please:

1. Check the [API Documentation](API_DOCUMENTATION.md)
2. Review the [README](README.md) for more information
3. Open an issue on the GitHub repository

## Security Considerations

- Change the default JWT secret key in the `.env` file
- Use strong API keys
- Enable TLS for production deployments
- Restrict access to the API endpoints
