from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from config import settings


def get_llm() -> ChatOpenAI:
    """Initialize ChatOpenAI with configured settings.

    Returns:
        ChatOpenAI: Configured model instance
    """
    
    return ChatOpenAI(
        model=settings.LLM_MODEL,
        base_url=settings.OPENAI_BASE_URL,
        api_key=SecretStr(settings.GOOGLE_API_KEY) if settings.GOOGLE_API_KEY else None,
    )
