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
from evals.runner import (
    CONTEXTO_NEUTRO,
    ContadorDeUso,
    ResultadoCaso,
    montar_relatorio,
    repeticoes_efetivas,
    resumo_do_custo,
)
from evals.schema import carregar_casos

#: `sha256` do payload renderizado de **cada um dos quatro** prompts de
#: produção, com um contexto fixo. Mudar prompt, parâmetro de amostragem ou
#: modelo move o `sha` e quebra aqui — o diff no PR mostra exatamente o quê.
#:
#: O teste de `sha` do registry (C.1) pega mudança de *texto de prompt*; este
#: pega mudança de qualquer coisa que vá no envelope — modelo, `temperature`,
#: `max_tokens`, `seed`, formato da mensagem. São defeitos diferentes.
# Regravado em 2026-08-17: a Groq aposentou `llama-3.3-70b-versatile` e o teto de
# tokens caiu de 8192 para 2048 (o free tier reserva `max_tokens` contra o limite
# de 8000 TPM). Os quatro hashes mudaram só por isso — verificado restaurando os
# dois valores antigos, que reproduzem exatamente os hashes anteriores. Nenhum
# texto de prompt foi tocado, e por isso nenhuma versão de prompt foi promovida.
SNAPSHOT_DE_PAYLOAD = {
    "meal_identify": "b5a56fb93828e644942b6523aca8e496b92007a05dde55da80733352f235807d",
    "meal_fallback": "81c497754be294253e71579025b22f201cd83d4a337dd4aa87828e279c25b62c",
    "vision_identify": "6a4e8f3dba70f67877d5a156511554f6730efb9e8a839c3a46db9ac8c040fea6",
    "vision_fallback": "d454ff29b18e220842c9922578e999d6ded5288cdc646f80178337736d310ea1",
}

_DESCRICAO_FIXA = "1 prato de arroz feijão e frango grelhado"

#: Os dois `*_fallback` não têm template de user message — quem monta é o
#: parser. Este texto espelha o formato que ele envia (`meal_parser.py:310-313`).
_PEDIDO_DE_MACROS = (
    "Calcule os macronutrientes para os alimentos abaixo:\n"
    '[{"food_name": "arroz", "quantity": 150.0, "unit": "g", "preparation": null}]'
)

#: Prompts que saem pelo modelo de visão, e não pelo de texto.
_PROMPTS_DE_VISAO = frozenset({"vision_identify", "vision_fallback"})


def payload_de_texto(
    nome: str,
    *,
    user_msg: str | None = None,
    modelo: str | None = None,
    **variaveis: str,
) -> dict[str, object]:
    """Monta o payload que o `AIClient` enviaria — sem enviar nada."""
    prompt = get_prompt(nome)
    return {
        "model": modelo or settings.GROQ_TEXT_MODEL,
        "temperature": settings.GROQ_TEMPERATURE,
        "max_tokens": settings.GROQ_MAX_TOKENS,
        "seed": settings.GROQ_SEED,
        "prompt_ref": prompt.ref,
        "prompt_sha": prompt.sha256,
        "messages": [
            {"role": "system", "content": prompt.system},
            {
                "role": "user",
                "content": user_msg
                if user_msg is not None
                else prompt.render(**variaveis),
            },
        ],
    }


def payload_do_prompt(nome: str) -> dict[str, object]:
    """Payload de qualquer um dos quatro prompts, com entrada fixa."""
    modelo = settings.GROQ_VISION_MODEL if nome in _PROMPTS_DE_VISAO else None
    if nome == "meal_identify":
        return payload_de_texto(
            nome,
            modelo=modelo,
            user_context=CONTEXTO_NEUTRO,
            description=_DESCRICAO_FIXA,
        )
    if nome == "vision_identify":
        return payload_de_texto(nome, modelo=modelo, user_context=CONTEXTO_NEUTRO)
    return payload_de_texto(nome, modelo=modelo, user_msg=_PEDIDO_DE_MACROS)


class TestSnapshotDePayload:
    @pytest.mark.parametrize("nome", sorted(SNAPSHOT_DE_PAYLOAD))
    def test_payload_do_prompt_esta_travado(self, nome: str) -> None:
        """Editar o prompt sem atualizar o snapshot faz o CI falhar."""
        assert chave_do_payload(payload_do_prompt(nome)) == SNAPSHOT_DE_PAYLOAD[nome]

    def test_o_snapshot_cobre_todos_os_prompts_de_producao(self) -> None:
        """Prompt novo sem snapshot passaria despercebido — este teste impede."""
        from app.prompts import PromptRegistry

        assert set(SNAPSHOT_DE_PAYLOAD) == set(PromptRegistry().names())

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


class TestRepeticoesEmReplay:
    """C5-IMP-1: repetir em replay mede o disco, não o modelo."""

    def test_replay_reduz_repeticoes_a_uma(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("EVAL_RECORD_CASSETTES", raising=False)
        assert repeticoes_efetivas(3, usar_cassettes=True) == 1

    def test_gravando_preserva_as_repeticoes(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Com gravação ligada o provedor é chamado a cada repetição."""
        monkeypatch.setenv("EVAL_RECORD_CASSETTES", "1")
        assert repeticoes_efetivas(3, usar_cassettes=True) == 3

    def test_sem_cassettes_preserva_as_repeticoes(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("EVAL_RECORD_CASSETTES", raising=False)
        assert repeticoes_efetivas(3, usar_cassettes=False) == 3

    def test_uma_repeticao_nunca_e_alterada(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("EVAL_RECORD_CASSETTES", raising=False)
        assert repeticoes_efetivas(1, usar_cassettes=True) == 1


class TestOrigemDaLatencia:
    """A latência entra na mesma série append-only vinda de duas origens."""

    @staticmethod
    def _resultado(segundos: float) -> ResultadoCaso:
        return ResultadoCaso(
            id="c1",
            estrato="simples",
            descricao="arroz",
            referencia_kcal=100.0,
            previsto_kcal=100.0,
            ape=0.0,
            segundos=segundos,
        )

    def test_a_latencia_declara_a_origem_do_custo(self) -> None:
        """Sem isso, 0,07 s de disco e 2,4 s de rede se comparam como se fossem o mesmo."""
        relatorio = montar_relatorio(
            carregar_casos(),
            [self._resultado(0.058)],
            custo=resumo_do_custo(ContadorDeUso(), origem="replay"),
        )
        assert relatorio["latencia"]["origem"] == "replay"
        assert relatorio["custo"]["origem"] == "replay"

    def test_execucao_sem_custo_medido_nao_finge_origem(self) -> None:
        relatorio = montar_relatorio(carregar_casos(), [self._resultado(2.4)])
        assert relatorio["latencia"]["origem"] == "nao medido"

    def test_execucao_vazia_ainda_declara_a_origem(self) -> None:
        relatorio = montar_relatorio(
            carregar_casos(),
            [],
            custo=resumo_do_custo(ContadorDeUso(), origem="provedor"),
        )
        assert relatorio["latencia"] == {
            "n": 0,
            "mediana_s": None,
            "total_s": None,
            "origem": "provedor",
        }
