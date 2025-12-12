from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1.chat import router as chat_router
from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    try:
        print(f"Starting {getattr(settings, 'APP_NAME', 'Unknown App')}...")
        print(f"Default Model: {getattr(settings, 'DEFAULT_MODEL', 'Unknown')}")
        db_url = getattr(settings, "DATABASE_URL", "Not configured")
        print(f"Database: {db_url.split('@')[-1] if '@' in db_url else db_url}")
        host = getattr(settings, "HOST", "0.0.0.0")
        port = getattr(settings, "PORT", 8000)
        print(f"API Docs: http://{host}:{port}/docs")
        yield
        print("Shutting down...")
    except Exception as e:
        print(f"❌ Lifespan error: {e}")
        import traceback

        traceback.print_exc()
        raise


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Returns:
        FastAPI: Configured application instance
    """
    print("Creating FastAPI app...")
    app = FastAPI(
        title="LangChain + LangGraph Agent API",
        description="agent with web search and calculation capabilities",
        version="1.0.0",
        lifespan=lifespan,
    )

    print("Adding CORS middleware...")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    print("Including chat router...")
    app.include_router(chat_router)

    print("Adding root endpoint...")

    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "service": "LangChain + LangGraph Agent",
            "version": "1.0.0",
            "documentation": "/docs",
            "health": "/health",
        }

    print("Adding health endpoint...")

    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "default_model": getattr(settings, "DEFAULT_MODEL", "Unknown"),
            "database_url": (
                getattr(settings, "DATABASE_URL", "Not configured").split("@")[-1]
                if getattr(settings, "DATABASE_URL", None)
                else "not configured"
            ),
        }

    print("✅ App created successfully!")
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
