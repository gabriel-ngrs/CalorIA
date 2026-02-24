from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup: inicia bot Telegram em modo polling (dev)
    if settings.TELEGRAM_BOT_TOKEN:
        from app.bots.telegram.bot import start_polling
        await start_polling()
    yield
    # Shutdown: encerra bot Telegram
    if settings.TELEGRAM_BOT_TOKEN:
        from app.bots.telegram.bot import stop_polling
        await stop_polling()


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
)

from app.api.v1 import router as api_v1_router

app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}
