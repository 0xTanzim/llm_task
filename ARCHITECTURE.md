# Architecture Overview

## System Architecture

### High-Level Architecture

```
┌─────────────────┐
│   FastAPI App   │ ← HTTP/REST API
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Chat Service   │ ← Business Logic
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  LangGraph      │ ← ReAct Agent Workflow
│   StateGraph    │
└────────┬────────┘
         │
    ┌────┴─────┬─────────┬──────────┐
    ▼          ▼         ▼          ▼
┌────────┐ ┌────────┐ ┌──────┐ ┌──────────┐
│  LLM   │ │ Tools  │ │Memory│ │PostgreSQL│
│Gemini  │ │Tavily  │ │State │ │Checkpoint│
└────────┘ └────────┘ └──────┘ └──────────┘
```

## Project Structure

```
src/
├── main.py                          # FastAPI application entry point
│
├── api/                             # API Layer (HTTP endpoints)
│   └── v1/
│       └── chat.py                  # Chat endpoints with validation
│
├── services/                        # Business Logic Layer
│   └── chat/
│       └── service.py               # Chat orchestration service
│
├── core/                            # Core Application Logic
│   ├── agent/                       # LangGraph Agent
│   │   ├── graph.py                 # Graph definition & compilation
│   │   ├── nodes.py                 # Node implementations
│   │   └── state.py                 # Agent state schema
│   │
│   ├── tools/                       # Agent Tools
│   │   ├── general.py               # Web search (Tavily)
│   │   ├── database.py              # Database operations
│   │   └── code.py                  # Code execution
│   │
│   ├── prompts/                     # Prompt Templates
│   │   └── templates.py             # System & routing prompts
│   │
│   ├── checkpointer/                # Memory Management
│   │   └── __init__.py              # PostgreSQL checkpointer
│   │
│   ├── utils/                       # Utilities
│   │   └── retry.py                 # Retry with backoff
│   │
│   └── validation.py                # Input validation & security
│
├── config/                          # Configuration
│   ├── settings.py                  # Environment config
│   └── constants.py                 # Constants & enums
│
└── schemas/                         # Data Schemas
    └── __init__.py                  # Pydantic models
```

## ReAct Agent Workflow

### Graph Structure

```
                    START
                      │
                      ▼
              ┌───────────────┐
              │validate_input │ ◄─── Input validation & sanitization
              └───────┬───────┘
                      │
           ┌──────────┴──────────┐
           │                     │
      (invalid)               (ok)
           │                     │
           ▼                     ▼
    ┌─────────────┐      ┌──────────────┐
    │invalid_input│      │route_request │ ◄─── Determine request type
    └──────┬──────┘      └──────┬───────┘
           │                     │
           │                     ▼
           │              ┌─────────────┐
           │              │ call_model  │ ◄─── LLM invocation with retry
           │              └──────┬──────┘
           │                     │
           │          ┌──────────┼──────────┐
           │          │          │          │
           │     (tools)    (finalize) (maxed_out)
           │          │          │          │
           │          ▼          │          ▼
           │     ┌───────┐      │    ┌──────────┐
           │     │ tools │      │    │maxed_out │ ◄─── Iteration limit
           │     └───┬───┘      │    └────┬─────┘
           │         │          │         │
           │         └──────────┤         │
           │                    │         │
           └────────────────────┼─────────┘
                                ▼
                        ┌───────────────┐
                        │validate_final │ ◄─── Format final response
                        └───────┬───────┘
                                │
                                ▼
                               END
```

### Node Descriptions

| Node | Purpose | Input | Output |
|------|---------|-------|--------|
| **validate_input** | Validates and sanitizes user input | Raw message | Validated message or error |
| **invalid_input** | Handles validation failures | Validation error | Error response |
| **route_request** | Determines request complexity | Validated message | Routing decision |
| **call_model** | Invokes LLM with retry logic | State + messages | Model response + tool calls |
| **tools** | Executes requested tools in parallel | Tool calls | Tool results |
| **maxed_out** | Handles iteration limit (15 max) | State with too many iterations | Warning message |
| **validate_final** | Formats and validates final response | Raw LLM output | Structured ChatResponse |

