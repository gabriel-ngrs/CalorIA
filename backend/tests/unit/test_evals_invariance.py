"""Bateria de invariância metamórfica (AC-14)."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from evals.invariance import (
    GrupoInvariancia,
    Relacao,
    avaliar_grupo,
    carregar_grupos,
    coeficiente_variacao,
    resumir,
    spread,
)
from evals.metrics import SemDadosError


def _grupo(**overrides: object) -> GrupoInvariancia:
    base: dict[str, object] = {
        "id": "g",
        "relacao": "parafrase",
        "nome": "n",
        "descricoes": ["a", "b"],
        "tolerancia_spread": 1.1,
    }
    return GrupoInvariancia.model_validate({**base, **overrides})


class TestSpread:
    def test_valores_iguais_dao_um(self) -> None:
        assert spread([100.0, 100.0]) == pytest.approx(1.0)

    def test_valor_calculado_a_mao(self) -> None:
        """A reprodução oficial do bug 001, antes da correção."""
        assert spread([3486.0, 2098.0]) == pytest.approx(3486 / 2098)

    def test_e_indiferente_a_ordem(self) -> None:
        assert spread([2098.0, 3486.0]) == spread([3486.0, 2098.0])

    def test_valor_zero_estoura(self) -> None:
        with pytest.raises(SemDadosError, match="positivos"):
            spread([0.0, 100.0])

    def test_grupo_vazio_estoura(self) -> None:
        with pytest.raises(SemDadosError, match="vazio"):
            spread([])


class TestCoeficienteVariacao:
    def test_valores_identicos_dao_zero(self) -> None:
        assert coeficiente_variacao([572.3] * 3) == pytest.approx(0.0)

    def test_valor_calculado_a_mao(self) -> None:
        # média 100, desvio amostral 10 → CV 0.1
        assert coeficiente_variacao([90.0, 100.0, 110.0]) == pytest.approx(0.1)

    def test_um_unico_valor_estoura(self) -> None:
        with pytest.raises(SemDadosError, match="ao menos 2"):
            coeficiente_variacao([1.0])


class TestAvaliacaoDeGrupo:
    def test_dentro_da_tolerancia_aprova(self) -> None:
        assert avaliar_grupo(_grupo(), [100.0, 105.0]).aprovado

    def test_fora_da_tolerancia_reprova(self) -> None:
        resultado = avaliar_grupo(_grupo(), [3486.0, 2098.0])
        assert not resultado.aprovado
        assert resultado.spread == pytest.approx(1.6615, abs=1e-4)

    def test_escala_normaliza_pelo_fator_antes_de_medir(self) -> None:
        """Dobrar a porção DEVE dobrar as kcal — o resíduo é o que se mede."""
        grupo = _grupo(relacao="escala", fator_esperado=2.0)
        assert avaliar_grupo(grupo, [100.0, 200.0]).aprovado

    def test_escala_que_nao_dobrou_reprova(self) -> None:
        grupo = _grupo(relacao="escala", fator_esperado=2.0)
        assert not avaliar_grupo(grupo, [100.0, 140.0]).aprovado

    def test_autoconsistencia_reporta_coeficiente_de_variacao(self) -> None:
        grupo = _grupo(relacao="autoconsistencia", descricoes=["x"], repeticoes=3)
        resultado = avaliar_grupo(grupo, [572.3, 572.3, 572.3])
        assert resultado.coeficiente_variacao == pytest.approx(0.0)

    def test_parafrase_nao_reporta_coeficiente_de_variacao(self) -> None:
        assert avaliar_grupo(_grupo(), [100.0, 100.0]).coeficiente_variacao is None

    def test_kcal_zero_vira_erro_e_nao_aprovacao(self) -> None:
        resultado = avaliar_grupo(_grupo(), [0.0, 100.0])
        assert not resultado.aprovado
        assert resultado.erro


class TestValidacaoDoGrupo:
    def test_escala_sem_fator_reprova(self) -> None:
        with pytest.raises(ValidationError, match="fator_esperado"):
            _grupo(relacao="escala")

    def test_autoconsistencia_com_duas_descricoes_reprova(self) -> None:
        with pytest.raises(ValidationError, match="uma descrição"):
            _grupo(relacao="autoconsistencia", repeticoes=3)

    def test_autoconsistencia_com_uma_repeticao_reprova(self) -> None:
        with pytest.raises(ValidationError, match="repeticoes"):
            _grupo(relacao="autoconsistencia", descricoes=["x"], repeticoes=1)

    def test_parafrase_com_uma_descricao_reprova(self) -> None:
        with pytest.raises(ValidationError, match="duas descrições"):
            _grupo(descricoes=["so-uma"])

    def test_tolerancia_precisa_ser_maior_que_um(self) -> None:
        with pytest.raises(ValidationError):
            _grupo(tolerancia_spread=1.0)

    def test_execucoes_repete_a_string_em_autoconsistencia(self) -> None:
        grupo = _grupo(relacao="autoconsistencia", descricoes=["x"], repeticoes=3)
        assert grupo.execucoes == ["x", "x", "x"]


class TestArquivoDeGrupos:
    def test_arquivo_versionado_valida_inteiro(self) -> None:
        assert len(carregar_grupos()) >= 12

    def test_a_reproducao_do_bug_001_e_cidada_de_primeira_classe(self) -> None:
        """O caso que dá a narrativa antes/depois não pode sumir do conjunto."""
        grupos = {g.id: g for g in carregar_grupos()}
        bug001 = grupos["inv-01-pizza-calabresa"]
        assert "8 fatias pizza calabresa" in bug001.descricoes
        assert any("pizza grande 8 fatias" in d for d in bug001.descricoes)

    def test_os_sete_pares_originais_migraram(self) -> None:
        """`instrument_meal_pipeline.py:41-88` tinha 7 pares; nenhum se perdeu."""
        ids = sorted(g.id for g in carregar_grupos())
        assert [i for i in ids if i < "inv-08"] == [
            "inv-01-pizza-calabresa",
            "inv-02-ovos-numeral-extenso",
            "inv-03-pf-vago-vs-gramas",
            "inv-04-pao-manteiga",
            "inv-05-leite-copo-ml",
            "inv-06-marmita-strogonoff",
            "inv-07-tacaca-ausente",
        ]

    def test_o_teste_de_determinismo_migrou(self) -> None:
        determinismo = next(
            g for g in carregar_grupos() if g.relacao is Relacao.AUTOCONSISTENCIA
        )
        assert determinismo.repeticoes == 3

    def test_as_cinco_relacoes_estao_representadas(self) -> None:
        presentes = {g.relacao for g in carregar_grupos()}
        assert presentes == set(Relacao)

    def test_id_duplicado_reprova(self, tmp_path: Path) -> None:
        linha = _grupo().model_dump_json()
        arquivo = tmp_path / "grupos_invariancia.jsonl"
        arquivo.write_text(f"{linha}\n{linha}\n", encoding="utf-8")
        with pytest.raises(ValueError, match="duplicado"):
            carregar_grupos(arquivo)


class TestResumo:
    def test_taxa_de_aprovacao_e_p95(self) -> None:
        resultados = [
            avaliar_grupo(_grupo(id=f"g{i}"), [100.0, 100.0 + i]) for i in range(10)
        ]
        resumo = resumir(resultados)
        assert resumo["n_grupos"] == 10
        assert 0.0 <= resumo["taxa_de_aprovacao"] <= 1.0
        assert resumo["spread_p95"] >= resumo["spread_mediano"]

    def test_reprovados_aparecem_com_os_numeros(self) -> None:
        resumo = resumir([avaliar_grupo(_grupo(), [3486.0, 2098.0])])
        assert resumo["reprovados"][0]["kcal"] == [3486.0, 2098.0]
        assert resumo["taxa_de_aprovacao"] == 0.0
