
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1.chat import router as chat_router
from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    print(f"Starting {settings.APP_NAME}...")
    print(f"LLM Model: {settings.LLM_MODEL}")
    print(f"API Docs: http://{settings.HOST}:{settings.PORT}/docs")
    yield
    print("Shutting down...")


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Returns:
        FastAPI: Configured application instance
    """
    app = FastAPI(
        title="LangChain + LangGraph Agent API",
        description="agent with web search and calculation capabilities",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(chat_router)

    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "service": "LangChain + LangGraph Agent",
            "version": "1.0.0",
            "documentation": "/docs",
            "health": "/health",
        }

    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "model": settings.LLM_MODEL,
            "base_url": settings.OPENAI_BASE_URL,
        }

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        log_level="info" if not settings.DEBUG else "debug",
    )