### Conditional Routing

**Input Validation Router:**
- `ok` → Proceed to route_request
- `invalid` → Return error message immediately

**Model Response Router:**
- `tools` → Execute tools and loop back to call_model
- `finalize` → Output final answer
- `maxed_out` → Too many iterations, exit with warning

## Data Flow

### 1. Request Flow (Synchronous Chat)

```
Client Request
    │
    ▼
POST /api/v1/chat/
    │
    ├─► Pydantic Validation (field validators)
    │       ├─► Message length (2-10,000 chars)
    │       ├─► XSS pattern detection
    │       └─► Thread ID format validation
    │
    ▼
ChatService.chat()
    │
    ├─► Get/create PostgreSQL checkpointer
    ├─► Get compiled graph with checkpointer
    ├─► Invoke graph with state
    │
    ▼
LangGraph Execution
    │
    ├─► validate_input node
    ├─► route_request node
    ├─► call_model node (retry logic)
    ├─► tools node (if needed)
    └─► validate_final node
    │
    ▼
Response Construction
    │
    ├─► Extract final message
    ├─► Extract tools used
    ├─► Extract model name
    ├─► Count LLM calls
    │
    ▼
ChatResponse
    └─► JSON response to client
```

### 2. Streaming Flow (SSE)

```
Client Request
    │
    ▼
POST /api/v1/chat/stream
    │
    ├─► Validation (same as sync)
    │
    ▼
ChatService.stream()
    │
    ├─► Yield thread_id event
    │
    ▼
Graph Stream Events
    │
    ├─► Yield tool_call events
    ├─► Yield tool_result events
    ├─► Yield response chunks
    │
    ▼
SSE Stream to Client
    └─► data: {type, content}
```

### 3. Memory/State Flow

```
Request with thread_id
    │
    ▼
PostgreSQL Checkpointer
    │
    ├─► Load conversation state from DB
    ├─► Resume from last checkpoint
    │
    ▼
Graph Execution
    │
    ├─► Process with full history
    ├─► Update state
    │
    ▼
Save Checkpoint
    │
    ├─► Store updated state in DB
    └─► Associate with thread_id
```

## Database Schema

### LangGraph Checkpoints

**Managed by:** `langgraph-checkpoint-postgres`

```sql
-- Checkpoint metadata table
CREATE TABLE checkpoints (
    thread_id TEXT,
    checkpoint_ns TEXT,
    checkpoint_id TEXT,
    parent_checkpoint_id TEXT,
    type TEXT,
    checkpoint JSONB,
    metadata JSONB,
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
);

-- Writes (pending/committed operations)
CREATE TABLE checkpoint_writes (
    thread_id TEXT,
    checkpoint_ns TEXT,
    checkpoint_id TEXT,
    task_id TEXT,
    idx INTEGER,
    channel TEXT,
    type TEXT,
    value JSONB,
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
);
```

### Business Data (init.sql)

```sql
-- Sample business tables
customers (id, name, email, phone, city, country, status)
orders (id, customer_id, order_date, total_amount, status)
products (id, name, category, price, stock_quantity)
order_items (id, order_id, product_id, quantity, unit_price)
```

## Security Architecture

### Input Validation Layer

**File:** `src/core/validation.py`

```python
validate_message()
    ├─► Length validation (2-10,000 chars)
    ├─► Whitespace trimming
    └─► XSS pattern detection:
        ├─► <script> tags
        ├─► javascript: protocol
        ├─► Event handlers (onclick, onerror, etc.)
        └─► <iframe> tags

validate_thread_id()
    └─► Format: thread_[a-f0-9]{16}
```

### API Layer Protection

**File:** `src/api/v1/chat.py`

```python
Pydantic Field Validators
    ├─► @field_validator("message")
    │       └─► Calls validate_message()
    │
    └─► @field_validator("thread_id")
            └─► Calls validate_thread_id()

FastAPI Automatic Handling
    └─► ValueError → HTTP 422 response
```

### LLM Layer Protection

