# Log de Execução da Auditoria

Cronologia detalhada de cada passo executado.

## § Snapshot inicial (2026-05-10)

| Ferramenta | Resultado |
|---|---|
| ruff | 14 errors (9 fixable) |
| mypy strict | 6 errors em 1 arquivo (`app/services/ai/ai_client.py`) |
| radon avg CC | 16.56 (C) — 9 blocos ≥ B; pior: `build_meal_context` D(25) |
| pytest cov | 62% (99 passed, 1 failed em smoke `test_ai_client` por API externa) |
| pip-audit | 0 vulns |
| npm audit | 16 vulns (4 low, 3 moderate, 9 high, 0 critical) |
| eslint | 1 warning, 0 errors |
| tsc | 0 errors |
| LOC backend | 5.708 |
| LOC frontend | 10.573 |
| Tests backend LOC | 1.845 |
| Tests frontend LOC | 1.553 |
| Endpoints REST | 47 |
| Modelos SQLAlchemy | 12 |
| Migrações Alembic | 10 |

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

## PASSO 1.8 — Baseline tsc --noEmit

- **Início:** 2026-05-10 17:09
- **Fim:** 2026-05-10 17:09
- **Comando(s) executado(s):** `npx tsc --noEmit` em `frontend/`
- **Artefato(s):** `docs/auditoria/artefatos/baseline-tsc.txt`
- **Achados gerados:** nenhum (fase de baseline)
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** **0 errors** — saída vazia. Artefato anotado com `(no output — 0 errors)` para auto-documentar.

## PASSO 1.9 — Baseline LOC e estrutura

- **Início:** 2026-05-10 17:10
- **Fim:** 2026-05-10 17:10
- **Comando(s) executado(s):** bloco `find ... | wc -l` + contagem de routers/models/migrations conforme runbook
- **Artefato(s):** `docs/auditoria/artefatos/baseline-loc.txt`
- **Achados gerados:** nenhum (fase de baseline)
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** Backend 5.708 LOC · Frontend 10.573 LOC · Tests backend 1.845 · Tests frontend 1.553 · 47 endpoints REST · 12 modelos · 10 migrações. Seção "Métricas de baseline" também adicionada a `relatorio-preliminar.md`.

## PASSO 1.10 — Consolidar baselines em log.md

- **Início:** 2026-05-10 17:11
- **Fim:** 2026-05-10 17:11
- **Comando(s) executado(s):** consolidação manual lendo `artefatos/baseline-*.{txt,xml,json}` e populando seção `§ Snapshot inicial` no topo deste log
- **Artefato(s):** nenhum novo — consolida os anteriores
- **Achados gerados:** nenhum (fase de baseline)
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** snapshot acrescido como tabela única no topo de `log.md`. Encerra a FASE 1; análise/achados começam na FASE 2 (Frente A).

## PASSO 2.1 — Verificar separação API → service

- **Início:** 2026-05-10 17:15
- **Fim:** 2026-05-10 17:20
- **Comando(s) executado(s):** `rg -n "(select|insert|update|delete)\(" backend/app/api/v1/`
- **Artefato(s):** `docs/auditoria/artefatos/A1-queries-em-routers.txt`
- **Achados gerados:** AUD-001
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** 11 matches brutos; 5 são falsos positivos (`@router.delete(...)` decorator HTTP, ou método `.delete()` em service). Restam **6 queries SQL inline reais, todas em `push.py`** (subscriptions + notificações). Todos os outros routers delegam para services.

## PASSO 2.2 — Mapear filtragem por user_id

- **Início:** 2026-05-10 17:22
- **Fim:** 2026-05-10 17:30
- **Comando(s) executado(s):** bloco `rg @router + rg select( em services/` para gerar `A2-user-id-coverage.txt`; depois script Python `re.finditer` para checar bloco-por-bloco se cada endpoint chama `get_current_user_id` e usa `user_id` no corpo
- **Artefato(s):** `docs/auditoria/artefatos/A2-user-id-coverage.txt`
- **Achados gerados:** nenhum
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** Apenas 4/47 endpoints não usam `Depends(get_current_user_id)` — todos legitimamente públicos (`POST /auth/register|login|refresh`, `GET /push/vapid-public-key`). Em services e workers, todas as queries que retornam dados de usuário filtram por `user_id` (direto ou indireto via FK). Única exceção real: `meal_service.py:67` faz refresh por `meal.id` sem `user_id`, mas o registro foi criado na linha anterior pelo próprio usuário — sem risco. Nenhum achado criado.
