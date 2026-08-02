"""Registry de prompts versionados (AC-10).

O teste de `sha256` é o gate de imutabilidade: editar o texto de uma versão
existente sem criar uma versão nova quebra esta suíte. É o mesmo contrato de uma
migration Alembic já aplicada.
"""

from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.prompts import (
    PromptNotFoundError,
    PromptRegistry,
    PromptVersion,
    get_prompt,
)
from app.services.ai.ai_client import AIClient

#: `sha256` das versões ativas. Atualizar SOMENTE junto de um bump de versão —
#: a lista existe justamente para que editar um prompt no lugar quebre a suíte.
#: Medido em 2026-08-02: as quatro na extração da C.1; `vision_identify` movida
#: para v2 na fase B.5, que removeu do prompt de visão as duas regras que foram
#: a causa raiz do bug 001.
SHA_TRAVADO = {
    "meal_fallback": "713ea1c529306cc18bc2a40b17e935209489af9c7edb2b8cd8650d0cf85b5fc0",
    "meal_identify": "f1334ef6072f8ef9aa6973346f21bb94650292128e96fe53bbbc261a133b632e",
    "vision_fallback": "7c206344f4f87a7ac01ea3a0cfae610a1923a56e92923ad63b713f87e1d01b78",
    "vision_identify": "0362121d603603b7d662fbd9b6118d06b66ba6658c5d8f817e9e55e7cd7ac3ae",
}


@pytest.fixture()
def registry_temporario(tmp_path: Path) -> PromptRegistry:
    """Registry isolado em disco, para exercitar resolução de versão."""
    (tmp_path / "exemplo").mkdir()
    (tmp_path / "exemplo" / "v1.txt").write_text("primeira", encoding="utf-8")
    (tmp_path / "exemplo" / "v2.txt").write_text("segunda", encoding="utf-8")
    (tmp_path / "exemplo" / "v2.user.txt").write_text("olá {nome}", encoding="utf-8")
    (tmp_path / "so_v1").mkdir()
    (tmp_path / "so_v1" / "v1.txt").write_text("única", encoding="utf-8")
    return PromptRegistry(root=tmp_path)


class TestResolucaoDeVersao:
    def test_sem_versao_resolve_a_maior(
        self, registry_temporario: PromptRegistry
    ) -> None:
        assert registry_temporario.get("exemplo").version == 2

    def test_versao_explicita_e_respeitada(
        self, registry_temporario: PromptRegistry
    ) -> None:
        assert registry_temporario.get("exemplo", 1).system == "primeira"

    def test_lista_versoes_em_ordem_crescente(
        self, registry_temporario: PromptRegistry
    ) -> None:
        assert registry_temporario.versions("exemplo") == [1, 2]

    def test_nome_desconhecido_estoura(
        self, registry_temporario: PromptRegistry
    ) -> None:
        with pytest.raises(PromptNotFoundError, match="desconhecido"):
            registry_temporario.get("nao_existe")

    def test_versao_inexistente_estoura(
        self, registry_temporario: PromptRegistry
    ) -> None:
        with pytest.raises(PromptNotFoundError, match="v9"):
            registry_temporario.get("exemplo", 9)

    def test_ref_identifica_nome_e_versao(
        self, registry_temporario: PromptRegistry
    ) -> None:
        assert registry_temporario.get("exemplo").ref == "exemplo@v2"


class TestUserTemplate:
    def test_render_substitui_variaveis(
        self, registry_temporario: PromptRegistry
    ) -> None:
        assert (
            registry_temporario.get("exemplo").render(nome="Gabriel") == "olá Gabriel"
        )

    def test_prompt_sem_template_recusa_render(
        self, registry_temporario: PromptRegistry
    ) -> None:
        with pytest.raises(ValueError, match="user message"):
            registry_temporario.get("so_v1").render()


class TestShaDoTemplate:
    def test_sha_muda_quando_o_conteudo_muda(self, tmp_path: Path) -> None:
        (tmp_path / "p").mkdir()
        arquivo = tmp_path / "p" / "v1.txt"
        arquivo.write_text("antes", encoding="utf-8")
        registry = PromptRegistry(root=tmp_path)
        sha_antes = registry.get("p").sha256

        arquivo.write_text("depois", encoding="utf-8")
        assert PromptRegistry(root=tmp_path).get("p").sha256 != sha_antes

    def test_sha_cobre_tambem_o_template_de_user(self, tmp_path: Path) -> None:
        """Mudar só a user message tem de mover o `sha` da versão."""
        (tmp_path / "p").mkdir()
        (tmp_path / "p" / "v1.txt").write_text("system", encoding="utf-8")
        user = tmp_path / "p" / "v1.user.txt"
        user.write_text("antes", encoding="utf-8")
        sha_antes = PromptRegistry(root=tmp_path).get("p").sha256

        user.write_text("depois", encoding="utf-8")
        assert PromptRegistry(root=tmp_path).get("p").sha256 != sha_antes


