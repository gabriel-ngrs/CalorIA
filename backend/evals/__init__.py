"""Harness de avaliação do pipeline de IA.

Mede a qualidade do que o pipeline produz — não a redesenha. O contrato entre a
infraestrutura (schema, runner, métricas, invariância, histórico) e o conteúdo
(o dataset em si) é o `CasoEval` de `evals.schema`: qualquer fonte de ground
truth que preencha esse schema serve, o que mantém o harness agnóstico enquanto
a OQ2 da spec 002 segue aberta.

Convenção local: identificadores em pt-BR, seguindo `eval_golden_set.py` e
`instrument_meal_pipeline.py`, para não criar um segundo idioma dentro do mesmo
domínio (princípio 8 da spec 002).
"""

from __future__ import annotations
