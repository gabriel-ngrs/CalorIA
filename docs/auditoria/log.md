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
- **Commit:** a3f76b2
- **Notas:** Backup é **inteiramente manual** hoje. `docs/deploy.md:306-321` documenta `pg_dump` e oferece uma dica de cron numa blockquote, mas `scripts/setup-server.sh`/`deploy.sh` não automatizam nada (0 hits para `backup\|pg_dump\|cron`). Sem offsite, retenção, ou procedimento de restore. **Sistema não está em produção** ainda (Roadmap § 9.2 todo aberto, item específico de backup também `[ ]`) — por isso severidade é 🟠 alta, não 🔴 crítico. **Mas escala para 🔴 no instante do primeiro deploy** — refeições/peso/hidratação são dados de saúde irreplicáveis. Plano mínimo de release: cron `pg_dump|gzip` em `setup-server.sh` + sync offsite (Hetzner Storage Box ou rclone) + retenção 30d local/90d offsite + seção Restore em `deploy.md` + teste de restore em staging. **Encerra Frente F** com 8 achados (1 alto + 4 médios + 4 baixos), considerando AUD-029 que veio do PASSO 6.5.

## PASSO 8.1 — 🔴 CRÍTICO: credenciais em e2e

- **Início:** 2026-05-10 21:40
- **Fim:** 2026-05-10 21:48
- **Comando(s) executado(s):** `rg -n "***REMOVED***|gabrielnegreirossaraiva38@gmail" .`; `git log --all --full-history -p -- frontend/e2e/auth.spec.ts | grep -E "082405|gabrielnegreiros" | head -20`; `git remote -v`; `git log --oneline -- frontend/e2e/auth.spec.ts`
- **Artefato(s):** `docs/auditoria/artefatos/G1-creds.txt`
- **Achados gerados:** AUD-038 (🔴 crítica)
- **Commit:** b6e6e7b
- **Notas:** **Confirmado**: par email+senha real em `frontend/e2e/auth.spec.ts:37-38`. Email = `gabrielnegreirossaraiva38@gmail.com` (mantenedor confirmado via `%ae` do commit `4737257` de 2026-04-29). Senha `***REMOVED***` em texto claro. Repo público em GitHub (`https://github.com/gabriel-ngrs/CalorIA.git`) — `git log -p` extrai trivialmente. Outros testes no mesmo arquivo (linhas 27-29) já usam fixture (`TEST_EMAIL`/`TEST_PASSWORD`); só o "login com user existente" foi escrito com credencial direta. **Vetor primário**: password reuse — se `***REMOVED***` está em outros serviços (Google, banco, etc.), comprometimento se propaga. **Ações pós-auditoria** (4 etapas, ordem importa): (1) trocar a senha AGORA em todos os lugares onde está; (2) substituir por `process.env.E2E_LOGIN_*` + GitHub Actions secret; (3) `git filter-repo --replace-text` para remover do histórico + force-push; (4) `gitleaks-action` no CI + pre-commit hook. Status totais: críticos sobe para **2** (era 1).

## PASSO 8.2 — Auth flow review

- **Início:** 2026-05-10 21:52
- **Fim:** 2026-05-10 22:00
- **Comando(s) executado(s):** leitura de `backend/app/api/v1/auth.py` (105 linhas) + `app/core/security.py` (41) + `app/core/deps.py` (40) + `app/services/auth_service.py` (40) + `app/core/config.py` (66)
- **Artefato(s):** nenhum (matriz embutida em `07-seguranca.md § G.1`)
- **Achados gerados:** AUD-039 (🟠 alta)
- **Commit:** 431aff2
- **Notas:** **Auth bem desenhada** — checklist do runbook praticamente todo verde: HS256 (com `algorithms=[ALG]` lista evitando `alg=none`), access 30min/refresh 30d, refresh blacklisted após uso (Redis SETEX com TTL=remaining), token type validado nos 2 callers, `raise ... from None` nos 2 sites de credentials. **Único achado**: `SECRET_KEY` default = `"insecure-default-key-change-in-production"` sem validator de fail-fast (AUD-039). Se alguém esquecer a env em prod, JWTs ficam forjáveis com a string que está no próprio source. Fix simples: `model_validator(mode="after")` que falha se `APP_ENV != development AND SECRET_KEY == default OR len < 32`. Mesmo padrão de gap em `VAPID_*` (defaults vazios sem fail-fast — push falha silenciosamente). Anotações sem novo achado: (a) `_redis_client()` cria conexão por chamada (mesma issue do AUD-014); (b) `blacklist_token` engole exceções com warning — degradação silenciosa se Redis cai; (c) `decode_token` sem `leeway` para clock skew (irrelevante em 1 host). Status totais: altos sobe para **10** (era 9).

## PASSO 8.3 — Validação de inputs (DoS / overflow)

- **Início:** 2026-05-10 22:03
- **Fim:** 2026-05-10 22:08
- **Comando(s) executado(s):** `grep -rn "max_length\|StringConstraints" backend/app/schemas/`; `grep -rn ": str\b\|: str | None" backend/app/schemas/*.py | grep -v max_length`; leitura de `schemas/ai.py` (133 linhas) + `api/v1/ai.py:40-75` para confirmar uso (ou não-uso) de `meal_type`/`mime_type`
- **Artefato(s):** nenhum dedicado (cross-ref embutida em `07-seguranca.md § G.3`)
- **Achados gerados:** nenhum novo (AUD-009 e AUD-010 do PASSO 3.6 já cobrem)
- **Commit:** 406d08c
- **Notas:** **Cross-validação confirma AUD-009/010 ainda válidos**. `description` em `MealAnalysisRequest` (ai.py:28) **já tem** `Field(min_length=3, max_length=2000)` — runbook listava como gap, mas é falso positivo (provavelmente fixado entre escrita do plano e execução). **Observações sem novo achado**: (1) `mime_type: str` em `PhotoAnalysisRequest` deveria ser `Literal["image/jpeg",...]` — combinar no fix do AUD-009; (2) `meal_type` nas duas requests AI é **dead field** (analyze_meal/analyze_photo não passam para o parser; `_infer_meal_type` em context_builder deriva do texto). Smell de contrato, sem bug funcional. Fica registrado para limpeza no PR de AUD-009/010.

## PASSO 8.4 — Rate limit assessment

- **Início:** 2026-05-10 22:11
- **Fim:** 2026-05-10 22:17
- **Comando(s) executado(s):** `rg -n "rate_limit|slowapi|RateLimit|Limiter" backend/`; `grep -n "rate" Caddyfile`; `grep -n "middleware\|add_middleware" backend/app/main.py`
- **Artefato(s):** `docs/auditoria/artefatos/G4-rate-limit.txt`
- **Achados gerados:** AUD-040 (🟠 alta)
- **Commit:** ac6078f
- **Notas:** **Zero rate limit em qualquer camada**. Backend não tem `slowapi`/equivalente; Caddyfile sem diretiva. `main.py` registra só `CORSMiddleware` (linha 42) + `timing_middleware` (linha 52). Vetores concretos: `/auth/login` exposto a credential stuffing (combina com AUD-038), `/auth/register` a bot signup, `/ai/analyze-*` a abuso de tokens Groq (combina com AUD-013 — sem visibilidade de quem consome), `/notifications/unread-count` a polling abusivo (combina com AUD-031). Severidade 🟠 contextual: hoje 1 usuário, mas sistema é deployable e CLAUDE.md confirma intenção multi-user. Recomendação: `slowapi` Redis-backed com limites por categoria (5/min para login, 3/hora para register, 30/min/user para AI). Defesa em profundidade: `caddy-ratelimit` no edge + captcha em `/register` se virar público.

