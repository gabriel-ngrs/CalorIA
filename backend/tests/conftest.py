from __future__ import annotations

import os
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
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
# DB session (function-scoped — rollback após cada teste)
# ---------------------------------------------------------------------------


@pytest.fixture()
async def db(setup_test_database: None) -> AsyncGenerator[AsyncSession, None]:
    async with _TestSessionLocal() as session:
        yield session
        await session.rollback()


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
