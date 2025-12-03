import os
from dotenv import load_dotenv

# Load .env from project root (parent of src/)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env"))


class Settings:
    """settings from environment."""
    
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-2.5-flash")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    OPENAI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai/"

settings = Settings()

