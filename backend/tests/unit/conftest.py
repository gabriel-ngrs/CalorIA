"""Configurações específicas para testes unitários.

Sobrepõe fixtures do conftest raiz que dependem de banco de dados real,
permitindo que testes unitários rodem sem infraestrutura Docker.
"""

from __future__ import annotations

import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_test_database() -> None:  # type: ignore[override]
    """Stub que substitui o fixture de banco de dados para testes unitários.

    Testes unitários não precisam de banco de dados real — eles usam mocks.
    """
    yield  # type: ignore[misc]
