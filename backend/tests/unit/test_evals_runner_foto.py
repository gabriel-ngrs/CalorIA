"""Estrato de foto no runner do eval (fase B.5, passo 5).

O runner nasceu na C.5 medindo só os estratos de texto, com o caminho de foto
explicitamente adiado para esta fase. Aqui ele passa a executar o caso de foto
pelo `VisionParser` de produção — sem o que o gate da B.5 ("delta do estrato de
foto, antes e depois") não é medível.

Zero rede: os parsers são substituídos por dublês.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pytest

from app.prompts import get_prompt
from app.schemas.ai import ParsedFoodItem
from app.services.ai import vision_parser as vision_parser_mod
from app.services.ai.food_lookup import IdentifiedFood
from evals import runner
from evals.schema import CasoEval, Estrato, carregar_casos


def _caso(estrato: Estrato, imagem_path: str | None = None) -> CasoEval:
    return CasoEval(
        id=f"caso-{estrato.value}",
        estrato=estrato,
        descricao="uma banana",
        referencia_kcal=69.0,
        fonte_referencia="TACO 4a edicao",
        fonte_url="https://www.nepa.unicamp.br/taco/",
        data_de_adicao=date(2026, 8, 3),
        imagem_path=imagem_path,
    )


def _item(calorias: float) -> ParsedFoodItem:
    return ParsedFoodItem(
        food_name="banana",
        quantity=75.0,
        calories=calorias,
        protein=1.0,
        carbs=17.0,
        fat=0.1,
        confidence=0.9,
    )


class _ParserFalso:
    """Dublê comum aos dois parsers — registra por onde a chamada entrou."""

    def __init__(self, calorias: float = 69.0) -> None:
        self.calorias = calorias
        self.chamadas: list[tuple[Any, ...]] = []

    async def _identify_foods(self, *args: Any) -> list[IdentifiedFood]:
        self.chamadas.append(args)
        return [IdentifiedFood(food_name="banana", quantity=1, unit="unidade")]

    async def _lookup_and_fill(
        self, items: list[IdentifiedFood], db: Any
    ) -> list[ParsedFoodItem]:
        return [_item(self.calorias) for _ in items]


class TestRoteamentoPorEstrato:
    """Um caso de foto é do `VisionParser`; um de texto, do `MealParser`."""

    @pytest.mark.asyncio
    async def test_caso_de_foto_entra_pelo_vision_parser_com_os_bytes_da_imagem(
        self,
    ) -> None:
        texto, foto = _ParserFalso(), _ParserFalso()
        caso = carregar_casos()[0].model_copy(
            update={
                "estrato": Estrato.FOTO,
                "imagem_path": "imagens/banana-1-unidade.jpg",
            }
        )

        await runner.identificar(caso, texto, foto)  # type: ignore[arg-type]

        assert texto.chamadas == []
        (bytes_enviados, mime, contexto) = foto.chamadas[0]
        assert bytes_enviados[:3] == b"\xff\xd8\xff"  # JPEG de verdade, não o path
        assert mime == "image/jpeg"
        assert contexto == runner.CONTEXTO_NEUTRO

    @pytest.mark.asyncio
    async def test_caso_de_texto_continua_pelo_meal_parser(self) -> None:
        texto, foto = _ParserFalso(), _ParserFalso()

        await runner.identificar(_caso(Estrato.SIMPLES), texto, foto)  # type: ignore[arg-type]

        assert foto.chamadas == []
        assert texto.chamadas[0] == ("uma banana", runner.CONTEXTO_NEUTRO)

    @pytest.mark.asyncio
    async def test_executar_caso_de_foto_produz_resultado_do_estrato_foto(self) -> None:
        foto = _ParserFalso(calorias=80.0)
        caso = carregar_casos()[0].model_copy(
            update={
                "estrato": Estrato.FOTO,
                "imagem_path": "imagens/banana-1-unidade.jpg",
                "referencia_kcal": 100.0,
            }
        )

        resultado = await runner.executar_caso(
            caso,
            _ParserFalso(),  # type: ignore[arg-type]
            db=None,
            coletor=runner.ColetorDeEstagios(),
            parser_de_foto=foto,  # type: ignore[arg-type]
        )

        assert resultado.executou
        assert resultado.estrato == "foto"
        assert resultado.previsto_kcal == 80.0
        assert resultado.ape == pytest.approx(20.0)

    @pytest.mark.asyncio
    async def test_foto_sem_parser_de_visao_vira_falha_registrada(self) -> None:
        """Nunca em silêncio: sem parser de visão o caso entra em `falhas`."""
        caso = carregar_casos()[0].model_copy(
            update={
                "estrato": Estrato.FOTO,
                "imagem_path": "imagens/banana-1-unidade.jpg",
            }
        )

        resultado = await runner.executar_caso(
            caso,
            _ParserFalso(),  # type: ignore[arg-type]
            db=None,
            coletor=runner.ColetorDeEstagios(),
        )

        assert not resultado.executou
        assert "estrato foto" in (resultado.erro or "")


class TestImagemDoCaso:
    """Um caso de foto sem imagem falha alto — não some do denominador."""

    def test_resolve_o_caminho_relativo_ao_dataset(self) -> None:
        caso = _caso(Estrato.FOTO, "imagens/banana-1-unidade.jpg")
        assert runner.imagem_do_caso(caso).is_file()

    def test_imagem_inexistente_levanta(self) -> None:
        caso = _caso(Estrato.FOTO, "imagens/nao-existe.jpg")
        with pytest.raises(FileNotFoundError, match="nao-existe"):
            runner.imagem_do_caso(caso)

    def test_caso_de_foto_sem_imagem_path_levanta(self) -> None:
        # `model_construct` pula a validação do schema de propósito: o objetivo
        # é provar que o runner também se defende, e não só o schema.
        caso = CasoEval.model_construct(id="x", estrato=Estrato.FOTO, imagem_path=None)
        with pytest.raises(ValueError, match="imagem_path"):
            runner.imagem_do_caso(caso)


class TestVersaoDeVisao:
    """Medir uma versão de prompt não pode exigir promovê-la."""

    def test_troca_a_versao_ativa_e_restaura_ao_sair(self) -> None:
        producao = vision_parser_mod._IDENTIFY_PROMPT

        with runner.versao_de_visao(1):
            assert vision_parser_mod._IDENTIFY_PROMPT.version == 1
            assert (
                vision_parser_mod._IDENTIFY_PROMPT.sha256
                == get_prompt("vision_identify", 1).sha256
            )

        assert vision_parser_mod._IDENTIFY_PROMPT is producao

    def test_restaura_mesmo_com_excecao(self) -> None:
        producao = vision_parser_mod._IDENTIFY_PROMPT
        with pytest.raises(RuntimeError), runner.versao_de_visao(1):
            raise RuntimeError("falha no meio da execução")
        assert vision_parser_mod._IDENTIFY_PROMPT is producao

    def test_sem_versao_nao_toca_o_modulo(self) -> None:
        producao = vision_parser_mod._IDENTIFY_PROMPT
        with runner.versao_de_visao(None):
            assert vision_parser_mod._IDENTIFY_PROMPT is producao


class TestProcedenciaDoPromptDeVisao:
    """O relatório precisa dizer sob qual versão de visão o número foi medido."""

    @staticmethod
    def _resultado(estrato: str) -> runner.ResultadoCaso:
        return runner.ResultadoCaso(
            id="c1",
            estrato=estrato,
            descricao="banana",
            referencia_kcal=69.0,
            previsto_kcal=69.0,
            ape=0.0,
        )

    def test_execucao_so_de_texto_nao_declara_prompt_de_visao(self) -> None:
        relatorio = runner.montar_relatorio(
            carregar_casos(), [self._resultado("simples")]
        )
        assert set(relatorio["prompts"]) == {"meal_identify", "meal_fallback"}

    def test_execucao_com_foto_declara_a_versao_de_visao_usada(self) -> None:
        with runner.versao_de_visao(1):
            relatorio = runner.montar_relatorio(
                carregar_casos(), [self._resultado("foto")]
            )
        # Sem isto, o delta v1→v2 seria registrado no histórico da C.8 com a
        # versão de produção nos dois lados — os dois pontos ficariam iguais.
        assert relatorio["prompts"]["vision_identify"]["versao"] == 1
        assert "vision_fallback" in relatorio["prompts"]


class TestDatasetDeFoto:
    def test_o_estrato_de_foto_tem_casos_executaveis(self) -> None:
        fotos = [c for c in carregar_casos() if c.estrato is Estrato.FOTO]
        assert fotos, "a C.4 populou o estrato; sem ele a B.5 volta a não ter gate"
        for caso in fotos:
            assert Path(runner.imagem_do_caso(caso)).is_file()