## PASSO 8.5 — Headers de segurança e CORS

- **Início:** 2026-05-10 22:20
- **Fim:** 2026-05-10 22:26
- **Comando(s) executado(s):** leitura completa de `Caddyfile` (57 linhas), `frontend/next.config.mjs` (19), `backend/app/main.py` (75)
- **Artefato(s):** nenhum (matriz embutida em `07-seguranca.md § G.8`)
- **Achados gerados:** AUD-041 (🟡 média)
- **Commit:** 888f51e
- **Notas:** **Caddy injeta HSTS automaticamente** quando HTTPS ativo via Let's Encrypt (`{$APP_DOMAIN}`) ✅. Demais headers de segurança ausentes em todas as 3 camadas (Caddy, Next, FastAPI): X-Frame-Options, X-Content-Type-Options, CSP, Referrer-Policy, Permissions-Policy. **CORS é defensivo por default**: `allow_origins` lê de `BACKEND_CORS_ORIGINS` (CSV); vazio = bloqueia tudo. Risco residual: se alguém setar `*` em prod com `allow_credentials=True`, ainda há especificação browser que rejeita, mas vale validator. Recomendação para AUD-041: bloco `header { }` no Caddyfile (entry único, cobre frontend+API simultaneamente). CSP inicial permissivo (`'unsafe-inline' 'unsafe-eval'` para Next dev) com aperto via nonces depois. `microphone=(self)` permitido pelo recurso de voice capture de refeições.

## PASSO 8.6 — Secret scan no histórico git

- **Início:** 2026-05-10 22:29
- **Fim:** 2026-05-10 22:34
- **Comando(s) executado(s):** `git log --all --full-history -p | grep -iE "(api_key|secret_key|password|token).*[=:].*[a-zA-Z0-9]{16}" | head -100`; `command -v gitleaks` (não instalado); `rg -n "SenhaForteAqui123" .`; `git log --all --full-history -- .env`; `cat .env.example`; `grep -n "\.env" .gitignore`
- **Artefato(s):** `docs/auditoria/artefatos/G6-secret-scan.txt`
- **Achados gerados:** nenhum novo (AUD-038 cobre o único segredo real, encontrado em PASSO 8.1)
- **Commit:** ffa3299
- **Notas:** **12 matches no regex, todos identificados**: 1 placeholder funcional (`POSTGRES_PASSWORD=SenhaForteAqui123!` em `docs/deploy.md` — risco de deployer copiar literal sem trocar) + 3 placeholders óbvios de Groq (`gsk_...sua_chave_aqui`) + 8 falsos positivos (identificadores TS NextAuth `setApiToken`/`accessTokenExpires`, schemas legados WhatsApp/Telegram). **`.env` nunca foi commitado** (`git log -- .env` → 0 hits) e está em `.gitignore` (linhas 8-11). **Limitação importante**: o regex exige `[a-zA-Z0-9]{16}` — **não pega senhas curtas como `***REMOVED***` (AUD-038)** que tem só 8 chars + especiais. Por isso esse scan é complementar à busca direcionada do PASSO 8.1, não substituto. `gitleaks` ofereceria cobertura mais ampla; recomendação combinada com AUD-038 § (4) já contempla `gitleaks-action` no CI.

## PASSO 8.7 — Autorização horizontal

- **Início:** 2026-05-10 22:37
- **Fim:** 2026-05-10 22:43
- **Comando(s) executado(s):** `rg -n "/\{[a-z_]+_id\}|/\{[a-z_]+\}" backend/app/api/v1/ -A 12`; `grep -nE "^\s*@router\.(get|post|patch|put|delete).*\{" backend/app/api/v1/*.py`; `grep -nA 6 "def get_meal\|def update_meal\|def delete_meal\|def delete_meal_item" backend/app/services/meal_service.py`; `grep -nA 6 "def toggle\|def delete\b" backend/app/services/reminder_service.py`
- **Artefato(s):** `docs/auditoria/artefatos/G7-authz.txt`
- **Achados gerados:** nenhum (todos os 6 endpoints com path param filtram por `user_id` corretamente)
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** **6 endpoints com path param**: 4 em `meals.py` (`GET/PATCH/DELETE /meals/{meal_id}` + `DELETE /meals/{meal_id}/items/{item_id}`), 2 em `reminders.py` (`PATCH /reminders/{reminder_id}/toggle`, `DELETE /reminders/{reminder_id}`). Todos passam `user_id` ao service E o service usa cláusula `WHERE Model.id == X AND Model.user_id == user_id`. Caso especial: `delete_meal_item` filtra `item_id` em memória sobre a lista de items já restrita ao meal do user (carregada via `selectinload`) — defensivo correto. **Nenhum vetor de IDOR**. Cross-validação com PASSO 2.2 (4/47 endpoints sem auth eram todos legitimamente públicos): a defesa de autorização do projeto está consistente. **Encerra Frente G** com 4 achados (1 crítico + 2 altos + 1 médio).

## PASSO 9.1 — Investigar bug de fixture unit

- **Início:** 2026-05-11 (sessão atual)
- **Fim:** 2026-05-11 (sessão atual)
- **Comando(s) executado(s):** `cd backend && .venv/bin/pytest tests/unit/ -q | tail -30` (reprodução); `.venv/bin/pytest tests/unit/test_security.py::TestHashPassword::test_retorna_hash_diferente_da_senha` (trace completo de 1 teste); leitura de `tests/conftest.py` (129 linhas) + `tests/unit/conftest.py` (19 linhas).
- **Artefato(s):** `docs/auditoria/artefatos/H1-unit-fixture-error.txt`
- **Achados gerados:** AUD-042 (🟠 alta)
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** **Reproduzido**: `49 passed, 49 errors in 30.79s` — exatamente o padrão descrito no plano. **Causa raiz confirmada**: `tests/unit/conftest.py:12-18` sobrescreve só `setup_test_database` por stub no-op; o `clean_db` raiz (`tests/conftest.py:68-75`) continua `autouse=True` e tenta `TRUNCATE TABLE ... CASCADE` em `127.0.0.1:5432` após cada teste — `ConnectionRefusedError: [Errno 111]` (Postgres parado durante a auditoria) marca cada item como erro de teardown. O teste em si passa (asserts OK); pytest reporta dois eventos por teste, dobrando o sinal. **Impacto principal**: ruído em CI — exit code não-zero apesar dos testes funcionarem; bug clássico de erosão de confiança. **Bônus do diagnóstico**: o próprio stub atual já carrega dois `# type: ignore[override]/[misc]` apontando que `setup_test_database` está sendo cobertor curto; faz sentido cobrir `clean_db` da mesma forma. Recomendação detalhada (curto prazo: stub no-op de `clean_db`; médio prazo: remover `autouse=True` raiz e exigir via marker nos testes de integração) registrada em AUD-042 e em `08-testes.md § H.2`.

