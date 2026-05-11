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

## PASSO 2.3 — Auditar relacionamentos cascade

- **Início:** 2026-05-10 17:31
- **Fim:** 2026-05-10 17:34
- **Comando(s) executado(s):** `rg -n "relationship\(|ForeignKey\(" backend/app/models/`
- **Artefato(s):** `docs/auditoria/artefatos/A3-relacionamentos.txt`
- **Achados gerados:** nenhum
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** Padrão **consistente** em todos os 11 relacionamentos: ORM `cascade="all, delete-orphan"` + FK `ondelete="CASCADE"` para relações de posse; `MealItem → Food` usa `SET NULL` por ser referencial (snapshot nutricional preservado). `MealItem` não declara `relationship("Food")` — intencional para evitar acoplamento com banco nutricional. Nenhuma divergência ORM/DB.

## PASSO 2.4 — Documentar responsabilidades dos services

- **Início:** 2026-05-10 17:35
- **Fim:** 2026-05-10 17:42
- **Comando(s) executado(s):** `wc -l` em todos os services + script Python AST para extrair classes e métodos públicos
- **Artefato(s):** nenhum dedicado (tabela embutida em `01-arquitetura.md § A.4`)
- **Achados gerados:** AUD-002
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** 17 services analisados; LOC varia de 28 (`tdee.py`) a **512** (`insights_generator.py`). Único violador do critério `>300 LOC + >4 responsabilidades` é `InsightsGenerator` (7 métodos públicos heterogêneos). `context_builder.py` tem 313 LOC mas só 1 método público + helpers — coeso, sem achado.

## PASSO 2.5 — Mapeamento de dependências entre services

- **Início:** 2026-05-10 17:43
- **Fim:** 2026-05-10 17:48
- **Comando(s) executado(s):** `rg -n "from app\.services" backend/app/services/`
- **Artefato(s):** `docs/auditoria/artefatos/A5-dep-services.txt`
- **Achados gerados:** nenhum adicional (reforça AUD-002 mas não cria novo)
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** Grafo é **DAG** — sem ciclos. Diagrama Mermaid em `01-arquitetura.md § A.5`. Fan-out mais alto: `InsightsGenerator` (5 services) — reforça recomendação de quebra. Camada `ai/*` consome só `AIClient`+`food_lookup`+`utils`(+`UserService` em `context_builder`); boa separação.

## PASSO 3.1 — Routers: response_model e status codes

- **Início:** 2026-05-10 17:55
- **Fim:** 2026-05-10 17:59
- **Comando(s) executado(s):** script Python iterando todos os `@router.*` de `backend/app/api/v1/*.py`; `rg -oN status_code=...` para inventário
- **Artefato(s):** `docs/auditoria/artefatos/B1-routers-response.txt`
- **Achados gerados:** AUD-003
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** 47 endpoints; **45 com `response_model` ou 204** (96% cobertura). 2 violadores em `push.py` (`POST /push/subscribe`, `POST /notifications/read-all`), ambos retornando `dict[str, str]`. Status codes em uso (404/201/502/204/422/401/503/409/200) coerentes com semântica HTTP.

## PASSO 3.2 — Routers: HTTPException com `from`

- **Início:** 2026-05-10 18:00
- **Fim:** 2026-05-10 18:03
- **Comando(s) executado(s):** `rg -n "raise HTTPException" backend/app/api/v1/ -A 3` + script Python de detecção de contexto `except`
- **Artefato(s):** `docs/auditoria/artefatos/B2-httpexc.txt`
- **Achados gerados:** AUD-004
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** 24 `raise HTTPException` totais; 9 dentro de `except`; **1 sem `from`** (`meals.py:101`, conforme já mapeado no plano Anexo A). Todos os 8 demais (em `ai.py`) já usam `from exc`. ✅

## PASSO 3.3 — Routers: paginação consistente

- **Início:** 2026-05-10 18:04
- **Fim:** 2026-05-10 18:06
- **Comando(s) executado(s):** `rg -n "skip|limit" backend/app/api/v1/ | grep "Query"`
- **Artefato(s):** `docs/auditoria/artefatos/B3-paginacao.txt`
- **Achados gerados:** AUD-005
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** 5 endpoints expõem `limit`; 3 expõem `skip`. **Único violador real:** `weight.py:16` aceita `le=200` enquanto o resto usa `le=100`. Defaults variam de 20 a 50 (esperado por domínio); `dashboard/weight-chart` e `notifications` usam `limit-only` (filtro temporal/recente).

