"""Métricas do eval (AC-13), validadas contra valores calculados à mão."""

from __future__ import annotations

import statistics

import pytest

from evals import metrics
from evals.metrics import SemDadosError
from evals.runner import ResultadoCaso, montar_relatorio, resumir
from evals.schema import carregar_casos


class TestApe:
    def test_valor_calculado_a_mao(self) -> None:
        # |110 - 100| / 100 = 10%
        assert metrics.ape(110.0, 100.0) == pytest.approx(10.0)

    def test_subestimar_pela_metade_da_50_por_cento(self) -> None:
        assert metrics.ape(50.0, 100.0) == pytest.approx(50.0)

    def test_superestimar_em_dobro_da_100_por_cento(self) -> None:
        assert metrics.ape(200.0, 100.0) == pytest.approx(100.0)

    def test_acerto_exato_da_zero(self) -> None:
        assert metrics.ape(100.0, 100.0) == 0.0

    def test_referencia_zero_estoura(self) -> None:
        with pytest.raises(SemDadosError):
            metrics.ape(10.0, 0.0)


class TestAssimetriaDoErroPercentual:
    """O motivo de a métrica headline ser mediana, e não média (§4 da spec)."""

    def test_dobro_e_metade_dao_o_mesmo_modulo_em_log_accuracy_ratio(self) -> None:
        dobro = metrics.log_accuracy_ratio(200.0, 100.0)
        metade = metrics.log_accuracy_ratio(50.0, 100.0)
        assert abs(dobro) == pytest.approx(abs(metade))
        assert dobro > 0 > metade

    def test_dobro_e_metade_dao_apes_diferentes(self) -> None:
        """A mesma razão de erro pune mais quando é superestimativa."""
        assert metrics.ape(200.0, 100.0) == pytest.approx(100.0)
        assert metrics.ape(50.0, 100.0) == pytest.approx(50.0)

    def test_o_mape_premia_quem_subconta(self) -> None:
        """Dois pipelines igualmente errados em razão; o que subconta ganha."""
        referencias = [100.0, 100.0, 100.0]
        subconta = [50.0, 50.0, 50.0]  # metade
        superconta = [200.0, 200.0, 200.0]  # dobro
        assert metrics.mape(subconta, referencias) < metrics.mape(
            superconta, referencias
        )

    def test_o_sspb_separa_os_dois_casos_pelo_sinal(self) -> None:
        referencias = [100.0, 100.0, 100.0]
        assert metrics.sspb([50.0] * 3, referencias) < 0
        assert metrics.sspb([200.0] * 3, referencias) > 0


class TestMdape:
    def test_mediana_de_valores_conhecidos(self) -> None:
        # APEs: 10, 20, 30 → mediana 20
        previstos = [110.0, 120.0, 130.0]
        referencias = [100.0, 100.0, 100.0]
        assert metrics.mdape(previstos, referencias) == pytest.approx(20.0)

    def test_mediana_resiste_a_um_outlier_que_a_media_nao(self) -> None:
        # APEs: 1, 2, 3, 900 → mediana 2.5, média 226.5
        previstos = [101.0, 102.0, 103.0, 1000.0]
        referencias = [100.0] * 4
        assert metrics.mdape(previstos, referencias) == pytest.approx(2.5)
        assert metrics.mape(previstos, referencias) == pytest.approx(226.5)

    def test_tamanhos_diferentes_estouram(self) -> None:
        with pytest.raises(SemDadosError, match="tamanhos diferentes"):
            metrics.mdape([1.0], [1.0, 2.0])

    def test_conjunto_vazio_estoura(self) -> None:
        with pytest.raises(SemDadosError, match="vazio"):
            metrics.mdape([], [])


class TestSspb:
    def test_sem_vies_da_zero(self) -> None:
        assert metrics.sspb([100.0, 100.0], [100.0, 100.0]) == pytest.approx(0.0)

    def test_valor_calculado_a_mao(self) -> None:
        # ln(1.2) mediano → (e^{ln 1.2} - 1) × 100 = 20%
        assert metrics.sspb([120.0, 120.0], [100.0, 100.0]) == pytest.approx(20.0)

    def test_e_simetrico_em_razao(self) -> None:
        """Errar por 2× e por ½× dá o mesmo módulo, com sinais opostos.

        É o contraste com o APE, que dá 100% e 50% para os mesmos dois casos.
        """
        acima = metrics.sspb([200.0], [100.0])
        abaixo = metrics.sspb([50.0], [100.0])
        assert acima == pytest.approx(100.0)
        assert abaixo == pytest.approx(-100.0)
        assert abs(acima) == pytest.approx(abs(abaixo))