## PASSO 9.2 — Cobertura por área

- **Início:** 2026-05-11 (sessão atual)
- **Fim:** 2026-05-11 (sessão atual)
- **Comando(s) executado(s):** leitura de `artefatos/baseline-coverage.txt` (capturado no PASSO 1.4) — coverage report por arquivo; tabulação e classificação por banda (< 50% / 50-65% / ≥ 80%).
- **Artefato(s):** nenhum novo (usa `baseline-coverage.txt`; matriz consolidada em `08-testes.md § H.3`)
- **Achados gerados:** AUD-043 (🟠 alta)
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** Total **62%** (2512 stmts, 942 missing). **10 módulos críticos < 50%**: `workers/celery_app.py` (0%), `services/ai/insights_generator.py` (14%), `services/ai/context_builder.py` (20%), `services/ai/pattern_analyzer.py` (27%), `services/push_service.py` (29%), `services/reminder_service.py` (31%), `workers/tasks/reports.py` (32%), `api/v1/ai.py` (36%), `services/ai/food_lookup.py` (41%), `services/ai/ai_client.py` (43%). 12 outros em zona cinzenta (50-65%). Áreas bem cobertas: schemas (100%), models (~95%), `nutrition/tdee.py` (100%), `core/security.py` (100%). **Padrão consistente**: o "buraco" da cobertura é o **núcleo IA + push + workers** — código com efeitos colaterais que é difícil de testar e que mais quebra silenciosamente. Combina mal com AUD-013 (logs sem dimensões) — sem cobertura nem observabilidade, regressões só aparecem quando o usuário reclama. Recomendação em 3 ondas: Onda 1 (food_lookup, meal_parser, vision_parser, ai_client, auth_service para ≥ 70%) + `--cov-fail-under=70` em CI; Onda 2 (context_builder, pattern_analyzer, push_service+fakeredis, reminder_service) + 75%; Onda 3 (insights_generator pós-decomposição AUD-002) + 80%. Property-based (Hypothesis) para tdee/correct_calories/extract_json. Snapshot tests para prompts de context_builder.

## PASSO 9.3 — Áreas críticas sem teste

- **Início:** 2026-05-11 (sessão atual)
- **Fim:** 2026-05-11 (sessão atual)
- **Comando(s) executado(s):** bloco `ls app/services/ai/*.py + ls app/services/*.py + ls tests/unit/test_*.py + ls tests/integration/test_*.py` redirecionado para artefato; cruzamento manual com cobertura do PASSO 9.2.
- **Artefato(s):** `docs/auditoria/artefatos/H3-test-coverage.txt`
- **Achados gerados:** nenhum novo (a lista de gaps consolidada em § H.4 alimenta o plano de AUD-043 — Onda 1/2/3 — sem precisar de novo achado)
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** **AI (8 arquivos)**: ✅ unit em `meal_parser` e `vision_parser`; ⚠️ smoke-only em `ai_client`; ❌ ausente em `food_lookup` (🟠 — coração da precisão; absorve AUD-016/AUD-006), `context_builder` (🟠 — prompts, CC D(25)), `insights_generator` (🟠 — 184 stmts, 14%; AUD-002), `pattern_analyzer` (🟡). `utils.py` coberto transitivamente — mas `extract_json_from_ai_response` precisa de teste dedicado para fechar AUD-017. **Services raiz (8 arquivos)**: nenhum tem unit test direto; cobertura vem só de integration (test_auth, test_users, test_meals, test_dashboard, test_logs). Gaps 🟡: `auth_service` (blacklist Redis), `push_service` (410 handling), `reminder_service`. **Workers**: `maintenance.py` (82% ✅), `reminders.py` (56% 🟡 — TZ AUD-026 e hardcode 2000 AUD-027 sem regressão test), `reports.py` (32% 🟠 — 114 stmts, duplica push 410). Ações concretas para PR de cobertura: adicionar `fakeredis>=2.20` à deps de dev; criar `tests/unit/test_food_lookup.py` com 50-100 alimentos populares; `test_context_builder.py` com snapshot de 3 personas; `test_ai_client.py` mockando `groq.AsyncGroq` (cache hit/miss, 429, 503, 401).

## PASSO 9.4 — E2E: BASE_URL e credenciais

- **Início:** 2026-05-11 (sessão atual)
- **Fim:** 2026-05-11 (sessão atual)
- **Comando(s) executado(s):** leitura de `frontend/playwright.config.ts` (26 LOC) + `e2e/auth.spec.ts` (43) + `e2e/dashboard.spec.ts` (66) + `e2e/meals.spec.ts` (72).
- **Artefato(s):** nenhum (matriz embutida em `08-testes.md § H.6`)
- **Achados gerados:** AUD-044 (🟠 alta)
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** **Inconsistência grave entre suites**: `playwright.config.ts:15` define `baseURL: "http://localhost:3000"` (+ `webServer: npm run dev`). `auth.spec.ts:3` cria constante local `BASE_URL = process.env.BASE_URL ?? "https://frontend-nine-mu-59.vercel.app"` — **ignora completamente** o config e cai em Vercel preview pública sem env var. `dashboard.spec.ts` e `meals.spec.ts` usam caminhos relativos e herdam corretamente (✅). Consequências: (1) o teste "deve cadastrar novo usuário" (linha 24-33) cria `playwright_test_<timestamp>@gmail.com` no banco de produção a cada execução local sem env vars; (2) o teste "login com user existente" (linhas 35-42) usa credenciais reais (AUD-038) contra produção — credential stuffing efetivo a cada run; (3) qualquer mudança de URL de preview quebra a suite sem regressão real no código. **Bug latente menor** (sem achado dedicado): linha 32 inclui `login` no matcher `toHaveURL(/(onboarding|dashboard|login)/)` — voltar pro login é considerado sucesso para "deve cadastrar e redirecionar". **Setup de usuário**: `auth.spec.ts` mistura uso real (Vercel) + mocks; `dashboard`/`meals` mockam tudo (`page.route` para `/api/auth/session` e `/api/v1/*`) — assertions superficiais (`not.toHaveURL(/login/)`), validam só navegação. Sem fixture global criando user via API. Plano: trocar constante por `process.env.E2E_BASE_URL ?? "http://localhost:3000"`; apertar matcher; criar `e2e/fixtures.ts` com registro via API. Combina com fix de AUD-038. **Encerra Frente H** com 3 achados (3 altos), totais agora em 14 altos.

## PASSO 10.1 — Detalhar erros ruff