## PASSO 3.4 — Services: detecção de N+1

- **Início:** 2026-05-10 18:07
- **Fim:** 2026-05-10 18:14
- **Comando(s) executado(s):** `rg -n "for .* in .*:\s*$" backend/app/services/ backend/app/workers/ -A 5 | grep -B 1 "await.*execute|await.*get_|await.*list"` + leitura manual dos hits
- **Artefato(s):** `docs/auditoria/artefatos/B4-n-mais-1.txt`
- **Achados gerados:** AUD-006, AUD-007, AUD-008
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** **5 N+1 reais** confirmados. Mais crítico: `food_lookup.py:89` (caminho síncrono do user, ~25 queries por refeição). `InsightsGenerator` repete o padrão em 2 métodos — solução já existe no projeto (`MealService.get_macros_by_date_range` foi introduzido em `DashboardService` para resolver caso análogo). Workers (reminders+maintenance) escalam linear com base de usuários.

## PASSO 3.5 — Schemas Pydantic: from_attributes

- **Início:** 2026-05-10 18:15
- **Fim:** 2026-05-10 18:18
- **Comando(s) executado(s):** `rg -n "from_attributes" backend/app/schemas/` + script Python para listar Responses + `rg` para descobrir como cada Response é construída
- **Artefato(s):** `docs/auditoria/artefatos/B5-pydantic-config.txt`
- **Achados gerados:** nenhum
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** 12 `*Response`; **8 com `from_attributes`** (todas serializam ORM). 4 sem `from_attributes` — `TokenResponse`, `MealAnalysisResponse`, `InsightResponse`, `NutritionalAlertsResponse` — todas construídas via kwargs em services. Configuração correta para os 4 (não são ORM). Schemas `*Create/*Update/Request` também corretos (inputs puros).

## PASSO 3.6 — Validação de inputs sensíveis

- **Início:** 2026-05-10 18:19
- **Fim:** 2026-05-10 18:25
- **Comando(s) executado(s):** leitura de `backend/app/schemas/*.py` + `grep -nE "Field\(" backend/app/schemas/`
- **Artefato(s):** nenhum dedicado (matriz embutida em `02-backend.md § B.6`)
- **Achados gerados:** AUD-009, AUD-010
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** Numéricos bem cobertos (`weight_kg`, `amount_ml`, `mood_level`, etc., todos com `gt`/`le`). **Pior achado: `image_base64` sem `max_length`** (vetor de DoS — payload pode ter qualquer tamanho). 8 campos texto livre (`notes`, `message`, `question`, `raw_input`) sem `max_length` — abuso de storage e inflar prompts IA.

## PASSO 3.7 — Type ignores

- **Início:** 2026-05-10 18:26
- **Fim:** 2026-05-10 18:30
- **Comando(s) executado(s):** `rg -n "# type: ignore" backend/app/`
- **Artefato(s):** `docs/auditoria/artefatos/B7-type-ignores.txt`
- **Achados gerados:** AUD-011
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** **22 `# type: ignore`** totais. **7 justificáveis** (`@celery_app.task` decorator não tipado × 6 + `aioredis.from_url` × 1). **15 elimináveis** — os 12 do `[arg-type]` em parsers IA derivam do padrão `float(d.get(...))` em `dict[str, Any]` da IA; solução: TypedDict ou cast. Os 3 restantes em `meal_service.py:45`, `utils.py:15`, `utils.py:18` são correção pontual de tipos.

## PASSO 4.1 — AIClient: cache, retry, observabilidade

- **Início:** 2026-05-10 18:35
- **Fim:** 2026-05-10 18:42
- **Comando(s) executado(s):** leitura de `backend/app/services/ai/ai_client.py` + verificação de timeout uvicorn em `Dockerfile`/compose
- **Artefato(s):** nenhum dedicado (matriz embutida em `03-ia.md § C.1`)
- **Achados gerados:** AUD-012, AUD-013, AUD-014
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** Cache (sha256 24-hex, TTL 7d) está bom. Pontos sensíveis: (1) retry baseado em `"429" in str(exc)` é frágil + 4 tentativas chegam a 225s acumulados (pode estourar timeout do reverse proxy); (2) log de tokens sem `user_id`/`request_id`/modelo/custo — sem dimensão para agregar; (3) `aioredis.from_url(...)` aberto/fechado por chamada (sem pool persistente). Vision usa mesmo padrão de retry — afetado pelos mesmos itens.

