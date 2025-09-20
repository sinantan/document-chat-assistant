from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.api.v1 import api_router
from app.core.config import settings
from app.core.errors import setup_exception_handlers
from app.db.mongo import close_mongo_connection, connect_to_mongo
from app.middleware.request_id import RequestIDMiddleware


logger = structlog.get_logger()


def get_limiter() -> Limiter:
    return Limiter(
        key_func=get_remote_address,
        default_limits=[f"{settings.RATE_LIMIT_REQUESTS}/{settings.RATE_LIMIT_WINDOW}minute"]
    )


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting up Document Chat Assistant", version=settings.APP_VERSION)
    
    try:
        await connect_to_mongo()
        logger.info("MongoDB connection established")
    except Exception as e:
        logger.error("MongoDB connection failed", error=str(e))
        raise
    
    if settings.AUTO_MIGRATE:
        try:
            logger.info("Running database migrations...")
            import subprocess
            result = subprocess.run(
                ["poetry", "run", "alembic", "upgrade", "head"],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info("Database migrations completed successfully")
        except subprocess.CalledProcessError as e:
            logger.error("Database migration failed", error=e.stderr)
            raise
        except Exception as e:
            logger.error("Unexpected error during migration", error=str(e))
            raise
    
    try:
        yield
    finally:
        await close_mongo_connection()
        logger.info("Shutting down Document Chat Assistant")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="JWT-based document chat assistant with PDF processing and AI conversations",
        docs_url="/docs",
        redoc_url="/redoc", 
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    
    limiter = get_limiter()
    app.state.limiter = limiter  # type: ignore
    
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
        return _rate_limit_exceeded_handler(request, exc)
    
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
    app.add_middleware(SlowAPIMiddleware)  # type: ignore
    app.add_middleware(RequestIDMiddleware)
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )
    
    setup_exception_handlers(app)
    
    app.include_router(api_router, prefix="/api/v1")
    
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "version": settings.APP_VERSION}
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
