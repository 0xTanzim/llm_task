# FastAPI LangChain REST Service 🚀

A professional FastAPI REST service with LangChain integration featuring:
- ✅ **Streaming chat** with real-time tokens
- ✅ **Chain-of-thought reasoning** with structured JSON
- ✅ **OpenAI compatibility** with Google Gemini

## 📁 Project Structure

```
src/
├── main.py              # FastAPI app
├── api/
│   ├── __init__.py
│   ├── router.py        # Main router
│   └── chat.py          # All chat endpoints
├── core/
│   ├── __init__.py
│   └── config.py        # Settings from .env
└── services/
    ├── __init__.py
    └── llm.py           # LangChain service
```

## 🚀 Quick Start

### 1. Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure
```bash
cp .env.example .env
# Add your GOOGLE_API_KEY to .env
```

### 3. Run
```bash
cd src
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Access: http://localhost:8000/docs

## 📡 API Endpoints

### 1️⃣ Chat (Simple & Streaming)
```bash
# Regular chat
curl -X POST "http://localhost:8000/api/chat/" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "stream": false}'

# Streaming (use -N flag!)
curl -N -X POST "http://localhost:8000/api/chat/" \
  -H "Content-Type: application/json" \
  -d '{"message": "Count to 5", "stream": true}'
```

### 2️⃣ Chain-of-Thought Reasoning
```bash
# Streaming
curl -N -X POST "http://localhost:8000/api/chat/reason" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is 2 + 3 * 5?", "stream": true}'

# JSON response
curl -X POST "http://localhost:8000/api/chat/reason" \
  -H "Content-Type: application/json" \
  -d '{"query": "Solve x^2 - 5x + 6 = 0", "stream": false}'
```

Returns structured JSON:
```json
{
  "thinking": "reasoning steps...",
  "steps": ["step1", "step2"],
  "answer": "final answer"
}
```

### Health Check
```bash
curl http://localhost:8000/api/health
```

## 🧪 Streaming Tips

### ⚠️ Use `-N` flag for real-time streaming!

```bash
# ❌ Waits for complete response
curl -X POST "http://localhost:8000/api/chat/" \
  -d '{"message": "Hello", "stream": true}'

# ✅ Shows real-time tokens
curl -N -X POST "http://localhost:8000/api/chat/" \
  -d '{"message": "Hello", "stream": true}'
```

### JavaScript Client
```javascript
async function streamChat(message) {
  const response = await fetch('http://localhost:8000/api/chat/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, stream: true })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const text = decoder.decode(value);
    text.split('\n').forEach(line => {
      if (line.startsWith('data: ')) console.log(line.slice(6));
    });
  }
}
```

## 📦 Tech Stack

| Component | Technology |
|-----------|------------|
| **Framework** | FastAPI |
| **LLM** | LangChain + Google Gemini |
| **Streaming** | Server-Sent Events (SSE) |
| **Validation** | Pydantic |
| **Config** | Python dotenv |

## 🎓 Features

✅ REST API Design  
✅ Async Programming  
✅ Data Streaming (SSE)  
✅ LangChain Integration  
✅ Type Safety (Pydantic)  
✅ Environment Config  
✅ Chain-of-Thought Reasoning
