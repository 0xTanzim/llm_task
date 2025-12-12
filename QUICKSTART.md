# Quick Start Guide 🚀

**Get your LangChain agent running in 5 minutes!**

## Prerequisites

- Docker & Docker Compose installed
- Python 3.11+ installed
- UV package manager (install: `curl -LsSf https://astral.sh/uv/install.sh | sh`)

## Step-by-Step Setup

### 1️⃣ Start Database

```bash
# Start PostgreSQL with sample data
docker-compose up -d

# Verify it's running
docker ps | grep langchain_db
```

**What this does:**
- Starts PostgreSQL 15 container
- Creates `langchain_db` database
- Runs `init.sql` to create sample tables
- Creates checkpoint tables for conversation memory

### 2️⃣ Get API Keys (Free Tiers Available)

**OpenRouter** (LLM Gateway)
- Visit: https://openrouter.ai/keys
- Sign up and get API key
- Free trial credits included

**Tavily** (Web Search)
- Visit: https://tavily.com
- Sign up and get API key
- Free tier: 1,000 searches/month

### 3️⃣ Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit with your API keys
nano .env  # or vim, code, etc.
```

**Required changes in `.env`:**
```bash
OPENROUTER_API_KEY=sk-or-v1-YOUR-KEY-HERE
TAVILY_API_KEY=tvly-YOUR-KEY-HERE
```

### 4️⃣ Install Dependencies

```bash
# Install UV if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync
```

### 5️⃣ Run the Server

```bash
uv run python src/main.py
```

**Expected output:**
```
Starting FastAPI LangChain Service...
Default Model: google/gemini-2.5-flash-lite-preview-09-2025
Database: localhost:5432/langchain_db
API Docs: http://0.0.0.0:8000/docs

INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 6️⃣ Test It Out!

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
  -d '{"message": "What are the latest AI developments?"}'
```

## 🎉 You're Done!

Your AI agent is now running with:
- ✅ Web search capabilities
- ✅ Database query tools
- ✅ Conversation memory
- ✅ Streaming responses
- ✅ Input validation & security

## Next Steps

### View API Documentation
http://localhost:8000/docs

### Try Advanced Features

**Conversation with Memory:**
```bash
# First message
curl -X POST http://localhost:8000/api/v1/chat/ \
  -d '{"message": "My name is Alice", "thread_id": "thread_alice_12345678"}'

# Ask follow-up (remembers your name!)
curl -X POST http://localhost:8000/api/v1/chat/ \
  -d '{"message": "What is my name?", "thread_id": "thread_alice_12345678"}'
```

**Database Queries:**
```bash
curl -X POST http://localhost:8000/api/v1/chat/ \
  -d '{"message": "Show me all customers from New York"}'
```

**Streaming Responses:**
```bash
curl -N -X POST http://localhost:8000/api/v1/chat/stream \
  -d '{"message": "Tell me a short story"}'
```

### Read Documentation

- **[README.md](README.md)** - Complete documentation
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture
- **[docs/VALIDATION_REPORT.md](docs/VALIDATION_REPORT.md)** - Security features
- **[docs/GRAPH_VALIDATION_REPORT.md](docs/GRAPH_VALIDATION_REPORT.md)** - Agent workflow

## Troubleshooting

### Database Won't Start
```bash
# Check if port 5432 is already in use
lsof -i :5432

# Stop conflicting PostgreSQL instance
sudo systemctl stop postgresql

# Restart docker-compose
docker-compose down && docker-compose up -d
```

### API Key Errors
```bash
# Verify .env file is in project root
cat .env | grep API_KEY

# Make sure keys are set correctly (no quotes, no spaces)
OPENROUTER_API_KEY=sk-or-v1-actual-key-here
TAVILY_API_KEY=tvly-actual-key-here
```

### Server Won't Start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill existing process
pkill -f "python src/main.py"

# Restart
uv run python src/main.py
```

### Import Errors
```bash
# Clear cache and reinstall
find . -type d -name __pycache__ -exec rm -r {} +
uv sync --reinstall
```

## Getting Help

- Check [README.md](README.md) for detailed documentation
- View [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
- Review logs: Server outputs detailed error messages
- Test endpoints: http://localhost:8000/docs

---

**Happy Building! 🤖**
