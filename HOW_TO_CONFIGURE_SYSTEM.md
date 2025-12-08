# How to Configure the ZainOne Orchestrator System

## Understanding the System Architecture

The ZainOne Orchestrator Studio has 4 main components that work together:

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│   LLM       │────▶│   Router     │────▶│   Tools     │────▶│   Result     │
│ Connection  │     │  & Planner   │     │  Executor   │     │              │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘
                            │                     │
                            ▼                     ▼
                    ┌──────────────┐     ┌─────────────┐
                    │ Data Sources │     │  External   │
                    │     (RAG)    │     │   Agents    │
                    └──────────────┘     └─────────────┘
```

## 1. LLM Connections (The Brain)

**What it does:** Provides the AI intelligence for understanding requests and generating responses.

**Configuration:**
- Go to: **LLM Connections** page
- Add your LLM:
  - **Local (Ollama)**: `http://localhost:11434` - No API key needed
  - **Remote (OpenAI)**: `https://api.openai.com/v1` - API key required
  - **Remote (Anthropic)**: `https://api.anthropic.com` - API key required

**Example:**
```
Name: Local Ollama
Base URL: http://localhost:11434
Model: llama3
API Key: (leave empty for local)
```

## 2. Data Sources (The Knowledge Base)

**What it does:** Provides read-only data for the LLM to reference (RAG - Retrieval Augmented Generation).

**How it relates to LLM:**
- When a user asks a question, the system can query Data Sources to get relevant information
- This information is then passed to the LLM as context
- The LLM uses this context to generate more accurate, grounded responses

**Configuration:**
- Go to: **Tools & Data Sources** → **Data Sources** tab
- Add a data source:
  - **Database**: PostgreSQL, MySQL, MongoDB for querying structured data
  - **API**: REST APIs that return data
  - **Cube.js**: Analytics data for business intelligence queries

**Example Use Case:**
```
User Question: "What were our sales last quarter?"
↓
System queries Data Source (Sales Database)
↓
Returns: "Q4 2024 sales: $1.2M"
↓
LLM receives this data as context
↓
LLM Response: "Your sales for Q4 2024 were $1.2 million, 
representing a 15% increase from Q3."
```

**Example Configuration:**
```
Name: Sales Database
Type: PostgreSQL
URL: postgresql://localhost:5432/sales_db
Auth Token: (database password)
```

## 3. Tools (The Actions)

**What it does:** Allows the LLM to perform actions and execute functions.

**How it relates to LLM:**
- The LLM can decide to use tools based on the user's request
- Tools can modify data, send emails, make API calls, etc.
- Results from tools are sent back to the LLM for processing

**Configuration:**
- Go to: **Tools & Data Sources** → **Tools** tab
- Add a tool:
  - **HTTP API**: Call external APIs
  - **Code Executor**: Run Python/JavaScript code
  - **Web Search**: Search the internet
  - **Custom**: Your own tool implementations

**Example Use Case:**
```
User Request: "Send an email to john@example.com about the meeting"
↓
LLM decides to use "Email Tool"
↓
Tool executes: SendEmail(to="john@example.com", subject="Meeting", body="...")
↓
Tool returns: "Email sent successfully"
↓
LLM Response: "I've sent the email to John about the meeting."
```

**Example Configuration:**
```
Name: Email Service
Type: HTTP API
Endpoint: https://api.sendgrid.com/v3/mail/send
API Key: (your SendGrid API key)
```

## 4. Orchestration Flow (The Workflow)

**What it does:** Defines how requests flow through the system.

**Why it's empty:** The flow needs to be configured with your specific components.

**How to Configure:**

### Step 1: Configure All Components First
Before creating a flow, you need:
- ✅ At least 1 LLM Connection
- ✅ At least 1 Data Source (optional but recommended)
- ✅ At least 1 Tool (optional but recommended)

### Step 2: Create a Flow
Go to: **Orchestration Flow** page

**Basic Flow Structure:**
```
1. INPUT (User Request)
   ↓
2. ROUTER (Analyze request intent)
   ↓
3. PLANNER (Decide what to do)
   ↓
4. EXECUTOR (Execute actions)
   ├─→ Query Data Sources (if needed)
   ├─→ Call Tools (if needed)
   └─→ Call LLM (for generation)
   ↓
5. RESULT (Return response)
```

### Step 3: Example Flow Configuration

**Simple Q&A Flow:**
```json
{
  "name": "Simple Q&A",
  "nodes": [
    {
      "id": "input",
      "type": "start",
      "config": {}
    },
    {
      "id": "llm",
      "type": "llm_agent",
      "config": {
        "llm_connection": "Local Ollama",
        "model": "llama3"
      }
    },
    {
      "id": "output",
      "type": "end",
      "config": {}
    }
  ],
  "connections": [
    {"from": "input", "to": "llm"},
    {"from": "llm", "to": "output"}
  ]
}
```