class TestMaeEToleranciaAbsoluta:
    def test_mae_calculado_a_mao(self) -> None:
        # |10-12| + |20-19| + |30-30| = 2 + 1 + 0 → média 1.0
        assert metrics.mae([12.0, 19.0, 30.0], [10.0, 20.0, 30.0]) == pytest.approx(1.0)

    def test_tolerancia_absoluta_conta_a_fracao_dentro_da_faixa(self) -> None:
        previstos = [10.0, 14.0, 20.0, 26.0]
        referencias = [10.0, 10.0, 20.0, 20.0]
        assert metrics.acuracia_por_tolerancia_absoluta(
            previstos, referencias, tolerancia=5.0
        ) == pytest.approx(0.75)

    def test_tolerancia_absoluta_nao_pune_macro_minusculo(self) -> None:
        """Café preto: 0,1 g de referência, 0,3 g previsto = 200% e 0,2 g."""
        assert metrics.acuracia_por_tolerancia_absoluta(
            [0.3], [0.1], tolerancia=5.0
        ) == pytest.approx(1.0)
        assert metrics.ape(0.3, 0.1) == pytest.approx(200.0)

    def test_tolerancia_percentual_espelha_o_limiar_do_golden_set(self) -> None:
        previstos = [105.0, 109.0, 111.0, 130.0]
        referencias = [100.0] * 4
        assert metrics.acuracia_por_tolerancia_percentual(
            previstos, referencias, tolerancia_pct=10.0
        ) == pytest.approx(0.5)


class TestBootstrap:
    def test_conjunto_constante_da_intervalo_degenerado(self) -> None:
        intervalo = metrics.ic95_bootstrap([7.0] * 30)
        assert intervalo.inferior == pytest.approx(7.0)
        assert intervalo.superior == pytest.approx(7.0)

    def test_intervalo_contem_a_estatistica_amostral(self) -> None:
        valores = [float(v) for v in range(1, 41)]
        intervalo = metrics.ic95_bootstrap(valores, statistics.median)
        assert intervalo.inferior <= statistics.median(valores) <= intervalo.superior

    def test_e_reprodutivel_com_a_mesma_semente(self) -> None:
        """NFR-5: mesmo dado, mesmo intervalo."""
        valores = [float(v) for v in range(1, 41)]
        assert metrics.ic95_bootstrap(valores) == metrics.ic95_bootstrap(valores)

    def test_um_unico_valor_nao_estoura(self) -> None:
        intervalo = metrics.ic95_bootstrap([3.0])
        assert intervalo.inferior == intervalo.superior == 3.0

    def test_conjunto_vazio_estoura(self) -> None:
        with pytest.raises(SemDadosError, match="vazio"):
            metrics.ic95_bootstrap([])

    def test_amostra_maior_estreita_o_intervalo(self) -> None:
        pequena = [float(v) for v in range(1, 11)]
        grande = [float(v) for v in range(1, 11)] * 10
        largura_pequena = (
            metrics.ic95_bootstrap(pequena).superior
            - metrics.ic95_bootstrap(pequena).inferior
        )
        largura_grande = (
            metrics.ic95_bootstrap(grande).superior
            - metrics.ic95_bootstrap(grande).inferior
        )
        assert largura_grande < largura_pequena


def _resultado(
    id_: str, estrato: str, previsto: float, referencia: float
) -> ResultadoCaso:
    return ResultadoCaso(
        id=id_,
        estrato=estrato,
        descricao="x",
        referencia_kcal=referencia,
        previsto_kcal=previsto,
        ape=metrics.ape(previsto, referencia),
    )


class TestAgregacaoDoRunner:
    def test_resumo_traz_n_e_ic95(self) -> None:
        resultados = [
            _resultado(f"c{i}", "simples", 100.0 + 10 * i, 100.0) for i in range(5)
        ]
        resumo = resumir("simples", resultados)
        assert resumo.n == 5
        assert resumo.ic95_mdape is not None
        assert resumo.mdape is not None

    def test_estrato_vazio_vira_n_zero_e_nao_some(self) -> None:
        resumo = resumir("foto", [])
        assert resumo.n == 0
        assert resumo.mdape is None

    def test_caso_com_erro_nao_entra_na_metrica(self) -> None:
        bom = _resultado("ok", "simples", 110.0, 100.0)
        ruim = ResultadoCaso(
            id="falhou",
            estrato="simples",
            descricao="x",
            referencia_kcal=100.0,
            previsto_kcal=0.0,
            ape=float("nan"),
            erro="RuntimeError: provedor fora do ar",
        )
        assert resumir("simples", [bom, ruim]).n == 1

    def test_relatorio_traz_os_tres_estratos_e_a_procedencia(self) -> None:
        casos = carregar_casos()
        resultados = [
            _resultado(
                c.id, c.estrato.value, c.referencia_kcal * 1.1, c.referencia_kcal
            )
            for c in casos
        ]
        relatorio = montar_relatorio(casos, resultados)

        assert set(relatorio["por_estrato"]) == {"simples", "composto", "foto"}
        for estrato in ("simples", "composto", "foto"):
            assert relatorio["por_estrato"][estrato]["n"] > 0
        assert relatorio["dataset"]["sha"]
        assert relatorio["dataset"]["casos_nao_verificados"] == 0
        assert relatorio["prompts"]["meal_identify"]["sha"]
        assert relatorio["agregado"]["mdape"] == pytest.approx(10.0)

    def test_relatorio_em_texto_mostra_estrato_vazio(self) -> None:
        """Estrato sem resultado aparece como vazio em vez de sumir do relatório."""
        from evals.runner import formatar_texto

        casos = [c for c in carregar_casos() if c.estrato.value != "foto"]
        resultados = [
            _resultado(c.id, c.estrato.value, c.referencia_kcal, c.referencia_kcal)
            for c in casos
        ]
        texto = formatar_texto(montar_relatorio(casos, resultados))
        assert "foto" in texto
        assert "(vazio)" in texto
        assert "nunca %" in texto or "AGREGADO" in texto