**File:** `src/core/agent/nodes.py`

```python
Retry Logic
    ├─► Exponential backoff: 1s, 2s, 4s, 8s, 16s
    ├─► Max retries: 5
    └─► Only on LLM calls (not tools)

Iteration Limit
    ├─► Max iterations: 15
    └─► Prevents infinite tool loops
```

## Tool Architecture

### Tool Registry

**File:** `src/core/tools/general.py`

```python
@tool
def tavily_search_results(query: str) -> str:
    """Web search with structured results"""
    # Returns: JSON with title, url, content
```

**File:** `src/core/tools/database.py`

```python
@tool
def query_database(sql: str) -> str:
    """Execute read-only SQL queries"""
    # Safety: Validates SELECT-only queries
```

**File:** `src/core/tools/code.py`

```python
@tool
def python_repl(code: str) -> str:
    """Execute Python code in sandbox"""
    # Safety: Timeout + restricted imports
```

### Tool Execution Flow

```
LLM requests tool
    │
    ▼
tools node (execute_tools_node)
    │
    ├─► Parse tool calls from AIMessage
    ├─► Execute each tool
    │       ├─► Call tool function
    │       ├─► Catch exceptions
    │       └─► Format result as ToolMessage
    │
    ▼
Return to call_model
    └─► LLM sees tool results → decides next action
```

## Configuration Management

### Environment Variables

**File:** `.env`

```bash
# LLM Provider
OPENROUTER_API_KEY=sk-or-v1-...
DEFAULT_MODEL=google/gemini-2.5-flash-lite-preview-09-2025

# Tools
TAVILY_API_KEY=tvly-...

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres123@localhost:5432/langchain_db

# Server
API_HOST=0.0.0.0
API_PORT=8000
```

### Settings Module

**File:** `src/config/settings.py`

```python
class Settings(BaseSettings):
    OPENROUTER_API_KEY: str
    DEFAULT_MODEL: str
    TAVILY_API_KEY: str
    DATABASE_URL: str

    model_config = SettingsConfigDict(env_file=".env")
```

## Performance Considerations

### Async Architecture

- **FastAPI:** Fully async endpoints
- **Database:** `asyncpg` for non-blocking I/O
- **Tools:** Can execute in parallel

### Caching Strategy

- **Embeddings:** Not implemented (stateless queries)
- **Checkpoints:** PostgreSQL persistence
- **Connection Pooling:** asyncpg default pool

### Resource Limits

- **Message Length:** 10,000 chars (DoS prevention)
- **Iterations:** 15 max (infinite loop prevention)
- **LLM Timeout:** Configurable per request
- **DB Connection Pool:** asyncpg defaults

## Deployment Architecture

### Local Development

```
Terminal 1: docker-compose up -d   # PostgreSQL
Terminal 2: uv run python src/main.py  # FastAPI server
```

### Production Deployment

```
                    ┌──────────────┐
                    │ Load Balancer│
                    └──────┬───────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│FastAPI App 1│    │FastAPI App 2│    │FastAPI App N│
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                  │
       └──────────────────┼──────────────────┘
                          │
                          ▼
                  ┌───────────────┐
                  │  PostgreSQL   │
                  │   (Primary)   │
                  └───────┬───────┘
                          │
                  ┌───────┴───────┐
                  │               │
                  ▼               ▼
          ┌──────────────┐  ┌──────────────┐
          │  Replica 1   │  │  Replica 2   │
          └──────────────┘  └──────────────┘
```

### Recommended Stack

- **Container:** Docker + Docker Compose
- **Orchestration:** Kubernetes (for scale)
- **Database:** PostgreSQL 15+ with replicas
- **Monitoring:** Prometheus + Grafana
- **Logging:** ELK Stack or CloudWatch
- **Secrets:** AWS Secrets Manager / Vault

## Technology Stack

### Core Framework

- **FastAPI 0.100+** - Async web framework
- **Pydantic 2.0+** - Data validation
- **Python 3.11+** - Language runtime

### LangChain Stack