**Advanced Flow with Data Sources:**
```json
{
  "name": "Data-Grounded Q&A",
  "nodes": [
    {
      "id": "input",
      "type": "start"
    },
    {
      "id": "router",
      "type": "intent_router",
      "config": {
        "llm_connection": "Local Ollama"
      }
    },
    {
      "id": "grounding",
      "type": "grounding_node",
      "config": {
        "datasource": "Sales Database"
      }
    },
    {
      "id": "llm",
      "type": "llm_agent",
      "config": {
        "llm_connection": "Local Ollama",
        "model": "llama3"
      }
    },
    {
      "id": "output",
      "type": "end"
    }
  ],
  "connections": [
    {"from": "input", "to": "router"},
    {"from": "router", "to": "grounding"},
    {"from": "grounding", "to": "llm"},
    {"from": "llm", "to": "output"}
  ]
}
```

## Complete Setup Example

### Scenario: Customer Support Bot with Database Access

**1. Configure LLM:**
```
Name: Support Bot LLM
Base URL: http://localhost:11434
Model: llama3
```

**2. Configure Data Source:**
```
Name: Customer Database
Type: PostgreSQL
URL: postgresql://localhost:5432/customers
Purpose: Query customer information, order history
```

**3. Configure Tool:**
```
Name: Ticket System
Type: HTTP API
Endpoint: https://api.zendesk.com/v2/tickets
Purpose: Create support tickets
```

**4. Create Flow:**
```
User Question
    ↓
Router (Analyze: Is this about orders? Account? Technical issue?)
    ↓
Grounding Node (Query Customer Database for relevant info)
    ↓
LLM Agent (Generate response using customer data)
    ↓
Tool Executor (Create ticket if needed)
    ↓
Return Response
```

## How Data Flows Through the System

### Example: "What's my order status?"

1. **User Input:** "What's my order status for order #12345?"

2. **Router:** Identifies this as an "order status query"

3. **Grounding (Data Source):**
   - Queries Customer Database
   - SQL: `SELECT status, tracking FROM orders WHERE order_id = 12345`
   - Returns: `{status: "shipped", tracking: "1Z999AA10123456784"}`

4. **LLM Agent:**
   - Receives context: "Order #12345 is shipped with tracking 1Z999AA10123456784"
   - Generates: "Your order #12345 has been shipped! You can track it using tracking number 1Z999AA10123456784."

5. **Output:** Returns formatted response to user

## Key Differences

| Component | Purpose | Can Modify Data? | Example |
|-----------|---------|------------------|---------|
| **LLM** | Generate text, understand intent | No | "Analyze this text and summarize it" |
| **Data Source** | Provide information (RAG) | No | Query customer database for order info |
| **Tool** | Execute actions | Yes | Send email, create ticket, update database |
| **External Agent** | Delegate to specialized AI | Depends | Call another AI service for specific task |

## Troubleshooting

### "Orchestration Flow is empty"
**Problem:** No nodes or connections visible
**Solution:**
1. Ensure backend is running on port 8000
2. Check that you have configured at least one LLM connection
3. Try creating a simple flow manually using the UI
4. Check browser console for errors

### "Data Sources not working with LLM"
**Problem:** LLM doesn't use data source information
**Solution:**
1. Ensure Data Source is configured and tested
2. Create a flow that includes a "Grounding Node"
3. Connect: Input → Router → Grounding → LLM → Output
4. The Grounding Node will query the data source and pass results to LLM

### "Tools not being called"
**Problem:** LLM doesn't use available tools
**Solution:**
1. Ensure Tools are configured and enabled
2. Use a routing profile that supports tools (e.g., "Tools + Data")
3. In Chat Studio, enable the "Tools" toggle
4. Provide clear instructions to the LLM about when to use tools

## Quick Start Checklist

- [ ] Configure at least 1 LLM Connection
- [ ] Test LLM connection (click "Test Connection" button)
- [ ] Configure at least 1 Data Source (optional)
- [ ] Test Data Source connection
- [ ] Configure at least 1 Tool (optional)
- [ ] Test Tool connection
- [ ] Create an Orchestration Flow
- [ ] Test the flow in Internal Chat
- [ ] Monitor results in Monitoring & Services

## Next Steps

1. Start with a simple LLM-only flow
2. Add Data Sources for grounding
3. Add Tools for actions
4. Create complex flows as needed
5. Monitor and optimize performance

For more help, see:
- `LLM_UI_IMPROVEMENTS_SUMMARY.md` - UI improvements guide
- `CONFIGURATION_GUIDE.md` - Detailed configuration
- `USER_GUIDE_CONFIGURATION.md` - User guide
