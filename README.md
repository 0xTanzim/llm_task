# LangChain FastAPI + LangGraph ReAct Agent 🤖

**Production-ready AI agent with web search, database tools, and conversation memory.**

[![Production Ready](https://img.shields.io/badge/Status-Production%20Ready-success)](READY_FOR_PRODUCTION.md)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.6.0%2B-purple)](https://langchain-ai.github.io/langgraph/)

## 🎯 What This Agent Does

- ✅ **Web Search** - Real-time information via Tavily API
- ✅ **Database Queries** - SQL operations on PostgreSQL
- ✅ **Code Execution** - Python REPL in sandbox
- ✅ **Conversation Memory** - Persistent state across sessions
- ✅ **Input Validation** - XSS protection & security hardening
- ✅ **Streaming Responses** - Real-time SSE streaming
- ✅ **ReAct Pattern** - Reasoning + Acting workflow

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Docker & Docker Compose**
- **API Keys** (free tiers available):
  - [OpenRouter](https://openrouter.ai/) - LLM gateway
  - [Tavily](https://tavily.com/) - Web search

### 1. Clone & Setup

```bash
# Clone repository
git clone git@github.com:0xTanzim/llm_task.git
cd llm_task

# Install UV (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync
```

### 2. Start PostgreSQL Database

```bash
# Start database with docker-compose
docker-compose up -d

# Verify database is running
docker ps | grep langchain_db

# Check database health
docker exec langchain_db pg_isready -U postgres
```

**What this does:**
- 🐘 Starts PostgreSQL 15 container
- 📊 Creates `langchain_db` database
- 🗂️ Runs `init.sql` to create sample tables (customers, orders, products)
- 💾 Persists data in `postgres_data` volume
- 🔍 Creates LangGraph checkpoint tables automatically

### 3. Configure Environment Variables

```bash
# Copy example config
cp .env.example .env

# Edit .env with your API keys
nano .env  # or vim, code, etc.
```

**Required Configuration:**

```bash
# === LLM Provider (OpenRouter) ===
# Get your key at: https://openrouter.ai/keys
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# Default model (recommended for cost/performance)
DEFAULT_MODEL=google/gemini-2.5-flash-lite-preview-09-2025

# === Web Search (Tavily) ===
# Get your key at: https://tavily.com
TAVILY_API_KEY=tvly-your-key-here

# === PostgreSQL Database ===
# These match docker-compose.yml defaults
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
POSTGRES_DB=langchain_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
DATABASE_URL=postgresql+asyncpg://postgres:postgres123@localhost:5432/langchain_db

# === FastAPI Server ===
API_HOST=0.0.0.0
API_PORT=8000
```

**Optional (for advanced features):**

```bash
# LangSmith tracing (debugging/monitoring)
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your-langsmith-key
LANGSMITH_PROJECT=agent_project
```

### 4. Run the Server

```bash
# Start FastAPI server
uv run python src/main.py
```

**Expected output:**
```
Starting FastAPI LangChain Service...
Default Model: google/gemini-2.5-flash-lite-preview-09-2025
Database: localhost:5432/langchain_db
API Docs: http://0.0.0.0:8000/docs

INFO:     Started server process [12345]
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 5. Test the API

```bash
# Health check
curl http://localhost:8000/health

# Simple chat
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "What is 2+2?"}'

# Web search
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "Search for latest AI news"}'
```

**🎉 You're now running a production-ready AI agent!**

---

## 📖 API Endpoints

### Health Check

Check server status and configuration.

```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "default_model": "google/gemini-2.5-flash-lite-preview-09-2025",
  "database_url": "localhost:5432/langchain_db"
}
```

### Chat (Synchronous)

Send a message and get a complete response.

```bash
POST /api/v1/chat/
Content-Type: application/json

{
  "message": "What is LangGraph?",
  "thread_id": "thread_1234567890abcdef"  // optional
}
```

**Response:**
```json
{
  "response": "LangGraph is a framework for building stateful, multi-agent applications...",
  "thread_id": "thread_1234567890abcdef",
  "model_used": "Gemini 2.5 Flash Lite",
  "llm_calls": 1,
  "tools_used": []
}
```

**With Tools:**
```bash
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "Search for the current weather in Paris"}'
```

**Response:**
```json
{
  "response": "Based on recent data, the weather in Paris is...",
  "thread_id": "thread_a1b2c3d4e5f67890",
  "model_used": "Gemini 2.5 Flash Lite",
  "llm_calls": 2,
  "tools_used": ["tavily_search_results"]
}
```

### Stream (Server-Sent Events)

Get real-time streaming responses with tool execution visibility.

```bash
POST /api/v1/chat/stream
Content-Type: application/json