- **Início:** 2026-05-11 (sessão atual)
- **Fim:** 2026-05-11 (sessão atual)
- **Comando(s) executado(s):** leitura de `artefatos/baseline-ruff.txt` (capturado em PASSO 1.1); tabulação por código/arquivo/linha/auto-fix.
- **Artefato(s):** nenhum novo (usa `baseline-ruff.txt`; tabela completa em `09-qualidade.md § I.1`)
- **Achados gerados:** AUD-045 (🟢 baixa, mas com gotcha funcional)
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** **14 erros, 9 auto-fixáveis.** Distribuição: 2 em `app/api/v1/meals.py` (I001 + B904 — esse último é o **mesmo** caso de AUD-004), 1 em `services/meal_service.py` (N818, sufixo `Error` em exception — estilístico), 11 em `scripts/` (utilitários one-shot). **Achado funcional disfarçado**: par F401(385) + F821(440) em `scripts/import_off_local.py` indica que `from sqlalchemy import text as sa_text` está dentro de uma função e `sa_text` é referenciado em outra função (`_flush()`) — `ruff --fix` cego remove o import e quebra o script em runtime. F821 já é a evidência. Recomendação: PR em duas frentes — corrigir 2 erros em `app/` (auto + manual com `from None`); para `scripts/`, mover o import para o topo do módulo antes do `--fix`, OU adicionar `extend-exclude = ["scripts/"]` em `[tool.ruff]` (alinha com exclusão já existente do mypy). N818 pode ficar pendente sem urgência.

## PASSO 10.2 — Detalhar warnings mypy

- **Início:** 2026-05-11 (sessão atual)
- **Fim:** 2026-05-11 (sessão atual)
- **Comando(s) executado(s):** leitura de `artefatos/baseline-mypy.txt` (capturado em PASSO 1.2); leitura de `app/services/ai/ai_client.py:60-150` para confirmar contexto dos 6 erros.
- **Artefato(s):** nenhum novo (usa `baseline-mypy.txt`; tabela em `09-qualidade.md § I.2`)
- **Achados gerados:** AUD-046 (🟢 baixa, mas com sinergia forte com AUD-011 e AUD-014)
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** **6 erros, todos em 1 arquivo** (`ai_client.py`), 67 source files checked. Duas classes: (1) tipos do `messages` da Groq SDK (linhas 69, 79, 106) — `dict` literal não encaixa nos `TypedDict`s `ChatCompletion*MessageParam`; particularmente vision (linha 67) usa `content: list[dict]` que só `ChatCompletionUserMessageParam` aceita; (2) `aioredis.from_url` não-tipada (linhas 135, 143) + `no-any-return` derivado (136). Sinergia importante: **fix do AUD-014 (pool persistente Redis) elimina automaticamente 3 dos 6 erros** (135/136/143) — vale bundlear. Para tipos Groq, importar `TypedDict`s do SDK e anotar `messages: list[ChatCompletionMessageParam]` cobre os outros 3. Sem refator, alternativa é `# type: ignore` em 5 sites (anestesia o sintoma, alimenta AUD-011). Recomendação: bundlar no PR maior de refator de IA (AUD-002/AUD-015/AUD-016) — overhead zero.

## PASSO 10.3 — ESLint frontend

- **Início:** 2026-05-11 (sessão atual)
- **Fim:** 2026-05-11 (sessão atual)
- **Comando(s) executado(s):** leitura de `artefatos/baseline-eslint.txt` (capturado em PASSO 1.7) + `frontend/components/auth/Plasma.tsx:140-161` para confirmar contexto do warning.
- **Artefato(s):** nenhum novo (usa `baseline-eslint.txt`; análise em `09-qualidade.md § I.3`)
- **Achados gerados:** nenhum (1 warning de cosmética, sem entrada dedicada em `achados.md`; anotado para PR de cleanup frontend junto com AUD-022)
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** **1 warning, 0 errors.** `components/auth/Plasma.tsx:155` — regra `react-hooks/exhaustive-deps`: uso de `containerRef.current` dentro da cleanup do `useEffect` (linhas 151-157). O ref pode ter sido reassinado entre o setup e a cleanup; o código tenta `containerRef.current?.removeChild(canvas)` mas está envolto em `try { } catch {}` que mascara possível erro. Fix idiomático: snapshot `const container = containerRef.current` no início do effect e usar `container.removeChild(canvas)` na cleanup. Impacto real pequeno (componente só monta na rota `/login`, sem re-renders frequentes), mas como single warning do projeto vale corrigir para baseline 0 e habilitar `eslint --max-warnings=0` em CI. Sem achado dedicado — combina em PR genérico de "frontend cleanup" com AUD-022 (extração `useVoiceCapture`).

## PASSO 10.4 — Pre-commit hooks atuais

- **Início:** 2026-05-11 (sessão atual)
- **Fim:** 2026-05-11 (sessão atual)
- **Comando(s) executado(s):** `cat .pre-commit-config.yaml > docs/auditoria/artefatos/I4-precommit.txt`; inventário e cross-ref com gaps de outras frentes.
- **Artefato(s):** `docs/auditoria/artefatos/I4-precommit.txt`
- **Achados gerados:** AUD-047 (🟡 média, com cross-ref importante a AUD-038)
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** **8 hooks ativos em 2 repos**: `ruff` (com `--fix`) + `ruff-format` em `^backend/`; e o pacote `pre-commit-hooks` v5.0.0 (`trailing-whitespace`, `end-of-file-fixer`, `check-yaml`, `check-merge-conflict`, `check-added-large-files --maxkb=1000`, `no-commit-to-branch --branch main`). **4 gaps importantes**: (1) **mypy** ausente — typecheck só em CI; (2) **eslint** frontend ausente — único warning passou; (3) **tsc --noEmit** ausente — TS estrito só em CI; (4) **gitleaks** ausente — **vetor crítico**: AUD-038 (credenciais reais commitadas) teria sido bloqueado se houvesse secret scan. `no-commit-to-branch --branch main` ✅ protege main; `--no-verify` bypassa tudo (esperado). Cross-ref forte: fix de AUD-047 deve ser bundlado com AUD-038 no mesmo PR (adicionar gitleaks pre-commit + GitHub Actions + filter-repo da senha do histórico). Snippet YAML completo em § I.4.

## PASSO 10.5 — Dead code

