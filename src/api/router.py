from fastapi import APIRouter
from api.chat import router as chat_router

router = APIRouter()  # No prefix here, main.py adds /api

router.include_router(chat_router)
