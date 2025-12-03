"""
LLM Service: LLM operations only
"""
from typing import AsyncGenerator, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage

from core.config import settings

_llm = None


def get_llm() -> ChatOpenAI:
    """Get singleton LLM instance."""
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            api_key=settings.GOOGLE_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
            temperature=settings.LLM_TEMPERATURE,
            streaming=True,
        )
    return _llm


async def stream_chat(messages: List[BaseMessage]) -> AsyncGenerator[str, None]:
    """Stream response from messages."""
    llm = get_llm()
    async for chunk in llm.astream(messages):
        if chunk.content:
            yield chunk.content


async def invoke_chat(messages: List[BaseMessage]) -> str:
    """Get complete response from messages."""
    llm = get_llm()
    response = await llm.ainvoke(messages)
    return response.content
