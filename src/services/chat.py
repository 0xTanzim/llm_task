"""
Chat Service: Chat business logic
Combines LLM, Memory, and Prompts
"""
from typing import AsyncGenerator, Dict, Any
import json
import re
from langchain_core.messages import HumanMessage, AIMessage

from services.llm import stream_chat, invoke_chat
from services.memory import get_session_history
from chains.prompts import chat_template, reason_template


async def chat_stream(message: str, session_id: str, response_mode: str) -> AsyncGenerator[Dict[str, Any], None]:
    """Stream chat response with memory."""
    history = get_session_history(session_id)
    messages = chat_template.format_messages(
        history=history.messages,
        input=message,
        response_mode=response_mode
    )
    
    full_response = ""
    async for chunk in stream_chat(messages):
        full_response += chunk
        yield {"type": "chunk", "content": chunk}
    
    # Save after complete
    history.add_message(HumanMessage(content=message))
    history.add_message(AIMessage(content=full_response))

    yield {"type": "final", "content": full_response}


async def chat_invoke(message: str, session_id: str, response_mode: str) -> str:
    """Get chat response with memory."""
    history = get_session_history(session_id)
    messages = chat_template.format_messages(
        history=history.messages,
        input=message,
        response_mode=response_mode
    )
    
    response = await invoke_chat(messages)
    
    # Save to history
    history.add_message(HumanMessage(content=message))
    history.add_message(AIMessage(content=response))
    
    return response


async def reason_stream(query: str, session_id: str) -> AsyncGenerator[Dict[str, Any], None]:
    """Stream reasoning response with memory."""
    history = get_session_history(session_id)
    messages = reason_template.format_messages(
        history=history.messages,
        input=query
    )
    
    full_response = ""
    async for chunk in stream_chat(messages):
        full_response += chunk
        yield {"type": "chunk", "content": chunk}
    
    # Save after complete
    history.add_message(HumanMessage(content=query))
    history.add_message(AIMessage(content=full_response))

    parsed = full_response
    try:
        parsed = json.loads(full_response)
    except json.JSONDecodeError:
        pass

    yield {"type": "final", "content": parsed}


async def reason_invoke(query: str, session_id: str) -> dict:
    """Get reasoning response with memory."""
    history = get_session_history(session_id)
    messages = reason_template.format_messages(
        history=history.messages,
        input=query
    )
    
    response = await invoke_chat(messages)
    
    # Save to history
    history.add_message(HumanMessage(content=query))
    history.add_message(AIMessage(content=response))
    
    # Try to parse JSON
    match = re.search(r'\{.*\}', response, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    
    return {"response": response}
