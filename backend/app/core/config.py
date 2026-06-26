import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "App Contabilidad"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql+asyncpg://app_user:app_pass@localhost:5432/app_contabilidad"
    DATABASE_SYNC_URL: str = "postgresql://app_user:app_pass@localhost:5432/app_contabilidad"
    SYNC_SERVER_URL: str = ""

    SECRET_KEY: str = "change-this-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://app-contabilidad.vercel.app",
        "https://app-contabilidad.railway.app",
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