- **LangChain Core** - Base abstractions
- **LangGraph 0.6.0+** - Agent workflows
- **LangChain OpenAI** - LLM integration
- **LangChain Community** - Tool integrations

### Database & Persistence

- **PostgreSQL 15** - Primary database
- **asyncpg** - Async PostgreSQL driver
- **langgraph-checkpoint-postgres** - State management

### Tools & APIs

- **Tavily API** - Web search
- **OpenRouter** - LLM gateway
- **Google Gemini** - Default LLM

### Development Tools

- **UV** - Python package manager
- **Docker & Docker Compose** - Containerization
- **Pytest** - Testing framework

## API Endpoints

### Health Check

```http
GET /health
Response: 200 OK
{
  "status": "healthy",
  "default_model": "google/gemini-2.5-flash-lite-preview-09-2025",
  "database_url": "localhost:5432/langchain_db"
}
```

### Chat (Synchronous)

```http
POST /api/v1/chat/
Content-Type: application/json

Request:
{
  "message": "What is LangGraph?",
  "thread_id": "thread_1234567890abcdef"  // optional
}

Response: 200 OK
{
  "response": "LangGraph is...",
  "thread_id": "thread_1234567890abcdef",
  "model_used": "Gemini 2.5 Flash Lite",
  "llm_calls": 1,
  "tools_used": []
}

Errors:
422 Unprocessable Entity - Invalid input
500 Internal Server Error - Processing error
```

### Stream (Server-Sent Events)

```http
POST /api/v1/chat/stream
Content-Type: application/json

Request:
{
  "message": "Search for AI news",
  "thread_id": "thread_abc123"  // optional
}

Response: 200 OK (SSE stream)
Content-Type: text/event-stream

data: {"type": "thread_id", "thread_id": "thread_abc123"}

data: {"type": "tool_call", "tool": "tavily_search_results", "input": {"query": "AI news"}}

data: {"type": "tool_result", "tool": "tavily_search_results", "result": "..."}

data: {"type": "response", "content": "Based on recent news..."}

data: {"type": "complete", "done": true}
```

### History

```http
GET /api/v1/chat/history/{thread_id}

Response: 200 OK
{
  "thread_id": "thread_1234567890abcdef",
  "messages": [
    {
      "role": "user",
      "content": "Hello",
      "timestamp": "2024-01-27T10:30:00Z"
    },
    {
      "role": "assistant",
      "content": "Hi! How can I help?",
      "timestamp": "2024-01-27T10:30:02Z"
    }
  ]
}

Errors:
400 Bad Request - Invalid thread_id format
404 Not Found - Thread not found
500 Internal Server Error - Database error
```

## Monitoring & Observability

### Health Checks

```python
# Application health
GET /health → Status of app + DB + model config

# Database health
docker exec langchain_db pg_isready -U postgres
```

### Logging

```python
# Console logs (stdout)
🟢 Selected: Default Model + General Tools
❌ Error: {error_detail}
✅ Health check passed

# Structured logging (production)
{
  "timestamp": "2024-01-27T10:30:00Z",
  "level": "INFO",
  "message": "Chat request processed",
  "thread_id": "thread_abc123",
  "llm_calls": 2,
  "tools_used": ["tavily_search_results"]
}
```

### Metrics (Recommended)

- Request rate (requests/sec)
- Response time (p50, p95, p99)
- Error rate (errors/total requests)
- LLM call count per request
- Tool execution time
- Database query time

## Error Handling

### API Layer

```python
try:
    # Request processing
except ValueError:
    # Validation error → 422
except Exception:
    # Unexpected error → 500 with sanitized message
```

### Agent Layer

```python
# Retry with exponential backoff
@retry_with_exponential_backoff(max_retries=5)
def call_model_node(state):
    # LLM invocation

# Iteration limit
if state["llm_calls"] >= 15:
    return "maxed_out"
```

### Tool Layer

```python
try:
    result = tool.invoke(input)
except Exception as e:
    # Return error as ToolMessage
    return ToolMessage(content=f"Error: {str(e)}")
```

---

**Last Updated:** 2025-01-27
**Version:** 1.0.0
**Status:** Production Ready