- **Início:** 2026-05-11 (sessão atual)
- **Fim:** 2026-05-11 (sessão atual)
- **Comando(s) executado(s):** bloco `find __init__.py -size 0 + find -size 0 type f + uvx vulture app/ --min-confidence 70` redirecionado para artefato.
- **Artefato(s):** `docs/auditoria/artefatos/I5-dead-code.txt`
- **Achados gerados:** nenhum (todos os hits são falsos positivos esperados)
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** **Nenhum dead code real detectado.** Os 12 `__init__.py` vazios são marcadores padrão de pacote Python. Os 6 hits do vulture @ confidence 100% são todos parâmetros obrigatórios de listeners SQLAlchemy (`before_cursor_execute` e `after_cursor_execute` em `app/core/database.py` linhas 30/32/34/42/44/46) — assinatura ditada pela API. Convenção mais limpa: prefixar com `_` (`_cursor`, `_parameters`, `_executemany`) para silenciar vulture. **Dead code real já mapeado em outros achados**: AUD-034 (`MealSource.TELEGRAM`/`WHATSAPP` legado, dead schema) e AUD-027 (`user.water_goal_ml` ignorado pelo worker de hidratação, "dead read"). **Smell extra anotado sem achado**: pasta `app/services/reminders/__init__.py` é vazia e a lógica real está em `app/services/reminder_service.py` (raiz) — pacote planejado e nunca materializado, pode ser removido. Recomendação opcional: rodar `vulture --min-confidence 80` como check informativo após prefixar os 6 params com `_`.

## PASSO 10.6 — Dockerfiles

- **Início:** 2026-05-11 (sessão atual)
- **Fim:** 2026-05-11 (sessão atual)
- **Comando(s) executado(s):** leitura dos 4 Dockerfiles (`backend/Dockerfile`, `backend/Dockerfile.dev`, `frontend/Dockerfile`, `frontend/Dockerfile.dev`); `ls .dockerignore` em ambos diretórios (não existe); `grep HEALTHCHECK` em Dockerfiles e compose; `grep NEXTAUTH_SECRET` em CI/compose.
- **Artefato(s):** nenhum (matriz embutida em `09-qualidade.md § I.7`)
- **Achados gerados:** AUD-048 (🟡 média)
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** **Estrutura geral boa**. Backend Dockerfile prod: multi-stage builder + runtime, usuário `appuser` não-root, build deps separadas de runtime, cache de deps antes do código (✅); `--workers 2` no `uvicorn` reforça AUD-035 (pool 30 × 2 workers = 60 conexões, vs `max_connections=100`). Frontend Dockerfile prod: 3-stage (deps + builder + runner), Next.js standalone, usuário `nextjs:nodejs` UID 1001, `NEXT_TELEMETRY_DISABLED=1` (✅). **2 issues encontrados**: (1) **`.dockerignore` AUSENTE** em ambos backend/ e frontend/ — `COPY . .` arrasta `.venv`, `node_modules`, `.next`, `.git`, `.env` (potencial leak), caches e tests para imagem; AUD-048 cobre. (2) **`NEXTAUTH_SECRET=insecure-secret-change-in-production`** como ARG default no `frontend/Dockerfile:30` + `docker-compose.yml:89` propaga `${NEXTAUTH_SECRET:-insecure-secret-change-in-production}` para build arg — embute o default na imagem se a env de prod não tiver `NEXTAUTH_SECRET`. **Cross-ref AUD-039**: padrão idêntico ao backend `SECRET_KEY` default; o fail-fast recomendado em AUD-039 deve ter contraparte no `next.config.mjs`. Sem novo achado dedicado — registrado em § I.7 como extensão de AUD-039. **Pequenas anotações sem achado**: backend Dockerfile poderia adicionar `ENV PYTHONUNBUFFERED=1` + `ENV PYTHONDONTWRITEBYTECODE=1`; HEALTHCHECK só no compose (não no Dockerfile) é padrão aceitável. **Encerra FASE 10** com 4 achados (1 médio + 3 baixos): AUD-045, AUD-046, AUD-047, AUD-048. Status totais agora: críticos 2, altos 14, médios 17, baixos 15.

## PASSO 11.1 — Logging atual

- **Início:** 2026-05-11 (sessão atual)
- **Fim:** 2026-05-11 (sessão atual)
- **Comando(s) executado(s):** `rg -n "logger = logging\.getLogger|logging\.basicConfig" backend/app/`; leitura de `backend/app/main.py` (75 LOC); inspeção de `backend/app/core/config.py` (campos disponíveis no `Settings`).
- **Artefato(s):** `docs/auditoria/artefatos/J1-loggers.txt`
- **Achados gerados:** AUD-049 (🟡 média)
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** **15 loggers nomeados**: 2 custom (`caloria.db`, `caloria.http`) + 13 via `__name__`. `logging.basicConfig(level=INFO, format="%(asctime)s %(levelname)s %(name)s | %(message)s", datefmt="%H:%M:%S")` em `main.py:14-18`. **Problemas mapeados**: (1) formato texto humano, não JSON — impossível agregar/filtrar por dimensão; (2) `LOG_LEVEL` hardcoded em INFO; `Settings` nem tem o campo, ajustar em prod exige redeploy; (3) sem `request_id` propagado via `contextvars` — logs do mesmo request não correlacionam; (4) `datefmt="%H:%M:%S"` sem data perde rastro de dia em logs 24h; (5) inconsistência `logger.info("%s", x)` vs `logger.info(f"...")` (formatação eager). **Bom sinal**: `getLogger(__name__)` em 12/14 módulos permite ajuste por namespace, o que mitiga AUD-036 sem deletar listener (basta `getLogger("caloria.db").setLevel(WARNING)`). **Cross-ref forte**: AUD-049 combina com AUD-013 (custo Groq por user invisível), AUD-027 (silêncio do hardcode água), AUD-028 (duplicação 410 não correlata), AUD-040 (abuso invisível sem rate limit + sem log estruturado). PR de instrumentação (structlog + request_id middleware + `LOG_LEVEL` settings + ruff G004) é M, 1-4h, mas desbloqueia 4 outros achados.

## PASSO 11.2 — Health check completeness

- **Início:** 2026-05-11 (sessão atual)
- **Fim:** 2026-05-11 (sessão atual)
- **Comando(s) executado(s):** leitura de `backend/app/main.py:72-74` (handler `/health`) + `:23-40` (lifespan e FastAPI version); `grep "version" backend/pyproject.toml`; `grep "^## " CHANGELOG.md`.
- **Artefato(s):** nenhum (matriz em `10-observabilidade.md § J.3`)
- **Achados gerados:** AUD-050 (🟡 média)
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** Handler `/health` é uma linha: `return {"status": "ok", "version": "0.1.0"}`. **3 gaps confirmados**: (1) sem readiness — não checa Postgres/Redis; container fica `healthy` mesmo com banco caído (compose dev:43 ratifica); (2) versão hardcoded `0.1.0` vs CHANGELOG `[0.7.0] - 2026-05-10` E vs `pyproject.toml:7` ainda em `0.1.0` (cross-ref PASSO 12.1 — coerência de versões); (3) `FastAPI(version="0.1.0")` em main.py:36 também desalinhado, OpenAPI reporta versão errada. **Inconsistência interna**: o lifespan (linhas 23-30) **já** executa `SELECT 1` no startup — conhecimento "DB ok" existe mas não é exposto. **Recomendação**: 4 itens em PR S: (1) versão via `importlib.metadata.version("caloria-backend")`; (2) separar `/health/live` (atual) e `/health/ready` (com `SELECT 1` + `redis PING`, retorna 503 se degradado); (3) `/health` como alias de `/health/live` (retrocompat); (4) apontar healthcheck do compose para `/health/ready`. Combina com AUD-014 (pool Redis persistente facilita ping) e com AUD-039 (validator SECRET_KEY pode usar mesmo lifespan).

