"""Testes do normalizador determinístico de porção (bug 001, achado A).

O módulo é o que tira a conversão unidade→grama das mãos da IA. Estes testes
cobrem o vocabulário de unidades, números por extenso/fração e a marcação de
itens sem âncora determinística.
"""

from __future__ import annotations

import pytest

from app.services.nutrition.portions import (
    PortionNormalizer,
    RegraPorcao,
    canonizar_unidade,
    interpretar_quantidade,
    normalizar_texto,
)

# Subconjunto da tabela `portions` suficiente para os casos abaixo.
_REGRAS = [
    RegraPorcao("pizza", "fatia", 100.0, 80.0, 130.0, 30, "teste"),
    RegraPorcao("pizza", "unidade", 800.0, 600.0, 1000.0, 30, "teste"),
    RegraPorcao("ovo", "unidade", 50.0, 45.0, 60.0, 40, "teste"),
    RegraPorcao("arroz", "prato", 175.0, 150.0, 200.0, 30, "teste"),
    RegraPorcao("feijao", "concha", 90.0, 80.0, 100.0, 30, "teste"),
    RegraPorcao("pao frances", "unidade", 50.0, 45.0, 60.0, 40, "teste"),
    RegraPorcao("pao de forma", "fatia", 25.0, 22.0, 30.0, 40, "teste"),
    RegraPorcao("pao", "fatia", 40.0, 30.0, 55.0, 10, "teste"),
    RegraPorcao("manteiga", "colher_sopa", 10.0, 8.0, 14.0, 40, "teste"),
    RegraPorcao("banana", "unidade", 100.0, 80.0, 130.0, 40, "teste"),
    RegraPorcao("", "copo", 200.0, 150.0, 300.0, 0, "teste"),
    RegraPorcao("", "fatia", 30.0, 15.0, 120.0, 0, "teste"),
]


@pytest.fixture
def normalizer() -> PortionNormalizer:
    """Normalizador com a tabela de porções injetada (sem banco)."""
    n = PortionNormalizer(db=None)  # type: ignore[arg-type]
    n._cache = list(_REGRAS)
    return n


class TestNormalizarTexto:
    @pytest.mark.parametrize(
        ("entrada", "esperado"),
        [
            ("Feijão", "feijao"),
            ("PÃO  FRANCÊS", "pao frances"),
            ("  Açúcar ", "acucar"),
            ("", ""),
        ],
    )
    def test_remove_acento_e_normaliza_espaco(
        self, entrada: str, esperado: str
    ) -> None:
        assert normalizar_texto(entrada) == esperado


class TestCanonizarUnidade:
    @pytest.mark.parametrize(
        ("entrada", "esperado"),
        [
            ("g", "g"),
            ("gramas", "g"),
            ("GR", "g"),
            ("ml", "ml"),
            ("fatia", "fatia"),
            ("fatias", "fatia"),
            ("unidade", "unidade"),
            ("un", "unidade"),
            ("colher de sopa", "colher_sopa"),
            ("colheres de sopa", "colher_sopa"),
            ("Colher de Sopa", "colher_sopa"),
            ("prato", "prato"),
            ("concha", "concha"),
            ("copo", "copo"),
            ("scoop", "scoop"),
            ("marmita", "marmita"),
            ("quentinha", "marmita"),
        ],
    )
    def test_reconhece_grafias(self, entrada: str, esperado: str) -> None:
        assert canonizar_unidade(entrada) == esperado

    def test_unidade_desconhecida_devolve_none(self) -> None:
        # Devolver None em vez de um palpite é o ponto: o chamador marca o item.
        assert canonizar_unidade("tigela") is None
        assert canonizar_unidade("") is None

    def test_tolera_sufixo(self) -> None:
        assert canonizar_unidade("prato cheio") == "prato"
        assert canonizar_unidade("copo cheio") == "copo"


class TestInterpretarQuantidade:
    @pytest.mark.parametrize(
        ("entrada", "esperado"),
        [
            (2, 2.0),
            (2.5, 2.5),
            ("2", 2.0),
            ("2,5", 2.5),
            ("1/2", 0.5),
            ("3/4", 0.75),
            ("um", 1.0),
            ("dois", 2.0),
            ("DOIS", 2.0),
            ("três", 3.0),
            ("oito", 8.0),
            ("meia", 0.5),
            ("meio", 0.5),
            ("duzia", 12.0),
            ("meia duzia", 6.0),
        ],
    )
    def test_converte(self, entrada: object, esperado: float) -> None:
        assert interpretar_quantidade(entrada) == pytest.approx(esperado, abs=0.01)

    def test_valor_ininterpretavel(self) -> None:
        assert interpretar_quantidade("algumas") is None
        assert interpretar_quantidade(None) is None