{
  "message": "Search for AI breakthroughs in 2024",
  "thread_id": "thread_abc123"  // optional
}
```

**Response (SSE stream):**
```
data: {"type": "thread_id", "thread_id": "thread_abc123"}

data: {"type": "tool_call", "tool": "tavily_search_results", "input": {"query": "AI breakthroughs 2024"}}

data: {"type": "tool_result", "tool": "tavily_search_results", "result": "[...]"}

data: {"type": "response", "content": "In 2024, major AI breakthroughs include..."}

data: {"type": "complete", "done": true, "llm_calls": 2, "tools_used": ["tavily_search_results"]}
```

**Example with curl:**
```bash
curl -N -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me about quantum computing"}'
```

### Conversation History

Retrieve full conversation history for a thread.

```bash
GET /api/v1/chat/history/{thread_id}
```

**Example:**
```bash
curl http://localhost:8000/api/v1/chat/history/thread_1234567890abcdef
```

**Response:**
```json
{
  "thread_id": "thread_1234567890abcdef",
  "messages": [
    {
      "role": "user",
      "content": "Hello, my name is Alice",
      "timestamp": "2024-01-27T10:30:00Z"
    },
    {
      "role": "assistant",
      "content": "Hi Alice! How can I help you today?",
      "timestamp": "2024-01-27T10:30:02Z"
    },
    {
      "role": "user",
      "content": "What's my name?",
      "timestamp": "2024-01-27T10:32:00Z"
    },
    {
      "role": "assistant",
      "content": "Your name is Alice!",
      "timestamp": "2024-01-27T10:32:01Z"
    }
  ]
}
```

---

## 🗂️ Database Setup

### PostgreSQL with Docker

The `docker-compose.yml` sets up PostgreSQL with:

```yaml
services:
  postgres:
    image: postgres:15-alpine
    container_name: langchain_db
    environment:
      POSTGRES_DB: langchain_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres123
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
```

### init.sql - Sample Business Data

The `init.sql` file creates sample tables for testing database tools:

**Tables Created:**
- `customers` - Customer information (8 sample records)
- `orders` - Order history (8 sample orders)
- `products` - Product catalog (8 products)
- `order_items` - Order line items (14 items)

**Example Query with Agent:**
```bash
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me the top 3 customers by total order amount"}'
```

The agent will:
1. Use `query_database` tool to execute SQL
2. Fetch results from PostgreSQL
3. Format and present data

### Checkpoint Tables (Auto-Created)

LangGraph automatically creates these tables for conversation state:

- `checkpoints` - Conversation state snapshots
- `checkpoint_writes` - Pending/committed operations

**No manual setup needed** - these are managed by `langgraph-checkpoint-postgres`.

### Database Operations

```bash
# Connect to database
docker exec -it langchain_db psql -U postgres -d langchain_db

# View tables
\dt

# Query sample data
SELECT * FROM customers LIMIT 5;

# Check checkpoint tables
SELECT COUNT(*) FROM checkpoints;

# Stop database
docker-compose down

# Restart database (data persists)
docker-compose up -d

# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d
```

---

## 🏗️ Architecture

### System Overview

```
┌─────────────────┐
│   FastAPI App   │ ← HTTP REST API + SSE streaming
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Chat Service   │ ← Business logic & orchestration
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  LangGraph      │ ← ReAct agent workflow (StateGraph)
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

