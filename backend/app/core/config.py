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
    # IA — Groq (texto e visão, 100% gratuito)
    # --------------------------------------------------------------------------
    GROQ_API_KEY: str = ""
    # Modelos Groq, configuráveis por ambiente.
    #
    # Ficavam fixos como constantes de módulo em `services/ai/ai_client.py`, e
    # quando o modelo de visão foi descontinuado pela Groq a análise por foto
    # passou a responder 404 model_not_found — sem forma de trocar sem deploy.
    GROQ_TEXT_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_VISION_MODEL: str = "qwen/qwen3.6-27b"
    # `reasoning_effort` da chamada de visão. Vazio = não envia o parâmetro.
    # Modelos com raciocínio exposto gastam o orçamento de tokens no bloco
    # `<think>` e truncam antes do JSON; "none" devolve a resposta direta.
    GROQ_VISION_REASONING: str = "none"

    # --------------------------------------------------------------------------
    # Web Push (VAPID)
    # --------------------------------------------------------------------------
    VAPID_PRIVATE_KEY: str = ""
    VAPID_PUBLIC_KEY: str = ""
    VAPID_CLAIMS_EMAIL: str = "admin@caloria.app"

    # --------------------------------------------------------------------------
    # E-mail transacional (SMTP) — sem SMTP_HOST, EmailService degrada para log
    # --------------------------------------------------------------------------
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "CalorIA <no-reply@caloria.app>"

    # URL base do frontend, usada para montar o link de reset de senha
    FRONTEND_URL: str = "http://localhost:3000"

    # Expiração do token de reset de senha (minutos, ≤ 60)
    RESET_TOKEN_EXPIRE_MINUTES: int = 60

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"


settings = Settings()
