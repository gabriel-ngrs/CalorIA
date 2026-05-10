# Log de Execução da Auditoria

Cronologia detalhada de cada passo executado.

---

## PASSO 0.1 — Criar estrutura inicial

- **Início:** 2026-05-10 16:50
- **Fim:** 2026-05-10 16:51
- **Comando(s) executado(s):** `mkdir -p docs/auditoria/artefatos` + criação de 14 arquivos skeleton
- **Artefato(s):** nenhum (passo de inicialização)
- **Achados gerados:** nenhum
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** criados `log.md`, `achados.md`, 11 arquivos por frente (`01-arquitetura.md` … `11-dx-docs.md`), `relatorio-preliminar.md` e diretório `artefatos/` vazio. Total 14 arquivos novos + 1 diretório.

## PASSO 1.1 — Baseline ruff

- **Início:** 2026-05-10 16:55
- **Fim:** 2026-05-10 16:56
- **Comando(s) executado(s):** `RUFF_CACHE_DIR=/tmp/ruff-baseline uvx ruff check .` em `backend/`
- **Artefato(s):** `docs/auditoria/artefatos/baseline-ruff.txt`
- **Achados gerados:** nenhum (fase de baseline)
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** **14 errors**, 9 corrigíveis com `--fix`.

## PASSO 1.2 — Baseline mypy strict

- **Início:** 2026-05-10 16:58
- **Fim:** 2026-05-10 17:00
- **Comando(s) executado(s):** `uv run --extra dev --with types-passlib mypy --strict --cache-dir=/tmp/mypy-baseline app/` em `backend/`
- **Artefato(s):** `docs/auditoria/artefatos/baseline-mypy.txt`
- **Achados gerados:** nenhum (fase de baseline)
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** **6 errors** em 1 arquivo (`app/services/ai/ai_client.py`), 67 source files checked. Cache root-owned em `.mypy_cache` exigiu `--cache-dir=/tmp/mypy-baseline` (mesmo motivo do `RUFF_CACHE_DIR`). Mypy não estava no `.venv`; usou `uv run --extra dev`. `pyproject.toml` já configura `strict = true` e plugin `pydantic.mypy`.

## PASSO 1.3 — Baseline radon

- **Início:** 2026-05-10 17:01
- **Fim:** 2026-05-10 17:02
- **Comando(s) executado(s):** `uvx radon cc app/ -s -nc -a` e `uvx radon mi app/ -s` em `backend/`
- **Artefato(s):** `docs/auditoria/artefatos/baseline-radon-cc.txt`, `docs/auditoria/artefatos/baseline-radon-mi.txt`
- **Achados gerados:** nenhum (fase de baseline)
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** 9 blocos com CC ≥ B; **average CC = 16.56 (C)**. Hotspots: `build_meal_context` (D, 25), `InsightsGenerator.goal_adjustment_suggestion` (C, 18), `MealParser._lookup_and_fill` (C, 16). MI: todos os módulos analisados em rank A (≥ 63.89).

## PASSO 1.4 — Baseline cobertura backend

- **Início:** 2026-05-10 17:03
- **Fim:** 2026-05-10 17:04
- **Comando(s) executado(s):** `TEST_DATABASE_URL=postgresql+asyncpg://caloria:caloria@localhost:5432/caloria_test .venv/bin/pytest --cov=app --cov-report=term --cov-report=xml -q`
- **Artefato(s):** `docs/auditoria/artefatos/baseline-coverage.txt`, `docs/auditoria/artefatos/baseline-coverage.xml`
- **Achados gerados:** nenhum (fase de baseline; análise de cobertura virá na FASE 9)
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** **TOTAL = 62%** (2512 statements, 942 missing). 99 passed, **1 failed** (`tests/smoke_test.py::test_ai_client` — `groq.APIConnectionError`, falha externa de rede/API; não é bug funcional do código). Hotspots de baixa cobertura: `app/workers/celery_app.py` 0%, `app/services/ai/insights_generator.py` 14%, `app/services/ai/context_builder.py` 20%, `app/services/ai/pattern_analyzer.py` 27%, `app/services/push_service.py` 29%, `app/services/reminder_service.py` 31%, `app/workers/tasks/reports.py` 32%.

## PASSO 1.5 — Baseline pip-audit

- **Início:** 2026-05-10 17:05
- **Fim:** 2026-05-10 17:05
- **Comando(s) executado(s):** `uvx pip-audit -r <(uv pip compile pyproject.toml)` em `backend/`
- **Artefato(s):** `docs/auditoria/artefatos/baseline-pip-audit.txt`
- **Achados gerados:** nenhum (fase de baseline)
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** **No known vulnerabilities found** (29 pacotes auditados a partir do `pyproject.toml` resolvido por `uv pip compile`).

## PASSO 1.6 — Baseline npm audit

- **Início:** 2026-05-10 17:06
- **Fim:** 2026-05-10 17:06
- **Comando(s) executado(s):** `npm audit --json` e `npm audit` em `frontend/`
- **Artefato(s):** `docs/auditoria/artefatos/baseline-npm-audit.json`, `docs/auditoria/artefatos/baseline-npm-audit.txt`
- **Achados gerados:** nenhum (fase de baseline; análise virá na FASE 8 — Frente G)
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** **16 vulnerabilities** — 4 low, 3 moderate, **9 high**, 0 critical. Pacotes citados na cauda: `next/node_modules/postcss`, `postcss`.

## PASSO 1.7 — Baseline ESLint frontend

- **Início:** 2026-05-10 17:07
- **Fim:** 2026-05-10 17:08
- **Comando(s) executado(s):** `npx next lint --no-cache` em `frontend/` (substituiu `npm run lint` por causa de permissão root em `.next/cache`)
- **Artefato(s):** `docs/auditoria/artefatos/baseline-eslint.txt`
- **Achados gerados:** nenhum (fase de baseline)
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** **1 warning, 0 errors** — `components/auth/Plasma.tsx:155` (`react-hooks/exhaustive-deps`, ref cleanup). `npm run lint` falhou com `EACCES: permission denied, mkdir '/home/gabriel/projetos/CalorIA/frontend/.next/cache/eslint'`; mesmo problema legado do `.ruff_cache` / `.mypy_cache`. `--no-cache` contornou.
