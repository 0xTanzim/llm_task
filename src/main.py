from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings

def create_app() -> FastAPI:
    app = FastAPI()


    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    async def root():
        return {"message": "FastAPI + LangChain", "docs": "/docs"}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
