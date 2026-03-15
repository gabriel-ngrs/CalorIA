import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import settings

# ─── Logging config ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
http_logger = logging.getLogger("caloria.http")
# ───────────────────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Aquece a pool de conexões no startup — evita cold start na primeira requisição
    from app.core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        await session.execute(text("SELECT 1"))
    yield


app = FastAPI(
    title="CalorIA",
    description="API do diário alimentar inteligente CalorIA",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600,  # cache preflight OPTIONS por 1 hora — elimina round-trip repetitivo
)


@app.middleware("http")
async def timing_middleware(request: Request, call_next: Any) -> Any:
    """Loga método, path, status e duração de cada requisição HTTP."""
    start = time.perf_counter()
    response = await call_next(request)
    ms = (time.perf_counter() - start) * 1000
    # Ignora health check para não poluir o log
    if request.url.path != "/health":
        flag = "⚠️ LENTO" if ms > 500 else ""
        http_logger.info(
            f"[HTTP] {request.method:6} {request.url.path:<45} {response.status_code}  {ms:7.1f}ms  {flag}"
        )
    return response


from app.api.v1 import router as api_v1_router

app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}
