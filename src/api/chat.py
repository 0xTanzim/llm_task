"""
All Chat Endpoints - Simple & Clean
"""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json
import re

from services.llm import stream_response, get_response

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    message: str = Field(..., example="Hello!")
    stream: bool = Field(True)


class ReasonRequest(BaseModel):
    query: str = Field(..., example="What is 2 + 3 * 5?")
    stream: bool = Field(True)


# ========== SIMPLE CHAT ==========
@router.post("/")
async def chat(request: ChatRequest):
    """Simple chat with streaming."""
    prompt = request.message
    
    if request.stream:
        async def gen():
            async for chunk in stream_response(prompt):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(gen(), media_type="text/event-stream")
    
    return {"response": await get_response(prompt)}


# ========== CHAIN OF THOUGHT ==========
COT_PROMPT = """Solve step by step. Return JSON only:
{{"thinking": "your reasoning", "steps": ["step1", "step2"], "answer": "final"}}

Problem: {query}"""

@router.post("/reason")
async def reason(request: ReasonRequest):
    """Chain of thought reasoning with structured output."""
    prompt = COT_PROMPT.format(query=request.query)
    
    if request.stream:
        async def gen():
            async for chunk in stream_response(prompt):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(gen(), media_type="text/event-stream")
    
    response = await get_response(prompt)
    match = re.search(r'\{.*\}', response, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except:
            pass
    return {"response": response}
