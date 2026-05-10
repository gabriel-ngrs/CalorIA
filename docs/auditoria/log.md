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
