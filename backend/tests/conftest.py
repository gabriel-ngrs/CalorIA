from __future__ import annotations

import os
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.core.deps import get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import User  # noqa: F401 — registra todos os modelos no metadata

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://caloria:caloria@localhost:5432/caloria_test",
)

_engine = create_async_engine(TEST_DATABASE_URL, echo=False, pool_pre_ping=True)
_TestSessionLocal = async_sessionmaker(
    _engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Redireciona get_db da app para o banco de teste
async def _get_test_db() -> AsyncGenerator[AsyncSession, None]:
    async with _TestSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = _get_test_db

# Tabelas a truncar entre testes (exceto foods — populada por seed)
_TRUNCATE_TABLES = (
    "meal_items, meals, weight_logs, hydration_logs, mood_logs, "
    "reminders, push_subscriptions, notifications, ai_conversations, "
    "user_profiles, users"
)


# ---------------------------------------------------------------------------
# Database lifecycle (session-scoped)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
async def setup_test_database() -> AsyncGenerator[None, None]:
    """Cria as tabelas antes dos testes e remove ao final."""
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await _engine.dispose()


# ---------------------------------------------------------------------------
# Limpeza entre testes (function-scoped)
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
async def clean_db(setup_test_database: None) -> AsyncGenerator[None, None]:
    """Trunca todas as tabelas de dados após cada teste para isolamento."""
    yield
    async with _engine.begin() as conn:
        await conn.execute(
            text(f"TRUNCATE TABLE {_TRUNCATE_TABLES} RESTART IDENTITY CASCADE")
        )


# ---------------------------------------------------------------------------
# DB session (function-scoped)
# ---------------------------------------------------------------------------


@pytest.fixture()
async def db(setup_test_database: None) -> AsyncGenerator[AsyncSession, None]:
    async with _TestSessionLocal() as session:
        yield session


# ---------------------------------------------------------------------------
# Usuário de teste
# ---------------------------------------------------------------------------


@pytest.fixture()
async def test_user(db: AsyncSession) -> User:
    user = User(
        email="teste@caloria.com",
        name="Usuário Teste",
        password_hash=hash_password("senha123"),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# HTTP clients
# ---------------------------------------------------------------------------

_transport = ASGITransport(app=app)


@pytest.fixture()
async def anon_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=_transport, base_url="http://test") as client:
        yield client


@pytest.fixture()
async def client(test_user: User) -> AsyncGenerator[AsyncClient, None]:
    token = create_access_token(test_user.id)
    async with AsyncClient(
        transport=_transport,
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as c:
        yield c