## PASSO 11.3 — Sentry / APM

- **Início:** 2026-05-11 (sessão atual)
- **Fim:** 2026-05-11 (sessão atual)
- **Comando(s) executado(s):** `rg -l "sentry" /home/gabriel/projetos/CalorIA/ 2>/dev/null | grep -v node_modules` → artefato; `grep -nE "9\.3|sentry" Roadmap.md` para confirmar acknowledge do gap.
- **Artefato(s):** `docs/auditoria/artefatos/J3-sentry.txt`
- **Achados gerados:** AUD-051 (🟡 média)
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** **Zero instrumentação Sentry/APM** confirmada. Os 2 hits do `rg` são falsos positivos referenciais: o próprio runbook deste passo e um nome de alimento no CSV processado. Roadmap § 9.3 (`Roadmap.md:417-419`) tem os 3 itens da seção "Observabilidade" como `[ ]` — Sentry, health monitorado e logs estruturados. Logs estruturados já é AUD-049; health monitorado depende de AUD-050 (precisa de `/health/ready`); Sentry é o item que sobrou. **Pontos de dor concretos hoje**: (1) `groq.APIConnectionError` reaparecida no smoke test (PASSO 1.4) é re-elevada após 4 tentativas em `ai_client.py:122` sem alerta — pipeline IA quebra para usuário e equipe descobre por toast; (2) frontend sem nenhuma telemetria do que quebra para usuários em campo; (3) workers Celery (reminders, reports, maintenance) — falha só visível se alguém ler log, combina mal com AUD-026 (TZ latente). Plano (M, 1-4h): `sentry-sdk[fastapi,celery,sqlalchemy]` no backend gated por `settings.SENTRY_DSN`; `@sentry/nextjs` no frontend; tagging com `user_id` e `request_id` (cross-ref AUD-049); `release=APP_VERSION` (cross-ref AUD-050); sampling conservador (traces 10%, profiles 0% inicialmente). Beneficiários colaterais: AUD-013 (custo Groq via custom events), AUD-016 (food_lookup via profiling). Alternativa: GlitchTip self-hosted se Sentry-saaS for restritivo.

## PASSO 11.4 — Caddy

- **Início:** 2026-05-11 (sessão atual)
- **Fim:** 2026-05-11 (sessão atual)
- **Comando(s) executado(s):** leitura de `Caddyfile` (56 LOC) + `Caddyfile.backend` (22 LOC) + `docker-compose.backend.yml` (134 LOC) + `.github/workflows/cd.yml`; `git log -p -- Caddyfile.backend` para origem; `grep -rn "Caddyfile.backend\|docker-compose.backend"` para referências.
- **Artefato(s):** nenhum (matriz embutida em `10-observabilidade.md § J.5`)
- **Achados gerados:** AUD-052 (🟢 baixa) + AUD-053 (🟢 baixa)
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** **Funcionalmente o Caddy está bem**: HTTPS automático via Let's Encrypt através do envelope `{$APP_DOMAIN}`; `reverse_proxy` injeta `X-Forwarded-For`/`X-Forwarded-Proto` automaticamente; routing por `handle` é correto. **3 gaps complementares (AUD-052)**: `format console` (não JSON, combina com AUD-049); sem rate limit (combina com AUD-040); sem bloco `header { }` (AUD-041 já cobre). **Decisão pendente sobre 2 deployments (AUD-053)**: `Caddyfile` (56 linhas, full-stack frontend+backend, com `handle /api/auth/*` → `frontend:3000`) vs `Caddyfile.backend` (22 linhas, backend-only, sem catchall). **CD atual usa apenas o backend-only** (`cd.yml:33` → `docker-compose.backend.yml` → `Caddyfile.backend`); frontend está na Vercel (AUD-044 confirmou `frontend-nine-mu-59.vercel.app`). `docker-compose.yml` + `Caddyfile` full-stack continuam no repo mas não são deployados — pendência registrada como evidência sem prescrição forte. Recomendação suave para AUD-053: opção 1 (remover/renomear full-stack) reduz superfície; opção 2 (manter com README/ADR) mantém alternativa. **Encerra Frente J** com 5 achados (3 médios + 2 baixos): AUD-049, AUD-050, AUD-051, AUD-052, AUD-053. Status totais agora: críticos 2, altos 14, médios 20, baixos 17.

## PASSO 12.1 — Coerência das versões

- **Início:** 2026-05-11 (sessão atual)
- **Fim:** 2026-05-11 (sessão atual)
- **Comando(s) executado(s):** bloco `grep version` em `pyproject.toml`, `app/main.py`, `CHANGELOG.md` e `package.json` redirecionado para artefato.
- **Artefato(s):** `docs/auditoria/artefatos/K1-versions.txt`
- **Achados gerados:** AUD-054 (🟢 baixa, mas cross-ref forte com AUD-049/050/051)
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** **Dessincronia confirmada — 6 minor versions de gap**. `pyproject.toml`, `app/main.py:36` (FastAPI), `app/main.py:74` (`/health`), `frontend/package.json` todos em `0.1.0`; `CHANGELOG.md:14` em `[0.7.0] - 2026-05-10`. Hoje não quebra ninguém (não há publicação em PyPI/npm, nenhum monitoring ligado), mas vira problema imediato quando: (1) Sentry/APM entra em cena (AUD-051) — todos eventos agregam por release="0.1.0"; (2) UptimeRobot lê `/health` (AUD-050) — rollback por versão impossível; (3) bug report do usuário não correlaciona com commit. **Recomendação consolidada**: bumpar para `0.7.0` agora + substituir hardcode em `main.py` por `importlib.metadata.version("caloria-backend")` (combina com fix de AUD-050) + documentar workflow de release em CONTRIBUTING/ADR-007 (proposto em AUD-055). Alternativa robusta: `setuptools-scm` + git tags como fonte de verdade.

## PASSO 12.2 — ADR pendente

- **Início:** 2026-05-11 (sessão atual)
- **Fim:** 2026-05-11 (sessão atual)
- **Comando(s) executado(s):** `grep -nE "^## ADR-" docs/architecture.md`; `ls docs/adrs/` (não existe — todos os ADRs estão inline em `architecture.md`); leitura completa de ADR-002 e ADR-006 para comparação de qualidade.
- **Artefato(s):** nenhum (matriz em `11-dx-docs.md § K.1`)
- **Achados gerados:** AUD-055 (🟢 baixa)
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** **Premissa do runbook era falsa**: previa "criar ADR-006 sobre Groq", mas ADR-006 já existe (e cobre banco nutricional pg_trgm). O repo tem **8 ADRs** (001-008) inline em `docs/architecture.md`, cobertura estrutural boa. **Gap real**: ADR-002 (Groq) é "skinny" — descreve a decisão atual mas não registra alternativas (OpenAI, Anthropic, Ollama) nem trade-offs explícitos; ADR-003 (Web Push) tem mesmo padrão de "fato consumado sem racional"; ADR-006 (banco nutricional) é o melhor template — cita números (feijão carioca kcal, threshold 0.65, latência < 20ms). **ADRs propostos**: ADR-009 para AUD-053 (Vercel + Hetzner backend-only — registra o porquê de `docker-compose.backend.yml` ser canônico); ADR-010 para AUD-054 (workflow de release com sincronia CHANGELOG/pyproject/package.json); ADR-011 opcional para AUD-049/050/051 quando observabilidade for implementada. ADRs servem para decisões **tomadas**, não para backlog — adicionar à medida que cada AUD for atacado.

