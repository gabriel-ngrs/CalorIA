from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncGenerator, Iterator
from pathlib import Path
from unittest import mock

import pytest
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from alembic import command
from app.core.deps import get_db
from app.core.rate_limit import limiter
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import User  # noqa: F401 — registra todos os modelos no metadata


@pytest.fixture(autouse=True)
def rate_limiter_desligado() -> Iterator[None]:
    """Desliga o rate limiting por padrão e zera a contagem entre testes.

    O limitador conta por IP e o cliente ASGI de teste é sempre o mesmo IP, de
    modo que uma suíte com vários logins estouraria o limite por acúmulo entre
    testes independentes. Quem exercita o 429 religa o limitador explicitamente
    (`rate_limiter_ligado`).
    """
    limiter.reset()
    limiter.enabled = False
    yield
    limiter.enabled = False
    limiter.reset()


@pytest.fixture()
def rate_limiter_ligado(rate_limiter_desligado: None) -> Iterator[None]:
    """Religa o rate limiting para o teste que precisa observar o 429."""
    limiter.enabled = True
    yield
    limiter.enabled = False


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


async def _reset_schema() -> None:
    """Recria o schema aplicando as MIGRATIONS, não `Base.metadata`.

    `create_all` cria só as tabelas do metadata. Tudo que uma migration
    acrescenta além disso — extensões `pg_trgm`/`unaccent`, a função
    `caloria_unaccent`, os índices GIN de trigrama — ficava de fora, e o
    `food_lookup` estourava com `function caloria_unaccent(text) does not
    exist`. O efeito colateral era o gate da NFR-6 (`test_golden_set.py`)
    pular sempre, inclusive no CI: um gate que só pula não é gate.

    Aplicar migrations também faz o schema de teste ser o MESMO de produção,
    então uma migration quebrada passa a falhar aqui em vez de no deploy.
    """
    # `DROP SCHEMA ... CASCADE` em vez de `drop_all`: leva junto os tipos ENUM
    # e a função `caloria_unaccent`, que `drop_all` deixa para trás e fariam o
    # `CREATE TYPE`/`CREATE FUNCTION` das migrations falhar na segunda execução.
    async with _engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
    await asyncio.to_thread(_alembic_upgrade_head)


def _alembic_upgrade_head() -> None:
    """Roda `alembic upgrade head` contra o banco de TESTE.

    Síncrono por natureza (o Alembic abre a própria conexão), por isso vai para
    uma thread — o event loop de sessão não pode ser bloqueado.

    `alembic/env.py:21` sobrescreve `sqlalchemy.url` com `settings.DATABASE_URL`,
    então passar a URL pelo `Config` não basta: é preciso apontar a settings
    para o banco de teste durante o upgrade, e restaurar depois.
    """
    from app.core.config import settings

    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    url_original = settings.DATABASE_URL
    settings.DATABASE_URL = TEST_DATABASE_URL
    try:
        # `alembic/env.py:23-24` chama `fileConfig(...)`, que reconfigura o
        # logging do processo e **desabilita os loggers existentes**. O `caplog`
        # do pytest parava de capturar as linhas de `app.*`, e três testes de
        # log falhavam só quando a suíte rodava inteira — silenciosamente, por
        # ordem de execução. O upgrade não precisa configurar logging.
        #
        # O patch é em `logging.config.fileConfig`, e não em `alembic.env`: o
        # `env.py` é carregado dinamicamente pelo Alembic a cada upgrade e faz
        # `from logging.config import fileConfig` no topo, então pega a versão
        # já substituída.
        with mock.patch("logging.config.fileConfig"):
            command.upgrade(config, "head")
    finally:
        settings.DATABASE_URL = url_original


@pytest.fixture(scope="session", autouse=True)
async def setup_test_database() -> AsyncGenerator[None, None]:
    """Recria o schema no início da sessão e o remove ao final.

    Autouse + session-scoped garante que as tabelas existam antes do primeiro
    teste deste diretório, independentemente da ordem de coleta — assim o
    TRUNCATE de `clean_db` nunca encontra o schema ausente no teardown.

    O engine async é loop-bound, por isso setup, TRUNCATE e teardown usam o
    mesmo `_engine` dentro do event loop de sessão configurado em
    `asyncio_default_fixture_loop_scope`/`asyncio_default_test_loop_scope`.
    Nada de I/O acontece no import do módulo: uma seleção só-unit sobrepõe
    esta fixture (e `clean_db`) em `tests/unit/conftest.py` e roda sem banco.
    """
    await _reset_schema()
    try:
        yield
    finally:
        try:
            async with _engine.begin() as conn:
                await conn.execute(text("DROP SCHEMA public CASCADE"))
                await conn.execute(text("CREATE SCHEMA public"))
        finally:
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