**Full architecture details:** See [ARCHITECTURE.md](ARCHITECTURE.md)

### ReAct Agent Workflow

```
                    START
                      │
                      ▼
              ┌───────────────┐
              │validate_input │ ◄─── XSS protection, length validation
              └───────┬───────┘
                      │
           ┌──────────┴──────────┐
           │                     │
      (invalid)               (ok)
           │                     │
           ▼                     ▼
    ┌─────────────┐      ┌──────────────┐
    │invalid_input│      │route_request │ ◄─── Simple vs complex routing
    └──────┬──────┘      └──────┬───────┘
           │                     │
           │                     ▼
           │              ┌─────────────┐
           │              │ call_model  │ ◄─── LLM with retry (5x backoff)
           │              └──────┬──────┘
           │                     │
           │          ┌──────────┼──────────┐
           │          │          │          │
           │     (tools)    (finalize) (maxed_out)
           │          │          │          │
           │          ▼          │          ▼
           │     ┌───────┐      │    ┌──────────┐
           │     │ tools │◄─────┘    │maxed_out │ ◄─── 15 iteration limit
           │     └───┬───┘            └────┬─────┘
           │         │ (loop back)         │
           │         └──────────┬──────────┘
           │                    │
           └────────────────────┼─────────────────┐
                                ▼                 │
                        ┌───────────────┐         │
                        │validate_final │◄────────┘
                        └───────┬───────┘
                                │
                                ▼
                               END
```

**Detailed flow:** See [ARCHITECTURE.md](ARCHITECTURE.md) for node descriptions

### Project Structure

```
src/
├── main.py                          # FastAPI entry point
│
├── api/v1/                          # API Layer
│   └── chat.py                      # Endpoints with Pydantic validation
│
├── services/chat/                   # Business Logic
│   └── service.py                   # Chat orchestration
│
├── core/
│   ├── agent/                       # LangGraph Agent
│   │   ├── graph.py                 # Graph compilation
│   │   ├── nodes.py                 # Node implementations
│   │   └── state.py                 # Agent state schema
│   │
│   ├── tools/                       # Agent Tools
│   │   ├── general.py               # Web search (Tavily)
│   │   ├── database.py              # PostgreSQL queries
│   │   └── code.py                  # Python REPL
│   │
│   ├── prompts/                     # Prompt Templates
│   │   └── templates.py             # System & routing prompts
│   │
│   ├── checkpointer/                # Memory Management
│   │   └── __init__.py              # PostgreSQL checkpointer
│   │
│   ├── utils/
│   │   └── retry.py                 # Exponential backoff
│   │
│   └── validation.py                # Input validation & XSS protection
│
└── config/
    ├── settings.py                  # Environment config
    └── constants.py                 # Constants & enums
```

---

## 🧪 Usage Examples

### Example 1: Simple Chat

```bash
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the capital of France?"}'
```

**Agent Flow:**
```
validate_input → route_request → call_model → validate_final
```

**LLM Calls:** 1

---

### Example 2: Web Search

```bash
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the latest developments in quantum computing?"}'
```

**Agent Flow:**
```
validate_input → route_request → call_model → tools (tavily_search) → call_model → validate_final
```

**LLM Calls:** 2
**Tools Used:** `tavily_search_results`

---

### Example 3: Database Query

```bash
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me all customers from New York"}'
```

**Agent Flow:**
```
validate_input → route_request → call_model → tools (query_database) → call_model → validate_final
```

**SQL Generated:**
```sql
SELECT * FROM customers WHERE city = 'New York';
```

**LLM Calls:** 2
**Tools Used:** `query_database`

---

### Example 4: Conversation with Memory

```bash
# First message
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "My favorite color is blue",
    "thread_id": "thread_user_alice_001"
  }'

# Second message (remembers context)
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is my favorite color?",
    "thread_id": "thread_user_alice_001"
  }'
```

