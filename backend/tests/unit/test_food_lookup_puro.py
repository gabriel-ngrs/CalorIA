"""Funções puras do `food_lookup` — normalização, limpeza de consulta, n-gramas.

Estas três funções decidem **o que** vai para o banco. Erros aqui não aparecem
como exceção: aparecem como o alimento errado no diário, silenciosamente.

Os casos vêm da instrumentação real do pipeline (bug 001), não de invenção:
cada um reproduz uma consulta que o Estágio 1 de fato emitiu.
"""

from __future__ import annotations

import pytest

from app.services.ai.food_lookup import (
    _extract_candidates,
    _normalize,
    preparo_relevante,
)


class TestNormalize:
    @pytest.mark.parametrize(
        ("entrada", "esperado"),
        [
            ("Feijão", "feijao"),
            ("PÃO FRANCÊS", "pao frances"),
            ("Açúcar Mascavo", "acucar mascavo"),
            ("  Maçã  ", "maca"),
            ("Óleo de soja", "oleo de soja"),
            ("", ""),
        ],
    )
    def test_remove_acento_e_minusculas(self, entrada: str, esperado: str) -> None:
        assert _normalize(entrada) == esperado


class TestPreparoRelevante:
    @pytest.mark.parametrize(
        "preparo",
        ["grelhado", "frito", "cozido", "assado", "refogado", "empanado", "cru"],
    )
    def test_preparo_real_e_mantido(self, preparo: str) -> None:
        """Grelhado ≠ frito importa: o preparo muda o alimento no banco."""
        assert preparo_relevante(preparo) == preparo

    @pytest.mark.parametrize(
        "vazio",
        [
            "não aplicável",
            "NÃO APLICÁVEL",
            "nao aplicavel",
            "n/a",
            "nenhum",
            "natural",
            "in natura",
            "sem preparo",
            "indefinido",
            "-",
            "",
            None,
        ],
    )
    def test_preparo_vazio_e_descartado(self, vazio: str | None) -> None:
        """Concatenado à consulta, vira ruído trigrama e derruba o score.

        Medido: `"azeite não aplicável"` pontua 0,6364 (abaixo do limiar 0,65)
        enquanto `"azeite"` pontua 1,00 — o preparo vazio custava o match.
        """
        assert preparo_relevante(vazio) is None


class TestExtractCandidates:
    def test_palavra_unica_gera_ela_mesma(self) -> None:
        assert _extract_candidates("azeite", min_n=1) == ["azeite"]

    def test_gera_ngramas_de_2_a_4_palavras(self) -> None:
        c = _extract_candidates("arroz branco cozido", min_n=2)
        assert "arroz branco" in c
        assert "branco cozido" in c
        assert "arroz branco cozido" in c

    def test_descarta_fragmento_que_comeca_em_stopword(self) -> None:
        """`"manteiga derivado do leite"` gerava `"do leite"`, que casava com o
        alimento `Leite` (26,8 kcal/100g) acima do limiar — manteiga virava
        leite, erro de 27×."""
        c = _extract_candidates("manteiga derivado do leite", min_n=2)
        assert "do leite" not in c
        assert not any(frag.startswith("do ") for frag in c)

    def test_descarta_fragmento_que_termina_em_stopword(self) -> None:
        c = _extract_candidates("peito de frango com osso", min_n=2)
        assert not any(frag.endswith(" com") for frag in c)
        assert not any(frag.endswith(" de") for frag in c)

    def test_mantem_o_nome_completo_mesmo_com_stopword_no_meio(self) -> None:
        """A preposição interna é parte do nome: "peito de frango" é um alimento."""
        c = _extract_candidates("peito de frango grelhado", min_n=2)
        assert "peito de frango" in c
        assert "peito de frango grelhado" in c

    def test_deduplica_mantendo_ordem(self) -> None:
        c = _extract_candidates("arroz arroz arroz", min_n=2)
        assert len(c) == len(set(c))

    def test_descarta_fragmento_curto_demais(self) -> None:
        assert all(len(frag) >= 3 for frag in _extract_candidates("pa ao", min_n=1))

    def test_remove_pontuacao(self) -> None:
        c = _extract_candidates("arroz, feijao; frango", min_n=2)
        assert not any("," in frag or ";" in frag for frag in c)

    def test_texto_vazio_nao_gera_candidato(self) -> None:
        assert _extract_candidates("", min_n=1) == []

    def test_descricao_longa_nao_explode(self) -> None:
        """O array de candidatos vai inteiro para a query SQL.

        Uma descrição no limite do schema (2000 caracteres) não pode gerar um
        array grande a ponto de custar caro no banco.
        """
        texto = " ".join(["alimento"] * 250)  # ~2000 caracteres
        c = _extract_candidates(texto, min_n=2)
        # A deduplicação segura o crescimento: palavras repetidas colapsam.
        assert len(c) <= 50, f"{len(c)} candidatos para uma descrição repetitiva"

    def test_descricao_longa_variada_fica_limitada(self) -> None:
        texto = " ".join(f"item{i}" for i in range(250))
        c = _extract_candidates(texto, min_n=2)
        # 250 palavras × 3 tamanhos de janela ≈ 750 no pior caso.
        assert len(c) < 1000