## PASSO 12.3 — Runbook operacional ausente

- **Início:** 2026-05-11 (sessão atual)
- **Fim:** 2026-05-11 (sessão atual)
- **Comando(s) executado(s):** `ls docs/` → artefato; `grep -niE "troubleshoot|runbook|incident|emergência|rollback|on-call"` em `deploy.md`, `deploy-checklist.md`, `setup.md`; leitura de `deploy.md:340-391` (seção Troubleshooting).
- **Artefato(s):** `docs/auditoria/artefatos/K3-docs-list.txt`
- **Achados gerados:** AUD-056 (🟡 média)
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** **Sem `docs/runbook-prod.md`**. O que há é a seção `## Troubleshooting` em `deploy.md` (linhas 352-391, 40 LOC) cobrindo 4-5 cenários básicos de Day 0: app não abre, 502, banco com erro, push não chega, reset com/sem dados. Cobertura razoável para colocar sistema no ar, **insuficiente** para incidentes específicos que outras frentes já mapearam: (1) Groq 429 persistente (AUD-012/-013); (2) Push 410 em massa (AUD-028); (3) Worker Celery travado (AUD-025/-026 — bugs latentes que viram silenciosos); (4) Restore Postgres (AUD-037); (5) Rotação de secrets (AUD-039); (6) Resposta a Sentry 5xx burst (AUD-051). **Padrão sugerido**: criar `docs/runbook-prod.md` com seções no formato canônico Sintoma/Verificar/Mitigação/Causa raiz; cada cenário cita os AUDs correspondentes (runbook = fix imediato; AUD = fix definitivo). Construção incremental: começar com Groq + Worker (maior probabilidade hoje). Snippet de cenário-modelo (Groq 429) em `11-dx-docs.md § K.1.b`. Acopla com AUD-049 (logs estruturados facilitam achar linhas do incidente), AUD-050 (`/health/ready` detecta degradação antes), AUD-051 (Sentry descobre, runbook responde).

## PASSO 12.4 — CONTRIBUTING e templates

- **Início:** 2026-05-11 (sessão atual)
- **Fim:** 2026-05-11 (sessão atual)
- **Comando(s) executado(s):** bloco `wc -l CONTRIBUTING.md + ls .github/ISSUE_TEMPLATE/ + ls .github/PULL_REQUEST_TEMPLATE.md + find .github -type f + wc -l README.md` redirecionado para artefato; leitura completa de `CONTRIBUTING.md` (103 LOC) e `.github/PULL_REQUEST_TEMPLATE.md` (24 LOC).
- **Artefato(s):** `docs/auditoria/artefatos/K4-contrib.txt`
- **Achados gerados:** AUD-057 (🟢 baixa)
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** **Cobertura geral muito boa**. `CONTRIBUTING.md` (103 LOC) tem Setup ordenado (4 passos com docker/alembic/pre-commit), fluxo (refer a `git-workflow.md`), testes, convenções de commit alinhadas com CLAUDE.md, estrutura. PR template (24 LOC) tem descrição + tipo + checklist (5 itens, incluindo "sem `.env` ou secrets" — bom proxy mental para AUD-038); 2 issue templates (bug_report, feature_request); dependabot.yml presente; ci.yml/cd.yml já analisados. **Único ponto desalinhado (AUD-057)**: `CONTRIBUTING.md:42` afirma "pre-commit roda ruff, mypy, eslint" — falso. PASSO 10.4 (AUD-047) confirmou que só `ruff`+`ruff-format` estão no `.pre-commit-config.yaml`. Documentação adiantada à implementação. **2 recomendações conforme prioridade**: Opção A — atualizar a linha 42 para refletir o estado (10 min); Opção B (preferível) — bundlar com fix de AUD-047 (adicionar mypy/eslint/gitleaks ao pre-commit), aí a documentação vira verdadeira sem editar. Pequenos pontos sem achado: CONTRIBUTING não menciona workflow de release (cross-ref AUD-054 — atualizar quando atacado); PR template pode ganhar item "se está corrigindo achado de auditoria, citar AUD ID" quando os AUDs começarem a virar PRs. **Encerra FASE 12 / Frente K** com 4 achados (1 médio + 3 baixos): AUD-054, AUD-055, AUD-056, AUD-057. Status totais agora: críticos 2, altos 14, médios 21, baixos 20.

## PASSO 13.1 — Reordenar achados.md por severidade

- **Início:** 2026-05-11 (sessão atual)
- **Fim:** 2026-05-11 (sessão atual)
- **Comando(s) executado(s):** script Python embutido em Bash que (1) parseia `achados.md` por blocos `### AUD-NNN`, (2) extrai severidade pela **primeira emoji** na linha `- **Severidade:**` (corrige caveats como "🟡 média (sobe para 🟠...)"), (3) extrai primeira letra do `- **Frente:**` (cobre "A" e também "C / F" em AUD-016), (4) ordena por (severidade, frente, id) e reescreve com cabeçalhos `## 🔴 Críticos (N)`, `## 🟠 Altos (N)`, etc.
- **Artefato(s):** nenhum (reorganização in-place)
- **Achados gerados:** nenhum (passo de consolidação)
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** 57 achados reorganizados. Cabeçalhos por severidade com contagem entre parênteses. Dentro de cada severidade: ordem por frente (A → K) depois por ID numérico. Atualizada a introdução de `achados.md` para refletir nova ordem (era "por ID", agora "por severidade") e adicionado `**total: 57**` à linha de status. **Caveats do script** (dois bugs corrigidos durante a execução): (a) primeira tentativa do regex de severidade picava emojis de qualquer parte da linha — entradas como AUD-047 ("🟡 média (mas sobe para 🟠...)") classificavam errado em 🟠; (b) regex de Frente exigia `[A-Z]$` (linha terminando) — AUD-016 com `Frente: C / F` falhava e caía em frente "Z" default. Ambos corrigidos antes da escrita final. Validação final: 🔴=2, 🟠=14, 🟡=21, 🟢=20 — soma 57, bate com o esperado e com o cabeçalho. Primeiro AUD em 🔴 agora é AUD-016 (Frente C) seguido de AUD-038 (Frente G) — ordem alfabética por frente.

## PASSO 13.2 — Escrever relatório preliminar