## PASSO 4.2 — Duplicação MealParser ↔ VisionParser

- **Início:** 2026-05-10 18:43
- **Fim:** 2026-05-10 18:48
- **Comando(s) executado(s):** `diff -u meal_parser.py vision_parser.py` + script Python que separa por método e calcula igualdade linha-a-linha
- **Artefato(s):** `docs/auditoria/artefatos/C2-parsers-diff.txt`
- **Achados gerados:** AUD-015
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** **`_estimate_macros_batch` 100% idêntico** (exceto 1 palavra na docstring). **`_lookup_and_fill` funcionalmente equivalente** (~85 LOC). Divergência legítima fica em `_identify_foods` (texto vs imagem) e entry points. ~120 LOC extraíveis para classe base `BaseAIFoodParser(ABC)`.

## PASSO 4.3 — FoodLookup: performance

- **Início:** 2026-05-10 18:50
- **Fim:** 2026-05-10 19:00
- **Comando(s) executado(s):** leitura de `food_lookup.py` + script Python para estimar n-gramas + 3× `EXPLAIN ANALYZE` no Postgres real (variantes da query)
- **Artefato(s):** `docs/auditoria/artefatos/C3-food-lookup-explain.txt`
- **Achados gerados:** **AUD-016 (🔴 crítica)** — primeiro achado crítico da auditoria
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** Achado muito mais grave do que o esperado pelo runbook (que previa 🟠 batch). Medido em ambiente real: **query atual leva 585ms** (Seq Scan) vs **8ms** sem o OR `similarity()`. Combinado com N+1 do AUD-006 (~25 n-gramas), uma refeição leva **~14.6s** bloqueando worker uvicorn. Com 2 workers default, 2 usuários simultâneos = backend indisponível. Fix simples (`SET pg_trgm.similarity_threshold + remover OR`) reduz 70×.

## PASSO 4.4 — InsightsGenerator: decomposição

- **Início:** 2026-05-10 19:01
- **Fim:** 2026-05-10 19:05
- **Comando(s) executado(s):** `rg "    async def [a-z]" insights_generator.py` + awk para LOC por método + leitura de imports
- **Artefato(s):** `docs/auditoria/artefatos/C4-insights-metodos.txt`
- **Achados gerados:** nenhum novo (reforça AUD-002 com dados)
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** 7 métodos públicos: `daily_insight` (33), `weekly_insight` (28), `monthly_report` (**158**), `answer_question` (28), `suggest_meal` (57), `nutritional_alerts` (90), `goal_adjustment_suggestion` (78). `monthly_report` sozinho ocupa 1/3 do arquivo e contém N+1 do AUD-007. Plano de decomposição: 3 services (PeriodicInsights, Recommendations, QA) ≤ 250 LOC cada.

## PASSO 4.5 — extract_json_from_ai_response: robustez

- **Início:** 2026-05-10 19:06
- **Fim:** 2026-05-10 19:10
- **Comando(s) executado(s):** leitura de `utils.py` + script Python sintético com 9 padrões de saída de LLM
- **Artefato(s):** nenhum dedicado (matriz embutida em `03-ia.md § C.5`)
- **Achados gerados:** AUD-017
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** 4/9 padrões testados falham: texto antes do JSON, texto depois, ambos, e trailing comma. Pior: `{"items": [...]}` é aceito mas retorna dict; type hint promete list — caller silenciosamente percorre as keys do dict.

## PASSO 5.1 — Páginas frontend grandes

- **Início:** 2026-05-10 19:15
- **Fim:** 2026-05-10 19:18
- **Comando(s) executado(s):** `wc -l frontend/app/(dashboard)/*/page.tsx frontend/components/dashboard/*.tsx | sort -rn`
- **Artefato(s):** `docs/auditoria/artefatos/D1-paginas-loc.txt`
- **Achados gerados:** AUD-018
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** 4 arquivos > 500 LOC. **Pior: `refeicoes/page.tsx` 1055 LOC** (god component — listagem + criação texto + foto + voz + edição inline; 25 ícones importados). 8 arquivos > 300 LOC.

## PASSO 5.2 — Hooks customizados

