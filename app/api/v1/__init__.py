from fastapi import APIRouter

from app.api.v1 import auth, documents, messages

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(messages.router, prefix="/messages", tags=["Chat"])

__all__ = ["api_router"]
