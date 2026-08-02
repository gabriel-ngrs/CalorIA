"""Fail-fast de `SECRET_KEY` fora de desenvolvimento (AC-7)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import INSECURE_SECRET_KEY, MIN_SECRET_KEY_LENGTH, Settings

_CHAVE_FORTE = "x" * MIN_SECRET_KEY_LENGTH


def _settings(**overrides: str) -> Settings:
    """Constrói Settings ignorando `.env` e o ambiente do processo."""
    return Settings(_env_file=None, **overrides)  # type: ignore[call-arg]


class TestSecretKeyEmDesenvolvimento:
    def test_default_inseguro_e_aceito(self) -> None:
        cfg = _settings(APP_ENV="development", SECRET_KEY=INSECURE_SECRET_KEY)
        assert cfg.SECRET_KEY == INSECURE_SECRET_KEY

    def test_chave_curta_e_aceita(self) -> None:
        cfg = _settings(APP_ENV="development", SECRET_KEY="curta")
        assert cfg.SECRET_KEY == "curta"


class TestSecretKeyForaDeDesenvolvimento:
    @pytest.mark.parametrize("ambiente", ["production", "staging", "test"])
    def test_default_inseguro_aborta(self, ambiente: str) -> None:
        with pytest.raises(ValidationError, match="default inseguro"):
            _settings(APP_ENV=ambiente, SECRET_KEY=INSECURE_SECRET_KEY)

    def test_chave_curta_aborta(self) -> None:
        with pytest.raises(ValidationError, match="caracteres"):
            _settings(
                APP_ENV="production", SECRET_KEY="x" * (MIN_SECRET_KEY_LENGTH - 1)
            )

    def test_chave_propria_com_tamanho_minimo_sobe(self) -> None:
        cfg = _settings(APP_ENV="production", SECRET_KEY=_CHAVE_FORTE)
        assert cfg.SECRET_KEY == _CHAVE_FORTE

    def test_mensagem_de_erro_nomeia_o_ambiente(self) -> None:
        with pytest.raises(ValidationError, match="APP_ENV=production"):
            _settings(APP_ENV="production", SECRET_KEY=INSECURE_SECRET_KEY)
