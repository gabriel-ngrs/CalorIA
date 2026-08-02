"""Porção de gordura de passar não cai mais na regra genérica de 100 g.

Regressão do achado da bateria de invariância (2026-08-02): "1 pão francês com
manteiga" dava 880 kcal contra 212,6 kcal de "50g pão + 10g manteiga" — spread
4,14, o pior do conjunto. A IA emite `unit="porção"` para a manteiga, e não havia
regra para esse par, então valia a genérica de 100 g. Cem gramas de manteiga são
~720 kcal; ninguém come isso num pão.
"""

from __future__ import annotations

import pytest

import scripts.seed_portions as seed_portions

#: Itens de passar/temperar: a porção nunca é da ordem de 100 g.
_GORDURAS_E_PASTAS = (
    "manteiga",
    "margarina",
    "requeijao",
    "geleia",
    "cream cheese",
    "azeite",
    "oleo",
)
#: Unidades vagas que a IA emite e que caíam na regra genérica.
_UNIDADES_VAGAS = ("porcao", "unidade")


def _regras() -> dict[tuple[str, str], float]:
    return {(t, u): g for t, u, g, _mn, _mx, _p, _s in seed_portions.PORCOES}


class TestGorduraDePassar:
    @pytest.mark.parametrize("termo", _GORDURAS_E_PASTAS)
    def test_tem_regra_para_porcao(self, termo: str) -> None:
        assert (termo, "porcao") in _regras(), (
            f"{termo!r} sem regra para 'porcao' cai na genérica de 100 g"
        )

    @pytest.mark.parametrize("termo", ("manteiga", "margarina", "requeijao"))
    def test_tem_regra_para_unidade(self, termo: str) -> None:
        assert (termo, "unidade") in _regras()

    @pytest.mark.parametrize("termo", _GORDURAS_E_PASTAS)
    def test_a_porcao_e_muito_menor_que_a_generica(self, termo: str) -> None:
        """A regra genérica de 'porcao' é 100 g — absurda para item de passar."""
        assert _regras()[(termo, "porcao")] <= 25.0


class TestIntegridadeDaTabela:
    def test_nenhum_par_termo_unidade_duplicado(self) -> None:
        """`portions` tem unique (term, unit); duplicata quebra o seed inteiro."""
        pares = [(t, u) for t, u, *_ in seed_portions.PORCOES]
        assert len(pares) == len(set(pares))

    def test_as_regras_genericas_continuam_existindo(self) -> None:
        """A rede de segurança para unidade desconhecida não pode sumir."""
        regras = _regras()
        for unidade in _UNIDADES_VAGAS:
            assert ("", unidade) in regras

    def test_toda_faixa_contem_o_valor_central(self) -> None:
        for termo, unidade, gramas, gmin, gmax, *_ in seed_portions.PORCOES:
            assert gmin <= gramas <= gmax, f"faixa incoerente em {termo}/{unidade}"
