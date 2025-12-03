"""Chat controller that delegates to services while enforcing UX rules."""
import json
from typing import Literal, Optional, List

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage

from services.chat import chat_stream, chat_invoke, reason_stream, reason_invoke
from services.memory import get_session_history, clear_session

router = APIRouter(prefix="/chat", tags=["Chat"])


STREAM_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


# ========== Request Models ==========
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, example="Hello!")
    stream: bool = Field(default=True)
    session_id: str = Field(default="default", min_length=1, max_length=128, example="user123")
    response_mode: Literal["helpful", "concise", "expert"] = Field(
        default="helpful",
        description="Controls tone and level of detail in the response.",
    )


class ReasonRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000, example="What is 2 + 3 * 5?")
    stream: bool = Field(default=True)
    session_id: str = Field(default="default", min_length=1, max_length=128, example="user123")


class ChatResponse(BaseModel):
    session_id: str = Field(..., example="user123")
    response_mode: Literal["helpful", "concise", "expert"]
    response: str = Field(..., description="Full assistant reply once streaming completes")


class WorkflowStep(BaseModel):
    step: Literal["START", "PLAN", "TOOL", "OBSERVE", "OUTPUT"]
    content: str = Field(..., description="One concise description of the action")
    tool_call: Optional[str] = Field(None, description="Tool name if invoked")
    tool_input: Optional[str] = Field(None, description="Arguments provided to the tool")


class ReasoningResult(BaseModel):
    workflow: List[WorkflowStep] = Field(..., description="Ordered reasoning trace")
    answer: str = Field(..., description="Final natural-language conclusion")


class ReasonResponse(BaseModel):
    session_id: str = Field(..., example="user123")
    result: ReasoningResult


class HistoryMessage(BaseModel):
    role: Literal["user", "ai"]
    content: str = Field(... , description="Message content")


class HistoryResponse(BaseModel):
    session_id: str = Field(..., example="user123")
    messages: List[HistoryMessage]


class DeleteHistoryResponse(BaseModel):
    message: str = Field(..., description="Result message")


# ========== Endpoints ==========
@router.post("/", response_model=ChatResponse, summary="Chat with the AI assistant")
async def chat(request: ChatRequest):
    """Chat with conversation memory."""
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message cannot be empty.")

    if request.stream:
        async def gen():
            try:
                async for event in chat_stream(message, request.session_id, request.response_mode):
                    payload = {
                        "session_id": request.session_id,
                        "type": event["type"],
                        "response_mode": request.response_mode,
                    }
                    if event["type"] == "chunk":
                        payload["chunk"] = event["content"]
                    elif event["type"] == "final":
                        payload["message"] = event["content"]
                    yield f"data: {json.dumps(payload)}\n\n"
            except Exception as exc:  # noqa: BLE001 - surface errors to client
                error_payload = {
                    "session_id": request.session_id,
                    "type": "error",
                    "message": str(exc),
                }
                yield f"data: {json.dumps(error_payload)}\n\n"
                return
            yield f"data: {json.dumps({'session_id': request.session_id, 'type': 'done'})}\n\n"

        return StreamingResponse(gen(), media_type="text/event-stream", headers=STREAM_HEADERS)

    response = await chat_invoke(message, request.session_id, request.response_mode)
    return ChatResponse(
        session_id=request.session_id,
        response_mode=request.response_mode,
        response=response,
    )


@router.post("/reason", response_model=ReasonResponse, summary="Reason with structured workflow")
async def reason(request: ReasonRequest):
    """Chain of thought reasoning with memory."""
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query cannot be empty.")

    if request.stream:
        async def gen():
            try:
                async for event in reason_stream(query, request.session_id):
                    payload = {
                        "session_id": request.session_id,
                        "type": event["type"],
                    }
                    if event["type"] == "chunk":
                        payload["chunk"] = event["content"]
                    elif event["type"] == "final":
                        payload["message"] = event["content"]
                    yield f"data: {json.dumps(payload)}\n\n"
            except Exception as exc:  # noqa: BLE001
                error_payload = {
                    "session_id": request.session_id,
                    "type": "error",
                    "message": str(exc),
                }
                yield f"data: {json.dumps(error_payload)}\n\n"
                return
            yield f"data: {json.dumps({'session_id': request.session_id, 'type': 'done'})}\n\n"

        return StreamingResponse(gen(), media_type="text/event-stream", headers=STREAM_HEADERS)

    result = await reason_invoke(query, request.session_id)
    return ReasonResponse(session_id=request.session_id, result=result)


@router.get("/history/{session_id}", response_model=HistoryResponse, summary="Retrieve session history")
async def get_history(session_id: str):
    """Get conversation history."""
    history = get_session_history(session_id)
    return HistoryResponse(
        session_id=session_id,
        messages=[
            HistoryMessage(role="user" if isinstance(m, HumanMessage) else "ai", content=m.content)
            for m in history.messages
        ],
    )


@router.delete("/history/{session_id}", response_model=DeleteHistoryResponse, summary="Delete session history")
async def delete_history(session_id: str):
    """Clear conversation history."""
    if clear_session(session_id):
        return DeleteHistoryResponse(message=f"History cleared for {session_id}")
    return DeleteHistoryResponse(message="Session not found")
