from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import router as api_router
from core.config import settings

app = FastAPI(title="FastAPI LangChain Service")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "FastAPI + LangChain", "docs": "/docs"}


@app.on_event("startup")
async def startup():
    print(f"🚀 Server started | Model: {settings.LLM_MODEL}")
    print(f"🔑 API Key loaded: {'Yes' if settings.GOOGLE_API_KEY else 'No'}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
