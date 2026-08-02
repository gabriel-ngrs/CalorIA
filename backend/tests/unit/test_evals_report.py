"""Série temporal versionada e gate da execução agendada (AC-16)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from evals.report import (
    FRACAO_MINIMA_DENTRO_DE_10PCT,
    MDAPE_MAXIMO,
    GateDoEvalError,
    carregar_historico,
    montar_linha,
    registrar,
    serie_temporal,
    verificar,
)


def _relatorio(
    *,
    commit_dataset: str = "abc123",
    mdape: float = 12.0,
    dentro: float = 0.8,
    prompt_v: int = 1,
    falhas: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    agregado = {
        "estrato": "agregado",
        "n": 10,
        "mdape": mdape,
        "mape": mdape + 5,
        "sspb": -3.2,
        "ic95_mdape": [8.0, 16.0],
        "dentro_da_tolerancia_kcal": dentro,
        "mae_macros_g": {},
        "acuracia_macros": {},
    }
    return {
        "dataset": {
            "sha": commit_dataset,
            "n": 10,
            "distribuicao": {"simples": 6, "composto": 4, "foto": 0},
            "casos_nao_verificados": 10,
        },
        "modelo": "llama-3.3-70b-versatile",
        "amostragem": {"temperature": 0.1, "max_tokens": 8192, "seed": 20260802},
        "prompts": {"meal_identify": {"versao": prompt_v, "sha": "f1334ef6"}},
        "agregado": agregado,
        "por_estrato": {"simples": agregado, "composto": agregado, "foto": agregado},
        "falhas": falhas or [],
    }


class TestLinhaDoHistorico:
    def test_amarra_metrica_a_commit_prompt_modelo_e_dataset(self) -> None:
        linha = montar_linha(_relatorio(), git_commit="deadbeef" * 5)
        assert linha["git_commit"] == "deadbeef" * 5
        assert linha["dataset_sha"] == "abc123"
        assert linha["modelo"] == "llama-3.3-70b-versatile"
        assert linha["prompts"]["meal_identify"]["sha"] == "f1334ef6"
        assert linha["amostragem"]["seed"] == 20260802

    def test_run_id_deriva_de_commit_e_dataset(self) -> None:
        """Mesma medição = mesmo `run_id` (NFR-5)."""
        a = montar_linha(_relatorio(), git_commit="c" * 40)
        b = montar_linha(_relatorio(), git_commit="c" * 40)
        assert a["run_id"] == b["run_id"]

    def test_dataset_diferente_muda_o_run_id(self) -> None:
        a = montar_linha(_relatorio(commit_dataset="aaa"), git_commit="c" * 40)
        b = montar_linha(_relatorio(commit_dataset="bbb"), git_commit="c" * 40)
        assert a["run_id"] != b["run_id"]

    def test_o_registro_nao_carrega_segredo(self) -> None:
        """Escopo travado: nada de chave de API, PII ou conteúdo de `.env`."""
        serializado = json.dumps(montar_linha(_relatorio(), git_commit="c" * 40))
        for proibido in ("gsk_", "API_KEY", "password", "@gmail"):
            assert proibido not in serializado


class TestHistoricoAppendOnly:
    def test_duas_execucoes_viram_duas_linhas_rastreaveis(self, tmp_path: Path) -> None:
        arquivo = tmp_path / "history.jsonl"
        registrar(
            montar_linha(_relatorio(mdape=20.0), git_commit="a" * 40), caminho=arquivo
        )
        registrar(
            montar_linha(_relatorio(mdape=12.0), git_commit="b" * 40), caminho=arquivo
        )

        historico = carregar_historico(arquivo)
        assert len(historico) == 2
        assert [h["git_commit"] for h in historico] == ["a" * 40, "b" * 40]
        assert [h["agregado"]["mdape"] for h in historico] == [20.0, 12.0]

    def test_registrar_nao_reescreve_linha_anterior(self, tmp_path: Path) -> None:
        arquivo = tmp_path / "history.jsonl"
        registrar(
            montar_linha(_relatorio(mdape=20.0), git_commit="a" * 40), caminho=arquivo
        )
        primeira = arquivo.read_text(encoding="utf-8")
        registrar(
            montar_linha(_relatorio(mdape=12.0), git_commit="b" * 40), caminho=arquivo
        )
        assert arquivo.read_text(encoding="utf-8").startswith(primeira)

    def test_historico_inexistente_e_lista_vazia(self, tmp_path: Path) -> None:
        assert carregar_historico(tmp_path / "nao-existe.jsonl") == []


class TestSerieTemporal:
    def test_gerada_sem_rede_a_partir_do_historico(self, tmp_path: Path) -> None:
        arquivo = tmp_path / "history.jsonl"
        registrar(
            montar_linha(_relatorio(mdape=20.0), git_commit="a" * 40), caminho=arquivo
        )
        registrar(
            montar_linha(_relatorio(mdape=12.0), git_commit="b" * 40), caminho=arquivo
        )

        texto = serie_temporal(carregar_historico(arquivo))
        assert "20.00%" in texto
        assert "12.00%" in texto
        assert "aaaaaaaaaaaa" in texto

    def test_anota_o_ponto_em_que_a_versao_de_prompt_mudou(
        self, tmp_path: Path
    ) -> None:
        arquivo = tmp_path / "history.jsonl"
        registrar(
            montar_linha(_relatorio(prompt_v=1), git_commit="a" * 40), caminho=arquivo
        )
        registrar(
            montar_linha(_relatorio(prompt_v=2), git_commit="b" * 40), caminho=arquivo
        )
        assert "versão de prompt mudou" in serie_temporal(carregar_historico(arquivo))

    def test_historico_vazio_diz_que_esta_vazio(self) -> None:
        assert "vazio" in serie_temporal([])


class TestGateDaExecucaoAgendada:
    def test_execucao_saudavel_passa(self) -> None:
        verificar(_relatorio(mdape=12.0, dentro=0.8))

    def test_caso_vazio_reprova(self) -> None:
        """NFR-3: nenhuma execução pode terminar com casos vazios."""
        relatorio = _relatorio(falhas=[{"id": "c1", "erro": "RateLimitError"}])
        with pytest.raises(GateDoEvalError, match="sem resultado"):
            verificar(relatorio)

    def test_mdape_acima_do_teto_reprova(self) -> None:
        with pytest.raises(GateDoEvalError, match="MdAPE"):
            verificar(_relatorio(mdape=MDAPE_MAXIMO + 0.1))

    def test_poucos_casos_dentro_da_tolerancia_reprova(self) -> None:
        with pytest.raises(GateDoEvalError, match="dentro de"):
            verificar(_relatorio(dentro=FRACAO_MINIMA_DENTRO_DE_10PCT - 0.01))

    def test_execucao_sem_nenhum_caso_reprova(self) -> None:
        relatorio = _relatorio()
        relatorio["agregado"]["n"] = 0
        with pytest.raises(GateDoEvalError, match="vazia"):
            verificar(relatorio)

    def test_a_mensagem_junta_todos_os_problemas(self) -> None:
        relatorio = _relatorio(
            mdape=99.0, dentro=0.1, falhas=[{"id": "c1", "erro": "boom"}]
        )
        with pytest.raises(GateDoEvalError) as exc:
            verificar(relatorio)
        assert "sem resultado" in str(exc.value)
        assert "MdAPE" in str(exc.value)


class TestHistoricoVersionado:
    def test_o_arquivo_versionado_existe_e_e_valido(self) -> None:
        """Nasce vazio; a primeira execução agendada real o popula."""
        from evals.report import HISTORY_PATH

        assert HISTORY_PATH.is_file()
        assert carregar_historico() == carregar_historico()
