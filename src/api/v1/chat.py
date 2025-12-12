import json
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

from services.chat.service import ChatService

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """Chat request model with input validation."""

    message: str = Field(
        ..., min_length=1, max_length=10000, description="User message"
    )
    thread_id: str | None = Field(None, description="Conversation thread ID")

    @field_validator("message")
    @classmethod
    def validate_message_content(cls, v: str) -> str:
        from core.validation import validate_message

        return validate_message(v)

    @field_validator("thread_id")
    @classmethod
    def validate_thread_format(cls, v: str | None) -> str | None:
        from core.validation import validate_thread_id

        return validate_thread_id(v)


class ChatResponse(BaseModel):
    """Chat response model."""

    response: str = Field(..., description="AI response")
    thread_id: str = Field(..., description="Conversation thread ID")
    model_used: str = Field(..., description="LLM model used for this response")
    llm_calls: int = Field(..., description="Number of LLM calls made")
    tools_used: list[str] = Field(default_factory=list, description="Tools used")


class HistoryResponse(BaseModel):
    """Conversation history response."""

    thread_id: str = Field(..., description="Conversation thread ID")
    messages: list[dict[str, Any]] = Field(..., description="Message history")


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message and receive a complete response.

    This endpoint waits for the full agent execution to complete before returning.

    Args:
        request: Chat request with message and optional thread_id

    Returns:
        ChatResponse: AI response with thread_id, llm_calls, and tools_used
    """
    service = ChatService()
    try:
        result = await service.chat(request.message, request.thread_id)
        return ChatResponse(**result)
    except Exception as e:
        import traceback

        error_detail = f"Chat error: {str(e)}"
        print(f"❌ {error_detail}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_detail)


@router.post("/stream")
async def stream(request: ChatRequest):
    """
    Stream agent responses in real-time using Server-Sent Events (SSE).

    This endpoint streams the agent's thinking process, tool calls, and final response.

    Event types:
    - thread_id: Initial thread ID
    - tool_call: Agent is calling a tool
    - tool_result: Tool execution result
    - response: AI response content
    - complete: Execution complete
    - error: Error occurred

    Args:
        request: Chat request with message and optional thread_id

    Returns:
        StreamingResponse: Server-sent events stream
    """
    service = ChatService()
    try:

        async def generate():
            try:
                async for chunk in service.stream(request.message, request.thread_id):
                    yield f"data: {json.dumps(chunk)}\n\n"
            except Exception as e:
                error_data = {"type": "error", "error": str(e), "done": True}
                yield f"data: {json.dumps(error_data)}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except Exception as e:
        import traceback

        error_detail = f"Stream error: {str(e)}"
        print(f"❌ {error_detail}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_detail)


@router.get("/history/{thread_id}", response_model=HistoryResponse)
async def get_history(thread_id: str):
    """
    Get conversation history for a specific thread.

    Args:
        thread_id: Conversation thread ID

    Returns:
        HistoryResponse: Thread ID and message history
    """
    from core.validation import validate_thread_id

    try:
        validated_thread_id = validate_thread_id(thread_id)
        if validated_thread_id is None:
            raise HTTPException(status_code=400, detail="Thread ID is required")

        service = ChatService()
        messages = await service.get_history(validated_thread_id)
        return HistoryResponse(thread_id=validated_thread_id, messages=messages)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback

        error_detail = f"History error: {str(e)}"
        print(f"❌ {error_detail}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_detail)
