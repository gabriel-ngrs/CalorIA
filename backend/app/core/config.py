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
    # Telegram Bot
    # --------------------------------------------------------------------------
    TELEGRAM_BOT_TOKEN: str = ""

    # --------------------------------------------------------------------------
    # WhatsApp — Evolution API
    # --------------------------------------------------------------------------
    EVOLUTION_API_URL: str = "http://evolution_api:8080"
    EVOLUTION_API_KEY: str = ""
    EVOLUTION_INSTANCE_NAME: str = "caloria"

    # --------------------------------------------------------------------------
    # Google Gemini API (IA)
    # --------------------------------------------------------------------------
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""  # mantido por compatibilidade

    # --------------------------------------------------------------------------
    # Web Push (VAPID)
    # --------------------------------------------------------------------------
    VAPID_PRIVATE_KEY: str = ""
    VAPID_PUBLIC_KEY: str = ""
    VAPID_CLAIMS_EMAIL: str = "admin@caloria.app"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"


settings = Settings()
