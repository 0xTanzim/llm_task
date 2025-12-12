# LangChain + LangGraph Agent

**Simple, clean implementation demonstrating LangChain and LangGraph concepts.**

## 🎯 What This Project Demonstrates

### LangChain Features
- ✅ **Tools**: Web search (Tavily) and calculator
- ✅ **LLM Integration**: Google Gemini via OpenAI-compatible API
- ✅ **Message Handling**: Proper message types and formatting
- ✅ **Tool Calling**: Automatic tool invocation

### LangGraph Features
- ✅ **StateGraph**: Workflow with nodes and edges
- ✅ **Conditional Routing**: Decision-making in graph
- ✅ **Memory/Checkpointing**: Conversation history
- ✅ **Streaming**: Real-time responses

## 📁 Project Structure

```
src/
├── core/
│   ├── agent/
│   │   └── simple_agent.py      # LangGraph agent
│   ├── base_llm/
│   │   └── openAi.py            # LLM setup
│   └── memory/
│       └── checkpointer.py      # Memory for conversations
├── services/
│   └── chat/
│       └── simple_service.py    # Chat service
├── api/
│   └── v1/
│       └── simple_chat.py       # FastAPI endpoints
├── config/
│   └── settings.py              # Configuration
└── main.py                      # FastAPI app
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -e .
```

### 2. Setup Environment

Create `.env` file:

```bash
cp .env.example .env
```

Add your API keys in `.env`:

```env
GOOGLE_API_KEY=your-google-api-key
TAVILY_API_KEY=your-tavily-api-key
```

**Get API Keys:**
- Google (Gemini): https://makersuite.google.com/app/apikey
- Tavily (Search): https://tavily.com (free tier available)

### 3. Run the Server

```bash
cd src
python main.py
```

API will be available at: http://localhost:8000

## 📖 Usage Examples

### Using the API

#### 1. Simple Chat

```bash
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "What is 25 * 4?"}'
```

Response:
```json
{
  "response": "25 * 4 = 100",
  "thread_id": "abc-123"
}
```

#### 2. Chat with Memory

```bash
# First message
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "My name is Alice", "thread_id": "user-1"}'

# Second message (remembers context)
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "What is my name?", "thread_id": "user-1"}'
```

#### 3. Web Search

```bash
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "Search for latest AI news"}'
```

#### 4. Streaming Response

```bash
curl -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me a story"}'
```

### Using Python

```python
import requests

# Simple chat
response = requests.post(
    "http://localhost:8000/api/v1/chat/",
    json={"message": "Calculate 10 + 20"}
)
print(response.json())

# With conversation memory
thread_id = "my-conversation"

# Message 1
requests.post(
    "http://localhost:8000/api/v1/chat/",
    json={"message": "I like pizza", "thread_id": thread_id}
)

# Message 2 (remembers previous)
response = requests.post(
    "http://localhost:8000/api/v1/chat/",
    json={"message": "What food do I like?", "thread_id": thread_id}
)
print(response.json()["response"])  # "You like pizza"
```

## 🎓 Learning Guide

### Core Concepts

#### 1. **LangChain Tools** (`core/agent/simple_agent.py`)

```python
@tool
def search_web(query: str) -> str:
    """Search the web for information."""
    # Tool implementation
```

- Tools are functions decorated with `@tool`
- LLM decides when to use them
- Results are returned to LLM

#### 2. **LangGraph Workflow** (`core/agent/simple_agent.py`)

```python
workflow = StateGraph(MessagesState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", call_tools)
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue)
```

- **StateGraph**: Defines workflow
- **Nodes**: Steps in the workflow
- **Edges**: Connections between nodes
- **Conditional Edges**: Decision points

#### 3. **Memory/Checkpointing**

```python
checkpointer = get_checkpointer()
agent = workflow.compile(checkpointer=checkpointer)
```

- Stores conversation history
- Each thread has separate memory
- Automatic state management

## 🔧 Configuration

Edit `.env` file:

```env
# App Settings
PORT=8000
DEBUG=True

# LLM Settings
LLM_MODEL=gemini-2.5-flash
LLM_TEMPERATURE=0.7

# API Keys
GOOGLE_API_KEY=your-key
TAVILY_API_KEY=your-key
```

## 📚 Documentation

Visit http://localhost:8000/docs for interactive API documentation (Swagger UI).

## 🧪 Testing

Run simple tests:

```python
python -c "
import sys
sys.path.insert(0, 'src')

from core.agent.simple_agent import create_simple_agent

agent = create_simple_agent()
result = agent.invoke(
    {'messages': [{'role': 'user', 'content': 'Hello!'}]},
    {'configurable': {'thread_id': 'test'}}
)
print(result['messages'][-1].content)
"
```

## 🎯 Key Features

1. **Clean Code**: Simple, readable, well-documented
2. **Modular**: Easy to extend and modify
3. **Production-Ready**: Proper error handling and logging
4. **Educational**: Clear examples of LangChain and LangGraph

## 📝 License

MIT
