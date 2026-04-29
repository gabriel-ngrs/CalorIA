import logging
import time
from typing import Any

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

db_logger = logging.getLogger("caloria.db")

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # desligamos o echo nativo — usamos nosso próprio log com timing
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)


# ─── Query timing via sync_engine events ──────────────────────────────────────
@event.listens_for(engine.sync_engine, "before_cursor_execute")
def _before_query(
    conn: Any,
    cursor: Any,
    statement: Any,
    parameters: Any,
    context: Any,
    executemany: Any,
) -> None:
    conn.info.setdefault("_qstart", []).append(time.perf_counter())


@event.listens_for(engine.sync_engine, "after_cursor_execute")
def _after_query(
    conn: Any,
    cursor: Any,
    statement: Any,
    parameters: Any,
    context: Any,
    executemany: Any,
) -> None:
    ms = (time.perf_counter() - conn.info["_qstart"].pop()) * 1000
    # Extrai primeira linha do SQL para identificar a operação
    first_line = statement.strip().splitlines()[0][:80]
    flag = "  ⚠️ LENTO" if ms > 100 else ""
    db_logger.info(f"[DB] {ms:7.1f}ms | {first_line}{flag}")


# ──────────────────────────────────────────────────────────────────────────────

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass
