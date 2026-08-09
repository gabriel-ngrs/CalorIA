"""Configurações específicas para testes unitários.

Sobrepõe as fixtures autouse do conftest raiz que dependem de banco de dados
real, permitindo que testes unitários rodem sem infraestrutura Docker.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_test_database() -> Iterator[None]:
    """Substitui a criação/remoção do schema — testes unitários usam mocks."""
    yield


@pytest.fixture(autouse=True)
def clean_db() -> Iterator[None]:
    """Substitui o TRUNCATE entre testes — nada é escrito no banco aqui."""
    yield