class TestPromptsDeProducao:
    def test_os_quatro_prompts_estao_registrados(self) -> None:
        assert set(PromptRegistry().names()) == set(SHA_TRAVADO)

    @pytest.mark.parametrize("nome", sorted(SHA_TRAVADO))
    def test_sha_da_versao_ativa_esta_travado(self, nome: str) -> None:
        """Editar o texto sem bump de versão quebra aqui — por desenho."""
        assert get_prompt(nome).sha256 == SHA_TRAVADO[nome]

    @pytest.mark.parametrize("nome", ["meal_identify", "vision_identify"])
    def test_prompts_de_identificacao_tem_template_de_user(self, nome: str) -> None:
        assert get_prompt(nome).user_template is not None

    @pytest.mark.parametrize("nome", ["meal_fallback", "vision_fallback"])
    def test_prompts_de_fallback_nao_tem_template_de_user(self, nome: str) -> None:
        assert get_prompt(nome).user_template is None

    def test_meal_identify_renderiza_as_duas_variaveis(self) -> None:
        renderizado = get_prompt("meal_identify").render(
            user_context="ctx", description="arroz"
        )
        assert "ctx" in renderizado
        assert "arroz" in renderizado
        assert "{" not in renderizado

    def test_vision_identify_renderiza_o_contexto(self) -> None:
        renderizado = get_prompt("vision_identify").render(user_context="ctx")
        assert "ctx" in renderizado
        assert "{" not in renderizado

    @pytest.mark.parametrize(
        ("nome", "versao"),
        [
            ("meal_identify", 1),
            ("meal_fallback", 1),
            ("vision_fallback", 1),
            ("vision_identify", 2),
        ],
    )
    def test_versao_ativa_esperada(self, nome: str, versao: int) -> None:
        assert get_prompt(nome).version == versao

    def test_v1_de_vision_identify_continua_intacta(self) -> None:
        """Imutabilidade: a v2 nasceu ao lado da v1, não por cima dela."""
        assert PromptRegistry().get("vision_identify", 1).sha256 == (
            "570e5fc7179932bfda20e2b8f008db1bbf6305a321a9b9a600db021d55bde200"
        )

    def test_a_v2_de_visao_removeu_as_regras_do_bug_001(self) -> None:
        v2 = PromptRegistry().get("vision_identify", 2).system
        assert "Liste cada alimento separadamente" not in v2
        assert "Estime porções sempre em gramas" not in v2
        assert "PRATO CONHECIDO VEM INTEIRO" in v2

    def test_prompt_version_e_imutavel(self) -> None:
        prompt = get_prompt("meal_identify")
        assert isinstance(prompt, PromptVersion)
        with pytest.raises(AttributeError):
            prompt.system = "outro"  # type: ignore[misc]


class TestIdentidadeNoLogDoAIClient:
    """AC-10: cada chamada registra `prompt_name`, `prompt_version` e `prompt_sha`."""

    @staticmethod
    def _resposta_groq() -> MagicMock:
        resposta = MagicMock()
        resposta.choices = [MagicMock(message=MagicMock(content="[]"))]
        resposta.usage = MagicMock(prompt_tokens=11, completion_tokens=22)
        return resposta

    async def test_log_traz_nome_versao_e_sha(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        client = AIClient()
        client._groq = MagicMock()  # type: ignore[assignment]
        client._groq.chat.completions.create = AsyncMock(
            return_value=self._resposta_groq()
        )
        prompt = get_prompt("meal_identify")

        with caplog.at_level(logging.INFO, logger="app.services.ai.ai_client"):
            await client.generate_text("oi", use_cache=False, prompt_ref=prompt)

        linha = caplog.text
        assert "prompt_name=meal_identify" in linha
        assert "prompt_version=v1" in linha
        assert f"prompt_sha={prompt.sha256[:16]}" in linha

    async def test_sem_prompt_ref_o_log_nao_quebra(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        client = AIClient()
        client._groq = MagicMock()  # type: ignore[assignment]
        client._groq.chat.completions.create = AsyncMock(
            return_value=self._resposta_groq()
        )

        with caplog.at_level(logging.INFO, logger="app.services.ai.ai_client"):
            await client.generate_text("oi", use_cache=False)

        assert "prompt_name=-" in caplog.text


class TestPromptsUsadosPelosParsers:
    """Os parsers têm de apontar para as versões do registry, não para literais."""

    def test_meal_parser_usa_o_registry(self) -> None:
        from app.services.ai import meal_parser

        assert meal_parser._IDENTIFY_PROMPT.sha256 == SHA_TRAVADO["meal_identify"]
        assert meal_parser._FALLBACK_PROMPT.sha256 == SHA_TRAVADO["meal_fallback"]

    def test_vision_parser_usa_o_registry(self) -> None:
        from app.services.ai import vision_parser

        assert vision_parser._IDENTIFY_PROMPT.sha256 == SHA_TRAVADO["vision_identify"]
        assert vision_parser._FALLBACK_PROMPT.sha256 == SHA_TRAVADO["vision_fallback"]