- **Início:** 2026-05-11 (sessão atual)
- **Fim:** 2026-05-11 (sessão atual)
- **Comando(s) executado(s):** redação direta de `relatorio-preliminar.md` consolidando dados de `log.md § Snapshot inicial`, `achados.md` (post-reorder), e síntese das 12 frentes.
- **Artefato(s):** `docs/auditoria/relatorio-preliminar.md` (substituído integralmente — antes era esqueleto de 28 LOC)
- **Achados gerados:** nenhum (passo de consolidação)
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** Relatório com 7 seções: (1) Visão geral com distribuição por frente; (2) Métricas baseline; (3) Top 10 achados de maior impacto (com critério: severidade primeiro, depois raio de impacto, depois esforço/valor); (4) Priorização em 4 ondas de fix; (5) Esforço total estimado (~150-200h, ~3 meses solo); (6) Referências cruzadas para todos os artefatos da auditoria; (7) Definition of Done com checklist das FASES. **Decisões importantes da redação**: (a) **Ondas, não fases** — agrupar PRs por sinergia operacional, não por ordem do runbook; Onda 1 (segurança + bug latente) bloqueia primeiro deploy; (b) **Bundling de achados em PR** — vários PRs combinam 3-5 AUDs com sinergia técnica (ex.: AUD-014+046+049 do pool Redis); (c) **Top 10** prioriza AUD-016 e AUD-038 como críticos mas também eleva AUD-026 (TZ latente, hoje funciona "por acidente") e AUD-039 (NEXTAUTH_SECRET default replicado entre frontend e backend); (d) Caveats explícitos: estimativas são para um dev solo, Onda 3 (refator IA) pode escalar se quebra do InsightsGenerator revelar acoplamentos. Frentes mais afetadas: G (3 críticos+altos), B (4 altos), E (3 altos); frentes em bom estado: A e H.

## PASSO 13.3 — Atualizar CHANGELOG e README

- **Início:** 2026-05-11 (sessão atual)
- **Fim:** 2026-05-11 (sessão atual)
- **Comando(s) executado(s):** edição direta de `CHANGELOG.md` (adição em `## [Não lançado]`) e `README.md` (adição de `docs/auditoria/` à árvore + nova seção "Documentação adicional" com link para o relatório).
- **Artefato(s):** nenhum novo
- **Achados gerados:** nenhum (passo de consolidação)
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** **CHANGELOG**: adicionada seção `### Documentação` sob `## [Não lançado]` com sumário da auditoria (57 achados, distribuição por severidade, links para relatório e achados). Texto curto, conforme convenção do Keep a Changelog. **README**: dois pequenos retoques — (a) `docs/auditoria/` adicionado à árvore do "Estrutura do Projeto" (linha 130-ish); (b) seção nova "Documentação adicional" antes de "Licença" com 4 bullets cobrindo architecture.md, setup.md, deploy.md e o relatório de auditoria. Mantém o README enxuto (linha-base 202 LOC, ficou 213). Caveat: README cita `Caddyfile` (full-stack) na árvore mas AUD-053 documentou que o ativo é `Caddyfile.backend` — não corrigido neste passo porque é decisão arquitetural pendente (ADR-009 proposto em AUD-055); fix será no PR que implementar AUD-053.

## PASSO 13.4 — Encerramento e handoff

- **Início:** 2026-05-11 (sessão atual)
- **Fim:** 2026-05-11 (sessão atual)
- **Comando(s) executado(s):** `git log --oneline | grep "docs(auditoria)" | wc -l` (= 63); `ls docs/auditoria/artefatos/ | wc -l` (= 49 — inclui 9 baselines + 36 artefatos por passo + 4 sub-arquivos); compilação dos contadores finais.
- **Artefato(s):** nenhum novo — seção `§ Encerramento` adicionada ao fim deste arquivo.
- **Achados gerados:** nenhum (passo final)
- **Commit:** _(preenchido após o commit deste passo)_
- **Notas:** Encerra FASE 13 e a auditoria como um todo. Próximo passo operacional: abrir PRs seguindo as **4 ondas de fix** descritas em `relatorio-preliminar.md § Priorização recomendada`. Onda 1 (segurança + bug latente) é bloqueante para o primeiro deploy com tráfego real.

## § Encerramento

- **Início da auditoria:** 2026-05-10 16:50 (PASSO 0.1)
- **Fim da auditoria:** 2026-05-11 (sessão atual)
- **Total de passos executados:** 47 (FASE 0 → FASE 13)
- **Total de commits:** 63 commits `docs(auditoria)` (do plano inicial à consolidação)
- **Total de achados registrados:** **57** (🔴 2 · 🟠 14 · 🟡 21 · 🟢 20)
- **Total de artefatos brutos:** 49 arquivos em `docs/auditoria/artefatos/` (baselines + saídas de ferramentas + EXPLAIN ANALYZE + diffs)
- **Próximos passos:** ver [`relatorio-preliminar.md § Priorização recomendada`](relatorio-preliminar.md) — 4 ondas de fix priorizadas, ~150-200h de esforço estimado para um desenvolvedor solo.

### Frentes em destaque

- **Mais afetadas (alta severidade):** G (segurança — 1 crítico + 2 altos), B (backend — 4 altos), E (workers — 3 altos), H (testes — 3 altos).
- **Em bom estado:** A (arquitetura — só refatorações), H (testes — gaps tratáveis), workers do compose dev healthchecks (✅), Caddy HTTPS automático (✅), CONTRIBUTING + templates (✅ com 1 desalinhamento documentado).

### Idempotência confirmada

Todos os passos foram desenhados como idempotentes (re-executar não corrompe estado). Se a auditoria precisar ser parcialmente re-rodada, basta:

1. `git log --oneline -10` para ver o último passo commitado.
2. Abrir este `log.md` e localizar a última entrada `## PASSO X.Y`.
3. Identificar o próximo PASSO no `runbook.md`.
4. Continuar a partir dele.

### Handoff

A auditoria está pronta para handoff:

- ✅ Todos os 47 passos do runbook executados.
- ✅ Cada passo tem entrada cronológica em `log.md`.
- ✅ Cada passo tem ao menos 1 commit semântico em PT-BR (sem mencionar IA, sem Co-Authored-By).
- ✅ `achados.md` consolidado e reordenado por severidade.
- ✅ `relatorio-preliminar.md` preenchido com Top 10, ondas de fix e estimativa de esforço.
- ✅ CHANGELOG e README citam a auditoria com links.
- ✅ `git status` limpo (apenas `backend/uv.lock` pré-existente e não-relacionado ao trabalho).
- ✅ Branch `dev` pronta para `git push origin dev` (58+ commits ahead da origin no início da auditoria; ~120 commits após).

**Próxima ação recomendada do mantenedor:**

1. Revisar `relatorio-preliminar.md § Top 10`.
2. Iniciar **Onda 1** com **AUD-038 (rotação de senha + remoção do código)** — não pode esperar PR review.
3. Em paralelo, abrir PR de **AUD-016** (fix S, ganho 70× em food_lookup) para mostrar valor imediato da auditoria.
4. Daí seguir o restante da Onda 1 como PRs separados.
