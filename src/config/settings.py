"""Application configuration."""

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

# Load environment variables from project root
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Settings:
    """Application settings with environment variable validation."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return

        self.APP_NAME = os.getenv("APP_NAME", "LangChain Agent API")
        self.PORT = int(os.getenv("PORT", 8000))
        self.HOST = os.getenv("HOST", "0.0.0.0")
        self.DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

        self.DATABASE_URL = os.getenv(
            "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres"
        )

        self.OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
        self.OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

        if not self.OPENROUTER_API_KEY:
            print(
                "WARNING: OPENROUTER_API_KEY not set. LLM functionality may not work."
            )

        self.DEFAULT_MODEL = "google/gemini-2.5-flash-lite-preview-09-2025"
        self.OPENAI_MODEL = "openai/gpt-4o-mini"
        self.ANTHROPIC_MODEL = "anthropic/claude-3-haiku"

        self.LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0.7))
        self.LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", 2048))

        self.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        self.TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

        if not self.TAVILY_API_KEY:
            print(
                "WARNING: TAVILY_API_KEY not set. Web search functionality will be limited."
            )

        self._initialized = True


settings = Settings()


def get_model(model_type: str = "default") -> ChatOpenAI:
    """
    Get configured LLM model based on type.

    Args:
        model_type: One of "default", "openai", "anthropic"

    Returns:
        Configured ChatOpenAI instance
    """
    if not settings.OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY is not configured")

    api_key = SecretStr(settings.OPENROUTER_API_KEY)

    model_map = {
        "default": settings.DEFAULT_MODEL,
        "openai": settings.OPENAI_MODEL,
        "anthropic": settings.ANTHROPIC_MODEL,
    }

    model_name = model_map.get(model_type, settings.DEFAULT_MODEL)

    return ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=settings.OPENROUTER_BASE_URL,
        temperature=settings.LLM_TEMPERATURE,
    )
