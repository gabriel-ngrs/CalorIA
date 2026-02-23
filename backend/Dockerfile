# =============================================================================
# CalorIA Backend — Dockerfile (multi-stage)
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: Builder — instala dependências em virtualenv isolado
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /app

# Dependências de sistema para compilar pacotes nativos (asyncpg, bcrypt)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Criar virtualenv isolado
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Instalar dependências antes de copiar o código (melhor cache do Docker)
COPY pyproject.toml .
# Criar pacote mínimo para satisfazer o build backend
RUN mkdir -p app && touch app/__init__.py \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

# ---------------------------------------------------------------------------
# Stage 2: Runtime — imagem final enxuta
# ---------------------------------------------------------------------------
FROM python:3.12-slim

WORKDIR /app

# Apenas runtime de sistema (libpq para asyncpg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copiar virtualenv do builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copiar código da aplicação
COPY . .

# Usuário não-root para segurança
RUN adduser --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
