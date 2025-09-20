from functools import lru_cache
from typing import Any, Dict, List, Optional

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    APP_NAME: str = "Document Chat Assistant"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    AUTO_MIGRATE: bool = Field(default=True)
    
    SECRET_KEY: str = Field(..., min_length=5)
    JWT_SECRET_KEY: str = Field(..., min_length=5)
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    POSTGRES_USER: str = Field(..., min_length=1)
    POSTGRES_PASSWORD: str = Field(..., min_length=1)
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432, ge=1, le=65535)
    POSTGRES_DB: str = Field(..., min_length=1)
    DATABASE_URL: Optional[PostgresDsn] = None
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info) -> Any:
        if isinstance(v, str):
            return v
        values = info.data if info else {}
        return PostgresDsn.build(
            scheme="postgresql",
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_HOST"),
            port=values.get("POSTGRES_PORT"),
            path=values.get("POSTGRES_DB") or "",
        )
    
    MONGO_HOST: str = Field(default="localhost")
    MONGO_PORT: int = Field(default=27017, ge=1, le=65535)
    MONGO_DB: str = Field(..., min_length=1)
    MONGO_USER: Optional[str] = None
    MONGO_PASSWORD: Optional[str] = None
    MONGO_URI: Optional[str] = None
    
    @field_validator("MONGO_URI", mode="before")
    @classmethod
    def assemble_mongo_connection(cls, v: Optional[str], info) -> str:
        if isinstance(v, str):
            return v
        
        values = info.data if info else {}
        user = values.get("MONGO_USER")
        password = values.get("MONGO_PASSWORD")
        host = values.get("MONGO_HOST")
        port = values.get("MONGO_PORT")
        
        if user and password:
            return f"mongodb://{user}:{password}@{host}:{port}"
        return f"mongodb://{host}:{port}"
    
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379, ge=1, le=65535)
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = Field(default=0, ge=0)
    REDIS_URI: Optional[str] = None
    
    @field_validator("REDIS_URI", mode="before")
    @classmethod
    def assemble_redis_connection(cls, v: Optional[str], info) -> str:
        if isinstance(v, str):
            return v
        
        values = info.data if info else {}
        host = values.get("REDIS_HOST")
        port = values.get("REDIS_PORT")
        password = values.get("REDIS_PASSWORD")
        db = values.get("REDIS_DB")
        
        if password:
            return f"redis://:{password}@{host}:{port}/{db}"
        return f"redis://{host}:{port}/{db}"
    
    GEMINI_API_KEY: str = Field(..., min_length=1)
    GEMINI_MODEL: str = Field(default="gemini-2.5-flash")
    GEMINI_MAX_TOKENS: int = Field(default=2048, ge=1)
    GEMINI_TEMPERATURE: float = Field(default=0.7, ge=0.0, le=2.0)
    
    MAX_FILE_SIZE_MB: int = Field(default=50, ge=1, le=100)
    ALLOWED_FILE_TYPES: List[str] = Field(default=["application/pdf"])
    PDF_CHUNK_SIZE: int = Field(default=1000, ge=100, le=5000)
    PDF_CHUNK_OVERLAP: int = Field(default=200, ge=0, le=1000)
    
    RATE_LIMIT_REQUESTS: int = Field(default=100, ge=1)
    RATE_LIMIT_WINDOW: int = Field(default=60, ge=1)
    
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(default="json")
    
    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
