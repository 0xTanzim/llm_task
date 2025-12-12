"""LLM configuration and initialization."""

from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from config import settings


def get_llm() -> ChatOpenAI:
    """Initialize ChatOpenAI with configured settings.

    Returns:
        ChatOpenAI: Configured model instance

    Raises:
        ValueError: If GOOGLE_API_KEY is not set
    """
    if not settings.GOOGLE_API_KEY:
        raise ValueError(
            "GOOGLE_API_KEY environment variable is required. "
            "Get your key from https://makersuite.google.com/app/apikey"
        )

    return ChatOpenAI(
        model=settings.LLM_MODEL,
        api_key=SecretStr(settings.GOOGLE_API_KEY),
        base_url=settings.OPENAI_BASE_URL,
        temperature=settings.LLM_TEMPERATURE,
    )
