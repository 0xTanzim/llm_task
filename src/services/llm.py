"""
LLM Service Layer - Clean separation of concerns
All LLM operations go here, no business logic in routes
"""
from typing import AsyncGenerator
from langchain_openai import ChatOpenAI

from core.config import settings


# Single LLM instance
_llm = None


def get_llm() -> ChatOpenAI:
    """Get or create LLM instance."""
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


async def stream_response(prompt: str) -> AsyncGenerator[str, None]:
    """
    Stream response token by token.
    Used by all endpoints that need streaming.
    """
    llm = get_llm()
    async for chunk in llm.astream([{"role": "user", "content": prompt}]):
        if chunk.content:
            yield chunk.content


async def get_response(prompt: str) -> str:
    """Get complete response without streaming."""
    llm = get_llm()
    response = await llm.ainvoke([{"role": "user", "content": prompt}])
    return response.content
