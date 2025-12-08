import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env'))

class Settings:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.APP_NAME = os.getenv("APP_NAME", "LangChainApp")
        self.PORT = int(os.getenv("PORT", 8000))
        self.HOST = os.getenv("HOST", "0.0.0.0")



        self.DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
        self.DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
        self.SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")

        
        self.OPENAI_BASE_URL = os.getenv(
            "OPENAI_BASE_URL",
            "https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        self.LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")
        self.LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0.7))
        self.LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", 2048))
        self.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")



settings = Settings()
