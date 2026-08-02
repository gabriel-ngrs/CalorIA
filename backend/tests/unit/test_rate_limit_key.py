"""Chave de contagem do rate limiting atrás (e fora) de proxy reverso."""

from __future__ import annotations

import pytest
from starlette.requests import Request

from app.core.config import settings
from app.core.rate_limit import client_key

_IP_DO_PEER = "10.0.0.1"


def _request(forwarded_for: str | None = None) -> Request:
    headers: list[tuple[bytes, bytes]] = []
    if forwarded_for is not None:
        headers.append((b"x-forwarded-for", forwarded_for.encode()))
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/auth/login",
            "headers": headers,
            "client": (_IP_DO_PEER, 12345),
        }
    )


class TestChaveDeContagem:
    def test_sem_confianca_no_proxy_ignora_o_cabecalho(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """`X-Forwarded-For` forjado não pode render um balde novo por requisição."""
        monkeypatch.setattr(settings, "RATE_LIMIT_TRUST_FORWARDED_FOR", False)
        assert client_key(_request(forwarded_for="203.0.113.7")) == _IP_DO_PEER

    def test_com_confianca_no_proxy_usa_o_primeiro_salto(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Atrás do Caddy, o peer é o proxy; o cliente real é o primeiro salto."""
        monkeypatch.setattr(settings, "RATE_LIMIT_TRUST_FORWARDED_FOR", True)
        req = _request(forwarded_for="203.0.113.7, 10.0.0.1")
        assert client_key(req) == "203.0.113.7"

    def test_com_confianca_mas_sem_cabecalho_cai_no_peer(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "RATE_LIMIT_TRUST_FORWARDED_FOR", True)
        assert client_key(_request()) == _IP_DO_PEER

    def test_cabecalho_vazio_cai_no_peer(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(settings, "RATE_LIMIT_TRUST_FORWARDED_FOR", True)
        assert client_key(_request(forwarded_for="")) == _IP_DO_PEER
