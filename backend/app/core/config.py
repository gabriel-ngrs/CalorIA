from __future__ import annotations

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --------------------------------------------------------------------------
    # App
    # --------------------------------------------------------------------------
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    # --------------------------------------------------------------------------
    # Banco de dados
    # --------------------------------------------------------------------------
    DATABASE_URL: str = "postgresql+asyncpg://caloria:caloria@localhost:5432/caloria_db"

    # --------------------------------------------------------------------------
    # Redis
    # --------------------------------------------------------------------------
    REDIS_URL: str = "redis://localhost:6379/0"

    # --------------------------------------------------------------------------
    # Segurança JWT
    # --------------------------------------------------------------------------
    SECRET_KEY: str = "insecure-default-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # --------------------------------------------------------------------------
    # CORS
    # --------------------------------------------------------------------------
    BACKEND_CORS_ORIGINS: list[str] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str) and v:
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v or []

    # --------------------------------------------------------------------------
    # Google Gemini API
    # --------------------------------------------------------------------------
    GEMINI_API_KEY: str = ""

    # --------------------------------------------------------------------------
    # Telegram
    # --------------------------------------------------------------------------
    TELEGRAM_BOT_TOKEN: str = ""

    # --------------------------------------------------------------------------
    # Evolution API (WhatsApp)
    # --------------------------------------------------------------------------
    EVOLUTION_API_URL: str = ""
    EVOLUTION_API_KEY: str = ""
    EVOLUTION_INSTANCE_NAME: str = "caloria"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"


settings = Settings()