**Response:**
```json
{
  "response": "Your favorite color is blue!",
  "thread_id": "thread_user_alice_001",
  "model_used": "Gemini 2.5 Flash Lite",
  "llm_calls": 1,
  "tools_used": []
}
```

---

### Example 5: Streaming Response

```python
import requests
import json

response = requests.post(
    "http://localhost:8000/api/v1/chat/stream",
    json={"message": "Search for AI news and summarize"},
    stream=True
)

for line in response.iter_lines():
    if line:
        line = line.decode('utf-8')
        if line.startswith('data: '):
            data = json.loads(line[6:])
            print(f"{data['type']}: {data.get('content', data.get('tool', ''))}")
```

**Output:**
```
thread_id: thread_a1b2c3d4e5f67890
tool_call: tavily_search_results
tool_result: [search results]
response: Based on recent news...
complete: Done!
```

---

## 🔒 Security Features

### Input Validation

**File:** `src/core/validation.py`

- ✅ **Message Length:** 2-10,000 characters
- ✅ **XSS Protection:** Blocks `<script>`, `javascript:`, event handlers, `<iframe>`
- ✅ **Thread ID Format:** Must match `thread_[a-f0-9]{16}`
- ✅ **Whitespace Trimming:** Auto-sanitization
- ✅ **Empty Input Prevention:** Rejects empty/whitespace-only messages

**Example validation errors:**

```bash
# Empty message
curl -X POST http://localhost:8000/api/v1/chat/ \
  -d '{"message": ""}'
# → HTTP 422: String should have at least 1 character

# XSS attempt
curl -X POST http://localhost:8000/api/v1/chat/ \
  -d '{"message": "<script>alert(1)</script>"}'
# → HTTP 422: Message contains potentially unsafe content

# Invalid thread ID
curl -X POST http://localhost:8000/api/v1/chat/ \
  -d '{"message": "Hi", "thread_id": "invalid"}'
# → HTTP 422: Invalid thread_id format
```

**Security test report:** See [docs/VALIDATION_REPORT.md](docs/VALIDATION_REPORT.md)

### Database Security

- ✅ **Read-Only Queries:** `query_database` tool validates `SELECT`-only operations
- ✅ **Connection Pooling:** asyncpg with secure defaults
- ✅ **Prepared Statements:** Protection against SQL injection
- ✅ **Timeout Limits:** Prevents long-running queries

### LLM Safety

- ✅ **Retry Logic:** Exponential backoff prevents API abuse
- ✅ **Iteration Limits:** Max 15 loops prevents infinite execution
- ✅ **Timeout Controls:** Configurable per-request timeouts
- ✅ **Error Sanitization:** No sensitive data in error messages

---

## 📚 Documentation

### Quick Reference

- **[🚀 Production Ready](READY_FOR_PRODUCTION.md)** - Status overview & quick tests
- **[🏗️ Architecture](ARCHITECTURE.md)** - Complete system architecture
- **[🛡️ Validation Report](docs/VALIDATION_REPORT.md)** - Security testing results
- **[🔄 Graph Validation](docs/GRAPH_VALIDATION_REPORT.md)** - Agent workflow analysis
- **[📋 Production Readiness](docs/PRODUCTION_READINESS.md)** - Deployment guide

### API Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Code Documentation

```bash
# View docstrings for nodes
cat src/core/agent/nodes.py | grep '"""' -A 5

# View graph structure
cat src/core/agent/graph.py | grep -A 30 'def create_graph'

# View available tools
cat src/core/tools/general.py | grep '@tool' -A 3
```

---

## 🛠️ Development

### Install Development Tools

```bash
# Install with dev dependencies
uv sync --dev

# Run tests
uv run pytest tests/

# Format code
uv run black src/

# Lint code
uv run ruff check src/
```

### Hot Reload