- **Início:** 2026-05-10 19:19
- **Fim:** 2026-05-10 19:23
- **Comando(s) executado(s):** `wc -l frontend/lib/hooks/*.ts` + leitura de cada hook + `frontend/app/providers.tsx`
- **Artefato(s):** nenhum dedicado (matriz embutida em `04-frontend.md § D.2`)
- **Achados gerados:** AUD-019
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** Estrutura sólida — defaults globais bem ajustados (staleTime 3min, retry skip 401), `invalidateQueries` em todos os `onSuccess`, `staleTime` override quando faz sentido. **Optimistic updates ausentes em 100% dos hooks** — oportunidade UX para toggles/mark-read. `QueryCache.onSuccess`/`onError` com `console.log` e `NavTimer` rodam em produção (será detalhado em PASSO 5.3).

## PASSO 5.3 — Camada API e cache de token

- **Início:** 2026-05-10 19:24
- **Fim:** 2026-05-10 19:28
- **Comando(s) executado(s):** leitura de `frontend/lib/api.ts` + `grep -nE "console\." frontend/lib/api.ts frontend/app/providers.tsx` + `grep "process.env.NODE_ENV"`
- **Artefato(s):** nenhum dedicado (matriz embutida em `04-frontend.md § D.3`)
- **Achados gerados:** AUD-020
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** Fluxo de token bem desenhado (cache 90s, dedupe Promise, refresh proativo 2min antes, retry transparente em 401). **7 console.log/error rodam em produção** — único item gateado é `ReactQueryDevtools`. Volume típico 50-100 logs/min em sessão ativa.

## PASSO 5.4 — Bug do contrato login (verificação)

- **Início:** 2026-05-10 19:29
- **Fim:** 2026-05-10 19:33
- **Comando(s) executado(s):** leitura de `backend/app/api/v1/auth.py:37-50` + `frontend/app/api/auth/[...nextauth]/route.ts` + `grep -rn "session.user.id"` em `app|components|lib`
- **Artefato(s):** nenhum dedicado (matriz embutida em `04-frontend.md § D.4`)
- **Achados gerados:** AUD-021
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** Bug **confirmado**. Backend `TokenResponse` tem só `access_token`, `refresh_token`, `token_type` — sem `user`. Frontend `authorize` lê `data.user?.id ?? ""` e `data.user?.name ?? credentials.email`. Resultado: `id="" `, `name=email`. Como `id` não é usado em lógica funcional (verificado), bug é silencioso — degrada apenas UX (nome). Login funciona end-to-end.

## PASSO 5.5 — TypeScript: usos de any

- **Início:** 2026-05-10 19:34
- **Fim:** 2026-05-10 19:36
- **Comando(s) executado(s):** `rg -n ": any\b|as any\b" frontend/app frontend/components frontend/lib | grep -v test/mock/build`
- **Artefato(s):** `docs/auditoria/artefatos/D5-any-usage.txt`
- **Achados gerados:** AUD-022
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** **6 `any` totais**, todos relacionados à Web Speech API (SpeechRecognition), duplicados entre `QuickAddModals.tsx` e `refeicoes/page.tsx`. Nenhum outro `any` no código de produção. Solução: module augmentation em `types/speech.d.ts` + extração de `useVoiceCapture()` (também resolve duplicação relacionada a AUD-018).

## PASSO 5.6 — PWA / Service Worker

- **Início:** 2026-05-10 19:37
- **Fim:** 2026-05-10 19:40
- **Comando(s) executado(s):** leitura de `frontend/public/sw.js` + `frontend/app/manifest.ts` + `ls frontend/public/icons/`
- **Artefato(s):** nenhum dedicado (matriz embutida em `04-frontend.md § D.6`)
- **Achados gerados:** AUD-023
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** SW funcional para push (`push`, `notificationclick` corretos) mas sem `skipWaiting`/`clients.claim` — atualizações exigem fechar tabs. Manifest cobre o essencial; faltam tamanhos comuns de ícone (144, 384), `apple-touch-icon` (iOS) e `screenshots` (Lighthouse).

## PASSO 5.7 — Bundle size analysis