class TestNormalizarPorcao:
    async def test_gramas_passam_direto(self, normalizer: PortionNormalizer) -> None:
        r = await normalizer.normalizar("frango grelhado", 150, "g")
        assert r.gramas == 150.0
        assert r.origem == "direta"
        assert r.confiavel

    async def test_kg_converte(self, normalizer: PortionNormalizer) -> None:
        r = await normalizer.normalizar("carne", 1.2, "kg")
        assert r.gramas == 1200.0

    async def test_ml_usa_densidade(self, normalizer: PortionNormalizer) -> None:
        r = await normalizer.normalizar("leite integral", 200, "ml")
        assert r.gramas == 200.0
        assert r.origem == "volume"

    async def test_unidade_caseira_usa_tabela(
        self, normalizer: PortionNormalizer
    ) -> None:
        r = await normalizer.normalizar("pizza de calabresa", 8, "fatia")
        assert r.gramas == 800.0
        assert r.origem == "tabela"
        assert r.confiavel

    async def test_termo_mais_especifico_vence(
        self, normalizer: PortionNormalizer
    ) -> None:
        # "pao de forma" (prio 40) deve vencer "pao" (prio 10) para "fatia"
        r = await normalizer.normalizar("pao de forma integral", 2, "fatia")
        assert r.gramas == 50.0

    async def test_numero_por_extenso(self, normalizer: PortionNormalizer) -> None:
        r = await normalizer.normalizar("ovo", "dois", "unidades")
        assert r.gramas == 100.0

    async def test_fracao(self, normalizer: PortionNormalizer) -> None:
        r = await normalizer.normalizar("banana", "meia", "unidade")
        assert r.gramas == 50.0

    async def test_regra_generica_nao_conta_como_ancora(
        self, normalizer: PortionNormalizer
    ) -> None:
        # Converte, mas a faixa é larga demais para sustentar um número calórico:
        # o item precisa chegar ao usuário marcado.
        r = await normalizer.normalizar("suco de laranja", 1, "copo")
        assert r.gramas == 200.0
        assert r.origem == "tabela"
        assert r.ancorada is False
        assert r.confiavel is False

    async def test_unidade_sem_regra_e_marcada(
        self, normalizer: PortionNormalizer
    ) -> None:
        r = await normalizer.normalizar("tacacá", 1, "tigela")
        assert r.origem == "sem_ancora"
        assert r.confiavel is False
        assert "tigela" in r.detalhe

    async def test_quantidade_invalida_nao_levanta(
        self, normalizer: PortionNormalizer
    ) -> None:
        r = await normalizer.normalizar("arroz", "algumas", "prato")
        assert r.gramas == 0.0
        assert r.confiavel is False

    async def test_faixa_plausivel_acompanha_a_quantidade(
        self, normalizer: PortionNormalizer
    ) -> None:
        r = await normalizer.normalizar("pizza", 8, "fatia")
        assert r.faixa_gramas == (640.0, 1040.0)


class TestEquivalenciaDeDescricao:
    """Invariante central do bug 001: a mesma porção, dita de formas diferentes,
    tem de normalizar para a MESMA massa."""

    @pytest.mark.parametrize(
        ("a", "b"),
        [
            # A reprodução oficial: "1 pizza grande de 8 fatias" vs "8 fatias".
            (("pizza de calabresa", 8, "fatia"), ("pizza de calabresa", 1, "unidade")),
            # Numeral contra extenso.
            (("ovo", 2, "unidade"), ("ovo", "dois", "unidades")),
            # Unidade caseira contra massa explícita.
            (("pao frances", 1, "unidade"), ("pao frances", 50, "g")),
            (("manteiga", 1, "colher de sopa"), ("manteiga", 10, "g")),
            (("arroz", 1, "prato"), ("arroz", 175, "g")),
            (("leite integral", 200, "ml"), ("leite integral", 200, "g")),
        ],
    )
    async def test_descricoes_equivalentes_dao_a_mesma_massa(
        self,
        normalizer: PortionNormalizer,
        a: tuple[str, object, str],
        b: tuple[str, object, str],
    ) -> None:
        ra = await normalizer.normalizar(*a)
        rb = await normalizer.normalizar(*b)
        assert ra.gramas == pytest.approx(rb.gramas, rel=0.001), (
            f"{a} → {ra.gramas}g diverge de {b} → {rb.gramas}g"
        )

    async def test_determinismo_da_normalizacao(
        self, normalizer: PortionNormalizer
    ) -> None:
        """A conversão é código puro: N execuções, resultado idêntico."""
        resultados = [
            (await normalizer.normalizar("pizza de calabresa", 8, "fatia")).gramas
            for _ in range(5)
        ]
        assert len(set(resultados)) == 1
