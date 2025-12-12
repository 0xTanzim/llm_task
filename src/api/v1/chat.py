
import json
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from services.chat.service import ChatService

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])
service = ChatService()


class ChatRequest(BaseModel):
    """Chat request model."""

    message: str = Field(..., min_length=1, description="User message")
    thread_id: Optional[str] = Field(None, description="Conversation thread ID")


class ChatResponse(BaseModel):
    """Chat response model."""

    response: str = Field(..., description="AI response")
    thread_id: str = Field(..., description="Conversation thread ID")


@router.post("/", response_model=ChatResponse)
def chat(request: ChatRequest):
    """Send a message and receive a response.

    Args:
        request: Chat request with message and optional thread_id

    Returns:
        ChatResponse: AI response with thread_id
    """
    try:
        result = service.chat(request.message, request.thread_id)
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@router.post("/stream")
async def stream(request: ChatRequest):
    """Stream agent responses in real-time.

    Args:
        request: Chat request with message and optional thread_id

    Returns:
        StreamingResponse: Server-sent events stream
    """
    try:

        async def generate():
            try:
                async for chunk in service.stream(request.message, request.thread_id):
                    yield f"data: {json.dumps(chunk)}\n\n"
            except Exception as e:
                error_data = {"error": str(e), "done": True}
                yield f"data: {json.dumps(error_data)}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stream error: {str(e)}")