- **Início:** 2026-05-10 19:41
- **Fim:** 2026-05-10 19:43
- **Comando(s) executado(s):** `grep "@next/bundle-analyzer"` em `frontend/package.json` (não encontrado); leitura de `next.config.mjs` e dependências
- **Artefato(s):** `docs/auditoria/artefatos/D7-bundle.txt`
- **Achados gerados:** AUD-024
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** Build com `ANALYZE=true` pulado (analyzer não instalado, conforme runbook orienta). Configuração atual já tem `output: standalone`, `transpilePackages: ["ogl"]` e `optimizePackageImports: ["lucide-react"]`. Suspeitos por tamanho conhecido: `recharts`, `ogl`, `@radix-ui` (8 pacotes). `date-fns@^2.30.0` poderia subir para v3 (locales tree-shake automático).

## PASSO 6.1 — Padrão `_run` deprecated

- **Início:** 2026-05-10 19:48
- **Fim:** 2026-05-10 19:52
- **Comando(s) executado(s):** `rg -n "asyncio\.get_event_loop\(\)" backend/app/` + leitura dos 3 módulos para confirmar que a helper é idêntica em assinatura/docstring/corpo
- **Artefato(s):** `docs/auditoria/artefatos/E1-get-event-loop.txt`
- **Achados gerados:** AUD-025
- **Commit:** 38dc89f
- **Notas:** **3 ocorrências confirmadas**, exatamente nos arquivos esperados pelo runbook (`reminders.py:21`, `reports.py:19`, `maintenance.py:21`). Cópias **textualmente idênticas** (mesma assinatura `def _run(coro: Any) -> Any`, mesma docstring, mesma implementação) — pede extração para `app/workers/_utils.py`. Severidade 🟠 alta porque, além do `DeprecationWarning` (Python 3.10+ → erro em 3.14), há risco real de `RuntimeError: Event loop is closed` se o pool migrar de prefork para gevent/eventlet ou se alguma task fechar o loop por bug. Fix imediato: trocar por `asyncio.run(coro)`. Também sugerido `PYTHONWARNINGS=error::DeprecationWarning` em CI para pegar regressões.

## PASSO 6.2 — dispatch_due_reminders: timezone

- **Início:** 2026-05-10 19:55
- **Fim:** 2026-05-10 20:02
- **Comando(s) executado(s):** leitura de `reminders.py:36-71` + `models/reminder.py` + `docker exec caloria_postgres psql -c "SHOW timezone"` + `docker inspect caloria_postgres` + `grep -nB 1 -A 1 "TZ\|timezone" docker-compose*.yml backend/app/workers/celery_app.py`
- **Artefato(s):** `docs/auditoria/artefatos/E2-tz.txt`
- **Achados gerados:** AUD-026
- **Commit:** cd9adc3
- **Notas:** Bug **latente, não ativo**. `datetime.now()` é naive (linha 37); `Reminder.time` é `Time` sem TZ; comparação direta `hour/minute`. **Hoje funciona por acidente** porque todos os containers (postgres, backend, celery_worker, celery_beat) têm `TZ=America/Sao_Paulo` (verificado em ambos compose files) e `User` não tem campo de fuso — logo "agora naive" == "agora São Paulo" == "horário que o usuário digitou". Quebra silencioso em 3 cenários: (1) migração para UTC (default na maioria dos PaaS) → offset de 3h; (2) usuário fora de São Paulo → lembrete dispara em hora errada para ele; (3) DST em outros países → duplicação ou pulo. Celery `timezone="America/Sao_Paulo"`+`enable_utc=True` cobre só o disparo do beat (cron interpretado em SP), não o conteúdo da task. Recomendação curta: trocar por `datetime.now(ZoneInfo("America/Sao_Paulo"))`. Médio: adicionar `User.timezone`. Longo: pré-calcular `Reminder.next_fire_at`.

## PASSO 6.3 — Hardcode de meta de hidratação

