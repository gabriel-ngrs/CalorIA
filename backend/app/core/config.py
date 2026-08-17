from __future__ import annotations

from typing import Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Valor de fábrica de SECRET_KEY. Fora de desenvolvimento a aplicação recusa
# subir com ele — ver `_validate_secret_key`.
INSECURE_SECRET_KEY = "insecure-default-key-change-in-production"
# Piso de entropia aceito para a chave de assinatura dos JWT (HS256).
MIN_SECRET_KEY_LENGTH = 32


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
    SECRET_KEY: str = INSECURE_SECRET_KEY
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
    #
    # 2026-08-17: `llama-3.3-70b-versatile` seguiu o mesmo caminho — a família
    # Llama inteira saiu do catálogo de chat da Groq e o registro por TEXTO
    # passou a responder 404. Substituído por `openai/gpt-oss-120b`, que expõe o
    # raciocínio em campo `reasoning` separado e por isso devolve `content` com
    # JSON limpo (o `qwen` de visão vaza `<think>` no conteúdo — ver
    # GROQ_VISION_REASONING abaixo).
    GROQ_TEXT_MODEL: str = "openai/gpt-oss-120b"
    GROQ_VISION_MODEL: str = "qwen/qwen3.6-27b"
    # `reasoning_effort` da chamada de visão. Vazio = não envia o parâmetro.
    # Modelos com raciocínio exposto gastam o orçamento de tokens no bloco
    # `<think>` e truncam antes do JSON; "none" devolve a resposta direta.
    GROQ_VISION_REASONING: str = "none"

    # --- Parâmetros de amostragem, explícitos para o eval ser reprodutível ---
    # Antes viviam implícitos no corpo do `AIClient`, e uma comparação A/B de
    # prompt não tinha como declarar sob quais parâmetros foi medida.
    #
    # Temperatura das chamadas com system prompt (todo o pipeline de parsing).
    GROQ_TEMPERATURE: float = 0.1
    # Temperatura das chamadas sem system prompt (os sete prompts do
    # InsightsGenerator). O valor difere por herança, não por decisão — está
    # preservado de propósito: mudá-lo agora contaminaria a linha de base do eval.
    GROQ_TEMPERATURE_SEM_SYSTEM: float = 0.3
    # Teto de tokens de saída. Generoso o bastante para os arrays JSON do
    # pipeline; existe para limitar custo, não para moldar a resposta.
    #
    # NÃO é só teto de custo: a Groq RESERVA `max_tokens` na conta do limite de
    # tokens por minuto. Com 8192, o valor anterior, toda chamada do free tier
    # (8000 TPM) era recusada com 413 Payload Too Large antes de sair do chão —
    # 799 de prompt + 8192 = 8991 pedidos contra um teto de 8000. 2048 cobre com
    # folga a maior saída observada no pipeline (~340 tokens) e deixa ~5900 de
    # espaço para o prompt, sendo que a maior entrada medida é a de visão, com
    # 3204 (constante: a Groq redimensiona a imagem do lado dela).
    GROQ_MAX_TOKENS: int = 2048
    # Semente de amostragem. `-1` = não enviar o parâmetro (comportamento atual).
    GROQ_SEED: int = -1
    # Timeout de uma requisição ao provedor.
    GROQ_TIMEOUT_SECONDS: float = 60.0
    # Retentativas internas do SDK (o default da lib é 2). O backoff próprio do
    # AIClient soma sobre isto.
    GROQ_SDK_MAX_RETRIES: int = 2
    # Teto de tempo TOTAL gasto no backoff próprio por rate limit. Sem teto, a
    # rodada de eval de 2026-07-26 poderia ficar horas em espera.
    GROQ_RETRY_MAX_SECONDS: float = 120.0

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

    # --------------------------------------------------------------------------
    # Rate limiting — expressões no formato do `limits` ("10/minute")
    # --------------------------------------------------------------------------
    RATE_LIMIT_ENABLED: bool = True
    # Endpoints públicos de autenticação: alvo de força bruta e de enumeração.
    RATE_LIMIT_LOGIN: str = "10/minute"
    RATE_LIMIT_REGISTER: str = "5/minute"
    RATE_LIMIT_FORGOT_PASSWORD: str = "5/minute"
    # Endpoints de IA: o custo é em tokens do provedor, não em CPU local.
    RATE_LIMIT_AI: str = "20/minute"
    # Endpoints de IA que são leitura autenticada (insights, padrões, relatório).
    # Também gastam tokens do provedor, então também precisam de teto — mais
    # folgado que o dos POST, porque são consultas que o dashboard dispara.
    RATE_LIMIT_AI_LEITURA: str = "40/minute"
    # Backend de contagem. Vazio = memória do processo (dev e testes). Em
    # produção com mais de um worker, apontar para o Redis com o prefixo
    # `async+` exigido pelo `limits` em contexto assíncrono:
    # `async+redis://redis:6379/1`.
    RATE_LIMIT_STORAGE_URI: str = ""
    # Ligar SOMENTE quando houver um proxy reverso confiável à frente (Caddy em
    # produção). Sem proxy, `X-Forwarded-For` é forjável pelo cliente e viraria
    # um caminho trivial de contornar o limite.
    RATE_LIMIT_TRUST_FORWARDED_FOR: bool = False

    # --------------------------------------------------------------------------
    # Limites de payload
    # --------------------------------------------------------------------------
    REMINDERS_BATCH_MAX_ITEMS: int = 50

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    @model_validator(mode="after")
    def _validate_secret_key(self) -> Self:
        """Recusa subir fora de desenvolvimento com chave de assinatura fraca.

        O default existe para o `make init` funcionar sem configuração; fora de
        desenvolvimento ele assina JWT que qualquer leitor do repositório
        consegue forjar.
        """
        if self.is_development:
            return self
        if self.SECRET_KEY == INSECURE_SECRET_KEY:
            raise ValueError(
                "SECRET_KEY está no valor default inseguro. Defina uma chave "
                f"própria com ao menos {MIN_SECRET_KEY_LENGTH} caracteres "
                f"(APP_ENV={self.APP_ENV})."
            )
        if len(self.SECRET_KEY) < MIN_SECRET_KEY_LENGTH:
            raise ValueError(
                f"SECRET_KEY tem {len(self.SECRET_KEY)} caracteres; o mínimo é "
                f"{MIN_SECRET_KEY_LENGTH} (APP_ENV={self.APP_ENV})."
            )
        return self


settings = Settings()
