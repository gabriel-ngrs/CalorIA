"""Camada rápida do eval: snapshot de payload e cassettes (AC-15, NFR-2).

Roda a cada PR. **Zero chamadas de rede**, e falha se e somente se o payload
enviado ao provedor mudar — que é a regressão de prompt que se quer pegar de
graça, antes de gastar quota.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.config import settings
from app.prompts import get_prompt
from evals.cassettes import (
    AIClientComCassette,
    CassetteAusenteError,
    chave_do_payload,
    gravar,
    reproduzir,
)
from evals.runner import CONTEXTO_NEUTRO
from evals.schema import carregar_casos

#: `sha256` do payload renderizado de cada prompt de produção, com um contexto
#: fixo. Mudar prompt, parâmetro de amostragem ou modelo move o `sha` e quebra
#: aqui — o diff no PR mostra exatamente o quê.
SNAPSHOT_DE_PAYLOAD = {
    "meal_identify": "ee413e7a6a322f841c34e94574e1eff0408492ee4470ac26a2b1e98d640d7995",
}

_DESCRICAO_FIXA = "1 prato de arroz feijão e frango grelhado"


def payload_de_texto(nome: str, **variaveis: str) -> dict[str, object]:
    """Monta o payload que o `AIClient` enviaria — sem enviar nada."""
    prompt = get_prompt(nome)
    return {
        "model": settings.GROQ_TEXT_MODEL,
        "temperature": settings.GROQ_TEMPERATURE,
        "max_tokens": settings.GROQ_MAX_TOKENS,
        "seed": settings.GROQ_SEED,
        "prompt_ref": prompt.ref,
        "prompt_sha": prompt.sha256,
        "messages": [
            {"role": "system", "content": prompt.system},
            {"role": "user", "content": prompt.render(**variaveis)},
        ],
    }


class TestSnapshotDePayload:
    def test_payload_do_meal_identify_esta_travado(self) -> None:
        """Editar o prompt sem atualizar o snapshot faz o CI falhar."""
        payload = payload_de_texto(
            "meal_identify",
            user_context=CONTEXTO_NEUTRO,
            description=_DESCRICAO_FIXA,
        )
        assert chave_do_payload(payload) == SNAPSHOT_DE_PAYLOAD["meal_identify"]

    def test_o_payload_carrega_a_identidade_do_prompt(self) -> None:
        payload = payload_de_texto(
            "meal_identify", user_context=CONTEXTO_NEUTRO, description=_DESCRICAO_FIXA
        )
        assert payload["prompt_ref"] == "meal_identify@v1"

    def test_mudar_o_modelo_muda_o_payload(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        antes = chave_do_payload(
            payload_de_texto(
                "meal_identify",
                user_context=CONTEXTO_NEUTRO,
                description=_DESCRICAO_FIXA,
            )
        )
        monkeypatch.setattr(settings, "GROQ_TEXT_MODEL", "outro-modelo")
        depois = chave_do_payload(
            payload_de_texto(
                "meal_identify",
                user_context=CONTEXTO_NEUTRO,
                description=_DESCRICAO_FIXA,
            )
        )
        assert antes != depois

    def test_mudar_a_temperatura_muda_o_payload(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        antes = chave_do_payload(
            payload_de_texto(
                "meal_identify",
                user_context=CONTEXTO_NEUTRO,
                description=_DESCRICAO_FIXA,
            )
        )
        monkeypatch.setattr(settings, "GROQ_TEMPERATURE", 0.9)
        assert antes != chave_do_payload(
            payload_de_texto(
                "meal_identify",
                user_context=CONTEXTO_NEUTRO,
                description=_DESCRICAO_FIXA,
            )
        )


class TestCassettes:
    def test_reordenar_chaves_nao_invalida_a_gravacao(self) -> None:
        a = chave_do_payload({"model": "m", "temperature": 0.1})
        b = chave_do_payload({"temperature": 0.1, "model": "m"})
        assert a == b

    def test_grava_e_reproduz(self, tmp_path: Path) -> None:
        payload = {"model": "m", "messages": [{"role": "user", "content": "oi"}]}
        gravar(payload, "[]", diretorio=tmp_path)
        assert reproduzir(payload, diretorio=tmp_path) == "[]"

    def test_payload_diferente_nao_tem_gravacao(self, tmp_path: Path) -> None:
        """O sinal de que o prompt mudou: não existe cassette para o novo payload."""
        gravar({"model": "m", "prompt": "antes"}, "[]", diretorio=tmp_path)
        with pytest.raises(CassetteAusenteError, match="payload enviado ao provedor"):
            reproduzir({"model": "m", "prompt": "depois"}, diretorio=tmp_path)

    def test_o_cassette_guarda_o_payload_para_diff_legivel(
        self, tmp_path: Path
    ) -> None:
        payload = {"model": "m", "messages": [{"role": "user", "content": "oi"}]}
        caminho = gravar(payload, "[]", diretorio=tmp_path)
        gravado = json.loads(caminho.read_text(encoding="utf-8"))
        assert gravado["payload"] == payload

    def test_nenhum_cassette_versionado_contem_credencial(self) -> None:
        """Escopo travado: sanitizar antes de versionar."""
        from evals.cassettes import CASSETTES_DIR

        proibidos = ("gsk_", "authorization", "api_key", "apikey", "bearer ")
        for arquivo in CASSETTES_DIR.glob("*.json"):
            conteudo = arquivo.read_text(encoding="utf-8").lower()
            for termo in proibidos:
                assert termo not in conteudo, f"{arquivo.name} contém {termo!r}"


class TestAIClientComCassette:
    """O envelope que liga o cassette ao runner — sem ele, o módulo é código morto."""

    @staticmethod
    def _cliente_real() -> MagicMock:
        cliente = MagicMock()
        cliente.generate_text = AsyncMock(return_value="[resposta do provedor]")
        return cliente

    async def test_gravando_chama_o_provedor_e_grava(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("EVAL_RECORD_CASSETTES", "1")
        real = self._cliente_real()
        envelope = AIClientComCassette(real, diretorio=tmp_path)

        assert (
            await envelope.generate_text("oi", system="s") == "[resposta do provedor]"
        )
        real.generate_text.assert_awaited_once()
        assert envelope.gravou == 1
        assert list(tmp_path.glob("*.json"))

    async def test_replicando_nao_chama_o_provedor(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A garantia central: com gravação desligada, a rede não é tocada."""
        monkeypatch.setenv("EVAL_RECORD_CASSETTES", "1")
        await AIClientComCassette(
            self._cliente_real(), diretorio=tmp_path
        ).generate_text("oi", system="s")

        monkeypatch.delenv("EVAL_RECORD_CASSETTES")
        real = self._cliente_real()
        envelope = AIClientComCassette(real, diretorio=tmp_path)

        assert (
            await envelope.generate_text("oi", system="s") == "[resposta do provedor]"
        )
        real.generate_text.assert_not_awaited()
        assert envelope.reproduziu == 1

    async def test_prompt_alterado_sem_regravar_estoura(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A regressão de prompt que o cassette existe para pegar."""
        monkeypatch.setenv("EVAL_RECORD_CASSETTES", "1")
        await AIClientComCassette(
            self._cliente_real(), diretorio=tmp_path
        ).generate_text("oi", system="prompt antigo")

        monkeypatch.delenv("EVAL_RECORD_CASSETTES")
        envelope = AIClientComCassette(self._cliente_real(), diretorio=tmp_path)
        with pytest.raises(CassetteAusenteError, match="payload enviado ao provedor"):
            await envelope.generate_text("oi", system="prompt novo")

    def test_metodos_nao_envolvidos_vao_ao_cliente_real(self, tmp_path: Path) -> None:
        real = MagicMock()
        real.generate_with_image = "sentinela"
        envelope = AIClientComCassette(real, diretorio=tmp_path)
        assert envelope.generate_with_image == "sentinela"


class TestCamadaRapidaNaoTocaARede:
    def test_o_dataset_carrega_sem_banco_e_sem_rede(self) -> None:
        assert carregar_casos()

    def test_montar_payload_nao_instancia_cliente_de_rede(self) -> None:
        """Se isto exigisse `AIClient`, a camada rápida deixaria de ser rápida."""
        payload = payload_de_texto(
            "meal_identify", user_context="ctx", description="arroz"
        )
        assert payload["messages"]