- **Início:** 2026-05-10 20:05
- **Fim:** 2026-05-10 20:10
- **Comando(s) executado(s):** `rg -n "2000" backend/app/workers/tasks/reminders.py` + `grep -n "water_goal_ml" backend/app/models/user.py` + leitura de `_send_hydration_reminders_async` (linhas 154-220)
- **Artefato(s):** `docs/auditoria/artefatos/E3-hydration-hardcode.txt`
- **Achados gerados:** AUD-027
- **Commit:** b0da6c2
- **Notas:** **Confirmado**: 2 sites com `2000` em `reminders.py:174,179`; `User.water_goal_ml: Mapped[int | None]` declarado em `models/user.py:44` mas nenhum uso em `backend/app/workers/`. Frontend já edita o campo (perfil/onboarding). Impacto: usuários com meta < 2000 recebem push depois da meta dele; usuários com meta > 2000 param de receber em 2000 (silencioso, difícil debugar sem logs estruturados — vide AUD-013). Bônus identificado: a mesma função tem N+1 já mapeado em AUD-008 (`for user in users: HydrationService(db).get_day_summary(user.id, today)`); fix do AUD-027 e do AUD-008 cabem no mesmo PR. Recomendação trivial: `goal_ml = user.water_goal_ml or 2000` e usar nas duas linhas.

## PASSO 6.4 — Duplicação de tratamento WebPush 410

- **Início:** 2026-05-10 20:13
- **Fim:** 2026-05-10 20:20
- **Comando(s) executado(s):** `rg -n "WebPushException|status_code == 410|expired_ids" backend/app/workers/ backend/app/services/push_service.py` + leitura de `services/push_service.py` (todo) + 4 trechos dos workers para confirmar identidade
- **Artefato(s):** `docs/auditoria/artefatos/E4-push-410.txt`
- **Achados gerados:** AUD-028
- **Commit:** f4ca308
- **Notas:** **4 sites** confirmados, ~30 LOC cada (≈120 LOC duplicados): `reminders.py:100-137` (lembrete pontual), `reminders.py:194-228` (hidratação), `reports.py:80-118` (resumo diário), `reports.py:179-217` (relatório semanal). Diferenças reais: apenas `body` e `url` (`/dashboard` × 2 vs `/relatorios` × 2). `services/push_service.py:11-50` já tem `send_push_notification_sync` mas NÃO tem o wrapper que busca subs+envia+deleta — esse ficou repetido. Bônus de smell: cada site repete `try: from pywebpush import WebPushException; except ImportError: pass` que nunca dispara (pywebpush é dependência direta no `pyproject.toml`). Severidade 🟡 (duplicação clássica, sem bug funcional hoje, mas custo de mudança ×4). Plano: `PushService(db).send_with_cleanup(user_id, title, body, url)` — cada caller vira 1 linha. Combina bem com AUD-013 (logs estruturados) e AUD-014 (pool Redis) num PR só de "limpeza de PushService".

## PASSO 6.5 — Maintenance e cleanup

- **Início:** 2026-05-10 20:24
- **Fim:** 2026-05-10 20:32
- **Comando(s) executado(s):** leitura de `backend/app/workers/tasks/maintenance.py` (todo, 129 linhas) + `docker exec caloria_postgres psql -c "\d ai_conversations"` + `\d weight_logs` + `EXPLAIN DELETE FROM ai_conversations WHERE updated_at < NOW() - INTERVAL '90 days' RETURNING id`
- **Artefato(s):** `docs/auditoria/artefatos/E5-ai-conv-indexes.txt`
- **Achados gerados:** AUD-029
- **Commit:** 629f196
- **Notas:** **`cleanup_old_conversations`** — usa `updated_at < cutoff` mas índices da tabela são apenas em `id`, `external_chat_id`, `user_id`. `EXPLAIN` confirma Seq Scan (cost 12.28, ~43 rows). Hoje irrelevante (Postgres escolhe Seq Scan corretamente nesse tamanho); vira problema quando a tabela crescer. Já é TZ-aware (`datetime.now(tz=UTC)`) — não tem o problema do AUD-026. **`recalculate_tdee`** — threshold de 2 kg é coerente clinicamente (flutuação diária típica ≈ 1 kg). N+1 do `for user in users` + 1 `SELECT WeightLog` por user já está em AUD-008, sem novo achado. Apenas atualiza `current_weight`+`tdee_calculated`; hoje as metas derivam de `tdee_calculated` na UI, então não há cascade de updates faltando. `weight_logs` tem `ix_weight_logs_user_id` + `ix_weight_logs_date` — para a query agregada do AUD-008 idealmente um índice composto `(user_id, date DESC, created_at DESC)`, fora de escopo deste passo (anotar para PASSO 7.1).

## PASSO 7.1 — Inventário de índices

