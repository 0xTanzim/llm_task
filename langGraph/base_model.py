import os

from langchain_openai import ChatOpenAI
from pydantic import SecretStr

raw_api_key = os.getenv("OPENROUTER_API_KEY")

if raw_api_key is None:
    raise ValueError(
        "OPENROUTER_API_KEY environment variable is not set. Please set it to use the model."
    )

api_key = SecretStr(raw_api_key)
base_url = "https://openrouter.ai/api/v1"


anthropic_model = ChatOpenAI(
    model="anthropic/claude-3-haiku",
    api_key=api_key,
    base_url=base_url,
)

gemini_model = ChatOpenAI(
    model="google/gemini-2.5-flash-lite-preview-09-2025",
    api_key=api_key,
    base_url=base_url,
)

openai_model = ChatOpenAI(
    model="openai/gpt-4o-mini",
    api_key=api_key,
    base_url=base_url,
    
)

default_model = gemini_model
