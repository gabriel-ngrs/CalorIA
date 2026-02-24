from __future__ import annotations

import time

import pytest
from jose import JWTError, jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestHashPassword:
    def test_retorna_hash_diferente_da_senha(self) -> None:
        h = hash_password("minha_senha")
        assert h != "minha_senha"

    def test_hash_bcrypt_comeca_com_prefixo(self) -> None:
        h = hash_password("abc")
        assert h.startswith("$2b$") or h.startswith("$2a$")

    def test_hashes_distintos_para_mesma_senha(self) -> None:
        h1 = hash_password("senha")
        h2 = hash_password("senha")
        assert h1 != h2


class TestVerifyPassword:
    def test_senha_correta_retorna_true(self) -> None:
        h = hash_password("correta")
        assert verify_password("correta", h) is True

    def test_senha_errada_retorna_false(self) -> None:
        h = hash_password("correta")
        assert verify_password("errada", h) is False

    def test_senha_vazia_retorna_false(self) -> None:
        h = hash_password("algo")
        assert verify_password("", h) is False


class TestCreateAccessToken:
    def test_token_decodifica_com_subject_correto(self) -> None:
        token = create_access_token(42)
        payload = decode_token(token)
        assert payload["sub"] == "42"
        assert payload["type"] == "access"

    def test_subject_string_e_preservado(self) -> None:
        token = create_access_token("user@email.com")
        payload = decode_token(token)
        assert payload["sub"] == "user@email.com"

    def test_token_tem_expiracao(self) -> None:
        token = create_access_token(1)
        payload = decode_token(token)
        assert "exp" in payload
        # expira no futuro
        assert payload["exp"] > time.time()


class TestCreateRefreshToken:
    def test_tipo_e_refresh(self) -> None:
        token = create_refresh_token(7)
        payload = decode_token(token)
        assert payload["type"] == "refresh"

    def test_expiracao_maior_que_access(self) -> None:
        access = create_access_token(1)
        refresh = create_refresh_token(1)
        exp_access = decode_token(access)["exp"]
        exp_refresh = decode_token(refresh)["exp"]
        assert exp_refresh > exp_access


class TestDecodeToken:
    def test_token_invalido_levanta_excecao(self) -> None:
        with pytest.raises(JWTError):
            decode_token("nao.e.um.jwt")

    def test_token_adulterado_levanta_excecao(self) -> None:
        token = create_access_token(1)
        partes = token.split(".")
        partes[2] = "assinatura_falsa"
        with pytest.raises(JWTError):
            decode_token(".".join(partes))

    def test_token_expirado_levanta_excecao(self) -> None:
        from datetime import datetime, timedelta, timezone

        expired_payload = {
            "sub": "1",
            "type": "access",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        }
        token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        with pytest.raises(JWTError):
            decode_token(token)
