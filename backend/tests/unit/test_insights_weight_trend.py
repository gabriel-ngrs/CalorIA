"""Regressão: direção da tendência de peso no insight semanal.

`WeightService.list` ordena por data DESC (`log_service.py:32`), então
`weight_logs[0]` é a pesagem MAIS RECENTE e `weight_logs[-1]` a mais antiga.
O ternário do insight semanal usava `"perdeu" if diff > 0`, invertendo as duas
direções: quem perdia 6 kg recebia um relatório sobre "o ganho de peso recente",
com recomendação nutricional na direção oposta à real.
"""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.ai.insights_generator import InsightsGenerator


def _log(dia: date, kg: float) -> SimpleNamespace:
    return SimpleNamespace(date=dia, weight_kg=kg)


async def _prompt_gerado(
    monkeypatch: pytest.MonkeyPatch, pesagens: list[SimpleNamespace]
) -> str:
    """Roda `weekly_insight` e devolve o prompt enviado à IA."""
    from app.services.ai import insights_generator as ig

    resumo = SimpleNamespace(
        start_date=date(2026, 7, 20),
        end_date=date(2026, 7, 26),
        total_days_logged=7,
        avg_calories=2000.0,
        avg_protein=100.0,
        avg_carbs=250.0,
        avg_fat=60.0,
    )

    monkeypatch.setattr(
        ig,
        "DashboardService",
        lambda db: SimpleNamespace(get_weekly=AsyncMock(return_value=resumo)),
    )
    monkeypatch.setattr(
        ig,
        "WeightService",
        lambda db: SimpleNamespace(list=AsyncMock(return_value=pesagens)),
    )

    client = MagicMock()
    client.generate_text = AsyncMock(return_value="relatório")
    await InsightsGenerator(client, MagicMock()).weekly_insight(1, date(2026, 7, 26))
    return str(client.generate_text.call_args[0][0])


class TestTendenciaDePeso:
    async def test_perda_de_peso_e_relatada_como_perda(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Ordem DESC: mais recente primeiro. 90 → 84 kg = PERDEU 6 kg.
        pesagens = [
            _log(date(2026, 7, 26), 84.0),
            _log(date(2026, 7, 24), 86.0),
            _log(date(2026, 7, 22), 88.0),
            _log(date(2026, 7, 20), 90.0),
        ]
        prompt = await _prompt_gerado(monkeypatch, pesagens)
        assert "perdeu 6.0kg" in prompt
        assert "ganhou" not in prompt

    async def test_ganho_de_peso_e_relatado_como_ganho(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pesagens = [
            _log(date(2026, 7, 26), 90.0),
            _log(date(2026, 7, 20), 84.0),
        ]
        prompt = await _prompt_gerado(monkeypatch, pesagens)
        assert "ganhou 6.0kg" in prompt
        assert "perdeu" not in prompt

    async def test_uma_unica_pesagem_nao_declara_tendencia(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        prompt = await _prompt_gerado(monkeypatch, [_log(date(2026, 7, 26), 84.0)])
        assert "Tendência de peso" not in prompt