```bash
# Run with auto-reload on code changes
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Debug Mode

```bash
# Enable debug logging
export DEBUG=True
uv run python src/main.py
```

### Testing Tools

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test with verbose output
curl -v -X POST http://localhost:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'

# Test streaming
curl -N -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Count to 5"}' | grep 'data:'

# Check database
docker exec -it langchain_db psql -U postgres -d langchain_db -c "SELECT COUNT(*) FROM checkpoints;"
```

---

## 🚢 Deployment

### Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Reset everything (WARNING: deletes data)
docker-compose down -v
```

### Production Checklist

- [ ] Set strong `POSTGRES_PASSWORD` in `.env`
- [ ] Use production database (not localhost)
- [ ] Enable HTTPS/TLS with reverse proxy (nginx, Caddy)
- [ ] Set up monitoring (Prometheus, Datadog)
- [ ] Configure logging aggregation (ELK, CloudWatch)
- [ ] Enable rate limiting (Redis + FastAPI-limiter)
- [ ] Set up backups for PostgreSQL
- [ ] Configure CORS for frontend domain
- [ ] Add authentication (JWT tokens)
- [ ] Set up CI/CD pipeline

### Environment Variables for Production

```bash
# Use strong secrets
POSTGRES_PASSWORD=<strong-random-password>
OPENROUTER_API_KEY=<your-production-key>

# Production database
DATABASE_URL=postgresql+asyncpg://user:pass@prod-db.example.com:5432/langchain_db

# Disable debug mode
DEBUG=False

# Enable monitoring
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=<your-langsmith-key>
```

---

## 🧩 Available Tools

### 1. Web Search (Tavily)

```python
@tool
def tavily_search_results(query: str) -> str:
    """Search the web for real-time information."""
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/chat/ \
  -d '{"message": "What is the current weather in Tokyo?"}'
```

### 2. Database Query

```python
@tool
def query_database(sql: str) -> str:
    """Execute read-only SQL queries on PostgreSQL."""
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/chat/ \
  -d '{"message": "Show me the top 5 products by price"}'
```

### 3. Python REPL

```python
@tool
def python_repl(code: str) -> str:
    """Execute Python code in a sandbox."""
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/chat/ \
  -d '{"message": "Calculate the factorial of 10"}'
```

---

## 🤝 Contributing

### Adding New Tools

1. Create tool in `src/core/tools/`
2. Decorate with `@tool`
3. Add to tool list in `src/core/agent/graph.py`
4. Test with agent

**Example:**
```python
from langchain.tools import tool

@tool
def weather_forecast(city: str) -> str:
    """Get weather forecast for a city."""
    # Implementation
    return f"Weather for {city}: Sunny, 72°F"
```

### Adding New Nodes

1. Define node function in `src/core/agent/nodes.py`
2. Add node to graph in `src/core/agent/graph.py`
3. Connect edges appropriately
4. Update state schema if needed

---

## 📝 License

MIT License - See [LICENSE](LICENSE) file for details

---

## 🆘 Troubleshooting

### Database Connection Errors

```bash
# Check if PostgreSQL is running
docker ps | grep langchain_db

# Check database health
docker exec langchain_db pg_isready -U postgres

# Restart database
docker-compose restart postgres
```

### Import Errors

```bash
# Reinstall dependencies
uv sync --reinstall

# Clear Python cache
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name '*.pyc' -delete
```

### API Key Issues

```bash
# Verify .env file exists
cat .env | grep API_KEY

# Check environment variables are loaded
uv run python -c "from src.config.settings import settings; print(settings.OPENROUTER_API_KEY[:10])"
```

### Server Won't Start

```bash
# Check port 8000 is not in use
lsof -i :8000

# Kill existing process
pkill -f "python src/main.py"

# Start with debug mode
DEBUG=True uv run python src/main.py
```

---

## 📞 Support

- **Documentation:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **Issues:** GitHub Issues
- **Status:** [READY_FOR_PRODUCTION.md](READY_FOR_PRODUCTION.md)

---

**🎉 Happy Building with LangChain + LangGraph! 🤖**