- **Início:** 2026-05-10 20:38
- **Fim:** 2026-05-10 20:48
- **Comando(s) executado(s):** `docker exec caloria_postgres psql -c "SELECT ... FROM pg_indexes WHERE schemaname='public'"` + `EXPLAIN` em 3 queries candidatas (`meals user+date`, `notifications unread count`, `reminders active=true`) + `pg_relation_size` para tamanhos
- **Artefato(s):** `docs/auditoria/artefatos/F1-indexes.txt`
- **Achados gerados:** AUD-030, AUD-031, AUD-032
- **Commit:** ebd045c
- **Notas:** **35 índices não-pkey** mapeados em 13 tabelas. Padrão observado: SQLAlchemy gera índices separados por coluna FK/filtro, **nunca compostos**. 4 tabelas (`meals`, `weight_logs`, `mood_logs`, `hydration_logs`) repetem o caso clássico `WHERE user_id AND date` sem composto — `EXPLAIN` confirma `Index Cond: (user_id=1)` + `Filter: (date=...)` (heap scan extra). `notifications` ainda pior: sem nenhum índice em `read`, polling do badge varre todo histórico do usuário no heap. **Surpresa**: `foods.name` tem 2 índices (`ix_foods_name` non-unique + `taco_foods_name_key` UNIQUE legado da era TACO-only); UNIQUE pode bloquear seed do Open Food Facts (duplicatas legítimas por marca). Não-achados verificados: `meal_items(meal_id, food_id)` composto sugerido no plano não agrega valor (joins simples cobertos); `reminders(active)` Seq Scan é correto para tabela pequena hoje. Achados criados: 2× 🟡 (compostos faltando) + 1× 🟢 (índices duplicados em foods).

## PASSO 7.2 — EXPLAIN ANALYZE de queries críticas

- **Início:** 2026-05-10 20:52
- **Fim:** 2026-05-10 21:02
- **Comando(s) executado(s):** `EXPLAIN ANALYZE` em 6 queries representativas via `docker exec caloria_postgres psql` (Q1 daily summary, Q2 dashboard semanal, Q3 unread count, Q4 reminders ativos, Q5 food lookup, Q6 weight history); duas tentativas porque `meal_items.protein_g` não existe (coluna real é `protein`), e `foods.calories_kcal` virou `calories_100g`.
- **Artefato(s):** `docs/auditoria/artefatos/F2-explain.txt`
- **Achados gerados:** nenhum novo (as 6 queries validam AUD-016, AUD-030, AUD-031 e o latente de § F.1 sobre `reminders`)
- **Commit:** 4e098d1
- **Notas:** **Caveat:** apenas `foods` (42.103 rows) tem dados; outras tabelas vazias. `actual time` é trivial mas o **plano** é representativo (planner usa estatísticas, não volume real). **Insights**: (1) Q2 — planner escolheu `ix_meals_date` em vez de `ix_meals_user_id` para `BETWEEN 7 days` — composto `(user_id, date)` resolve ambos caminhos; (2) Q5 confirma AUD-016 — sem o OR `similarity() >= 0.18`, query leva **19ms** (Bitmap Index Scan + 1166 candidatos + sort top-5); com o OR, vai para 585ms; (3) Q4 — Seq Scan está correto para tabela vazia mas planner estima 335 rows pela selectivity default; risco latente = quando reminders crescer, query continuará puxando todos os ativos para filtrar `time` em Python. Anotado: otimização Q5 adicional possível com KNN `<->` operator (~5ms), fora de escopo. **Sem achados novos** porque os 6 planos já estão cobertos por AUD-016/030/031 e § F.1 latente de `reminders`.

## PASSO 7.3 — Migrações Alembic: reversibilidade

