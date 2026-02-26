from __future__ import annotations

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
    # CORS — string comma-separated para compatibilidade com pydantic-settings v2
    # --------------------------------------------------------------------------
    BACKEND_CORS_ORIGINS: str = ""

    @property
    def cors_origins(self) -> list[str]:
        if not self.BACKEND_CORS_ORIGINS:
            return []
        return [o.strip() for o in self.BACKEND_CORS_ORIGINS.split(",") if o.strip()]

    # --------------------------------------------------------------------------
    # Groq API (IA — Llama)
    # --------------------------------------------------------------------------
    GEMINI_API_KEY: str = ""   # mantido por compatibilidade
    GROQ_API_KEY: str = ""

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