- **Início:** 2026-05-10 21:05
- **Fim:** 2026-05-10 21:14
- **Comando(s) executado(s):** loop em `backend/alembic/versions/*.py` com Python regex extraindo corpo de `def downgrade()`; `grep -rn "pg_trgm\|CREATE EXTENSION" backend/alembic/versions/`; `grep -n "MealSource\|TELEGRAM" backend/app/models/meal.py`; `psql -c "SELECT enumlabel FROM pg_enum WHERE enumtypid=(SELECT oid FROM pg_type WHERE typname='mealsource')"`; `SELECT source, COUNT(*) FROM meals GROUP BY source`
- **Artefato(s):** `docs/auditoria/artefatos/F3-downgrade.txt`
- **Achados gerados:** AUD-033, AUD-034
- **Commit:** f83f01f
- **Notas:** **10 migrações totais**, todas com `def downgrade()` declarado. **9 reversíveis** (3-25 LOC efetivas), **1 com apenas `pass`**: `20260306_adiciona_dessert_mealtype.py` (AUD-033). Comentário no arquivo justifica como limitação do Postgres, mas recriar o tipo é viável e padrão; `pass` é escolha consciente, não impossibilidade. `pg_trgm` extension confirmada em `20260309_taco_pgtrgm_source.py:20`. **Surpresa do plano § F.2**: `MealSource` enum (`MANUAL/TELEGRAM/WHATSAPP`) ainda tem `TELEGRAM` e `WHATSAPP` no model **E** no DB (verificado via `pg_enum`); 0 hits em `grep -rn "MealSource\.TELEGRAM\|MealSource\.WHATSAPP"` no backend; tabela `meals` vazia (não há dados legados). Dead schema da era de integrações Telegram/WhatsApp — AUD-034 (🟢 baixa). Bônus: `20260320_fix_search_text_taco.py` é migração de dados com partial revert documentado ("não reintroduzimos linhas Open Food Facts removidas") — defensável, sem achado.

## PASSO 7.4 — Pool sizing e conexões

- **Início:** 2026-05-10 21:18
- **Fim:** 2026-05-10 21:25
- **Comando(s) executado(s):** `cat backend/app/core/database.py` (verifica `pool_size=10, max_overflow=20, pool_pre_ping=True`); `grep -nE "uvicorn|--workers" backend/Dockerfile docker-compose*.yml`; `psql -c "SHOW max_connections; SHOW shared_buffers"`
- **Artefato(s):** nenhum (matriz embutida em `06-banco.md § F.3`)
- **Achados gerados:** AUD-035, AUD-036
- **Commit:** ab7a13e
- **Notas:** Pool atual: 30 conn por processo (10 size + 20 overflow). Prod: 2 uvicorn workers + 1 celery worker (concurrency default cpu_count) + 1 beat → pode chegar a 120-210 conn em pico vs Postgres `max_connections=100`. Hoje não acontece (1 usuário, baixíssima carga), mas é arquitetural — qualquer escala estoura. Fix curto: reduzir pool por processo OU introduzir PgBouncer (escolha padrão da indústria). Bônus identificado: event listener `db_logger.info` em `after_cursor_execute` registra TODA query em INFO, sem gate de env (AUD-036) — em escala 5-10k linhas/min só de log. Quick fix: trocar `info` por `debug`. Plano § F.4 (auditar `await db.refresh()` em services) **não foi coberto** — sem evidência de bug, sem achado criado por ora. Sem achados em `expire_on_commit=False` e `pool_pre_ping=True` (corretos).

## PASSO 7.5 — Backup e disaster recovery

- **Início:** 2026-05-10 21:28
- **Fim:** 2026-05-10 21:35
- **Comando(s) executado(s):** `grep -in "backup\|pg_dump\|cron\|restore" scripts/*.sh docs/deploy.md docs/setup.md docker-compose*.yml`; `grep -in "backup\|disaster\|restore" Roadmap.md README.md docs/architecture.md`; leitura de `docs/deploy.md:1-35` + `Roadmap.md § 9.2`
- **Artefato(s):** nenhum (matriz embutida em `06-banco.md § F.5`)
- **Achados gerados:** AUD-037
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** Backup é **inteiramente manual** hoje. `docs/deploy.md:306-321` documenta `pg_dump` e oferece uma dica de cron numa blockquote, mas `scripts/setup-server.sh`/`deploy.sh` não automatizam nada (0 hits para `backup\|pg_dump\|cron`). Sem offsite, retenção, ou procedimento de restore. **Sistema não está em produção** ainda (Roadmap § 9.2 todo aberto, item específico de backup também `[ ]`) — por isso severidade é 🟠 alta, não 🔴 crítico. **Mas escala para 🔴 no instante do primeiro deploy** — refeições/peso/hidratação são dados de saúde irreplicáveis. Plano mínimo de release: cron `pg_dump|gzip` em `setup-server.sh` + sync offsite (Hetzner Storage Box ou rclone) + retenção 30d local/90d offsite + seção Restore em `deploy.md` + teste de restore em staging. **Encerra Frente F** com 8 achados (1 alto + 4 médios + 4 baixos), considerando AUD-029 que veio do PASSO 6.5.
