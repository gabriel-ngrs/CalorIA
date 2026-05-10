# Plano de Auditoria Profissional — CalorIA

**Data:** 2026-05-10
**Escopo:** backend (FastAPI, ~5.700 LOC), frontend (Next.js 14, ~10.500 LOC), testes (~3.400 LOC), infraestrutura (Docker, CI/CD), documentação.
**Objetivo:** verificar arquitetura, boas práticas, segurança, performance, qualidade de testes e dívida técnica antes de evoluir o produto.

> Este é um **plano de auditoria** — descreve o que será verificado, com que método e quais sinais específicos foram pré-identificados durante o levantamento (ver `Anexo A`). A execução acontece em PRs separados, um por área/severidade.

---

## Sumário

1. [Metodologia](#1-metodologia)
2. [Mapa do que será auditado](#2-mapa-do-que-será-auditado)
3. [Frente A — Arquitetura](#frente-a--arquitetura)
4. [Frente B — Backend (FastAPI + SQLAlchemy)](#frente-b--backend-fastapi--sqlalchemy)
5. [Frente C — Pipeline de IA](#frente-c--pipeline-de-ia)
6. [Frente D — Frontend (Next.js + React)](#frente-d--frontend-nextjs--react)
7. [Frente E — Workers Celery e Web Push](#frente-e--workers-celery-e-web-push)
8. [Frente F — Banco de Dados e Migrações](#frente-f--banco-de-dados-e-migrações)
9. [Frente G — Segurança](#frente-g--segurança)
10. [Frente H — Testes (unit, integração, e2e)](#frente-h--testes-unit-integração-e2e)
11. [Frente I — Qualidade de código e ferramentas](#frente-i--qualidade-de-código-e-ferramentas)
12. [Frente J — Observabilidade e operação](#frente-j--observabilidade-e-operação)
13. [Frente K — DX, documentação e contribuição](#frente-k--dx-documentação-e-contribuição)
14. [Cronograma sugerido](#14-cronograma-sugerido)
15. [Critérios de saída](#15-critérios-de-saída-definition-of-done)
16. [Anexo A — Achados pré-identificados](#anexo-a--achados-pré-identificados-snapshot-do-levantamento)
17. [Anexo B — Métricas de baseline](#anexo-b--métricas-de-baseline)
18. [Anexo C — Comandos e referências](#anexo-c--comandos-e-referências)

---

## 1. Metodologia

A auditoria é executada em **três passes complementares**:

| Pass | Foco | Ferramentas |
|---|---|---|
| **1. Estático** | Linting, type checking, dependency scan, complexidade | `ruff`, `mypy --strict`, `eslint`, `tsc --noEmit`, `radon`, `pip-audit`, `npm audit` |
| **2. Dinâmico** | Comportamento em runtime, queries, latência, cobertura | `pytest --cov`, `jest --coverage`, EXPLAIN ANALYZE, profiler do Postgres, Lighthouse |
| **3. Manual** | Revisão de design, fluxos críticos, código-chave | Leitura linha-a-linha de áreas pré-mapeadas |

Cada achado vai para uma planilha (`docs/auditoria/achados.md`, criada na execução) com:
- **ID** (ex.: `BACK-007`)
- **Severidade**: 🔴 crítica · 🟠 alta · 🟡 média · 🟢 baixa
- **Frente** (A–K)
- **Arquivo:linha**
- **Descrição** + evidência
- **Recomendação** com snippet do fix sugerido
- **Esforço estimado** (S < 1h · M 1-4h · L > 4h)

**Severidade — critérios objetivos:**
- 🔴 Crítica: vulnerabilidade explorável, perda de dados, downtime, segredo exposto.
- 🟠 Alta: bug funcional reproduzível, regressão de performance > 2×, débito que bloqueia features.
- 🟡 Média: code smell impactante, falta de teste em caminho crítico, inconsistência de contrato.
- 🟢 Baixa: estilo, naming, comentário desatualizado, microoptimização.

---

## 2. Mapa do que será auditado

```
backend/
├── app/main.py                  # bootstrap FastAPI, CORS, lifespan, middleware HTTP
├── app/core/                    # config (Pydantic Settings), database, security (JWT/bcrypt), deps
├── app/api/v1/                  # 11 routers REST → todos serão revisados
├── app/models/                  # 11 modelos SQLAlchemy + relationships
├── app/schemas/                 # 8 módulos Pydantic v2 (request/response)
├── app/services/                # 8 services + ai/ (8 módulos) + nutrition/ + reminders/
├── app/workers/                 # celery_app + 3 módulos de tasks
└── alembic/versions/            # 11 migrações

frontend/
├── app/(auth)/                  # login, register
├── app/(dashboard)/             # 11 páginas (refeicoes 1055 LOC, insights 611, relatorios 548)
├── app/api/auth/[...nextauth]/  # NextAuth com refresh proativo
├── components/                  # ui/ (shadcn), dashboard/, charts/, layout/, auth/
├── lib/api.ts                   # axios + cache de token + retry 401 transparente
├── lib/hooks/                   # 8 hooks React Query
└── public/sw.js                 # service worker para Web Push

testes/
├── backend/tests/unit/          # 5 arquivos, 49 passes, 49 errors (DB stub mismatch)
├── backend/tests/integration/   # 5 arquivos com httpx + Postgres real
└── frontend/__tests__/ + e2e/   # 7 unit (hooks/utils), 3 e2e (Playwright)

infraestrutura/
├── docker-compose.yml + dev.yml # postgres 16, redis 7, backend, frontend, celery worker+beat, caddy
├── .github/workflows/ci.yml     # lint + test + build (push dev / PR main)
├── .github/workflows/cd.yml     # deploy SSH em merge para main
├── Caddyfile, Caddyfile.backend # reverse proxy HTTPS
└── Makefile                     # 30+ alvos para dev/test/deploy
```

---

## Frente A — Arquitetura

**Objetivo:** confirmar que a separação de camadas está sendo respeitada e que o domínio escala para multi-usuário.

### A.1 Separação de camadas

- [ ] Endpoints (`api/v1/*.py`) chamam **apenas** services — não há query SQLAlchemy direta nos routers.
  - Verificar com: `rg "select\(|delete\(|update\(" backend/app/api/`
- [ ] Services orquestram **apenas** modelos e outros services — não conhecem schemas de request (só response/domínio).
- [ ] Schemas são puros Pydantic — sem regras de negócio.
- [ ] Modelos SQLAlchemy não chamam services (sem ciclo).

### A.2 Coerência do domínio

- [ ] **Multi-tenancy ready**: toda query crítica filtra por `user_id`. Mapear e listar todos os pontos onde `user_id` está implícito.
- [ ] Relacionamentos com `cascade="all, delete-orphan"` consistentes em todos os modelos.
- [ ] FKs com `ondelete=` apropriado (CASCADE para owned, SET NULL para referencial).
- [ ] Sem `MealSource.TELEGRAM`/`WHATSAPP` mortos no enum (limpar em PR de migração — atualmente ainda existem em `models/meal.py:32`).

### A.3 Responsabilidade dos services

Auditar cada service contra "Single Responsibility":

| Service | LOC | Responsabilidade declarada | Risco |
|---|---|---|---|
| `MealService` | 165 | CRUD + agregação | OK |
| `LogService` | 143 | Weight + Hydration + Mood (3 classes) | 🟡 considerar separar arquivos |
| `DashboardService` | 67 | Compõe outros services | OK |
| `InsightsGenerator` | **511** | 6 prompts diferentes em uma classe | 🟠 candidato a quebrar em estratégias |
| `MealParser` | 273 | 2 estágios: identify + lookup/fallback | OK (duplica estrutura com `VisionParser`) |
| `VisionParser` | 280 | Idem para fotos | 🟡 90% duplicado com MealParser |

### A.4 Fluxos transversais

- [ ] Mapear quem orquestra a **transação** (commit/rollback) em cada operação. Hoje cada service faz `await self.db.commit()`. Avaliar mover para um *unit-of-work* no router (consistência cross-service).
- [ ] Auditar pontos onde múltiplos services compartilham a mesma `AsyncSession` — risco de commit prematuro.

**Entregável:** `docs/auditoria/01-arquitetura.md` com diagrama de dependências entre services.

---

## Frente B — Backend (FastAPI + SQLAlchemy)

### B.1 Configuração e bootstrap

- [ ] `config.py`: `SECRET_KEY` tem default inseguro (`"insecure-default-key-change-in-production"`). Em produção, falhar fast se igual ao default.
- [ ] `main.py`: middleware HTTP loga **todas** as requests com `print` — verificar se está em INFO mas com filtros razoáveis para produção (rate de log).
- [ ] Lifespan: warm-up só faz `SELECT 1`. Considerar pré-aquecer cache de food lookup (top 100 alimentos).
- [ ] `cors_origins` aceita string vazia → `[]` → tudo bloqueado em desenvolvimento. Documentar.

### B.2 Routers (`api/v1/*.py`)

Para **cada router**, validar:

| Critério | Como verificar |
|---|---|
| Status codes corretos (201 para create, 204 para delete, 422 para validação) | Leitura |
| `response_model=` em todos os endpoints públicos | `rg "@router\.(get|post|patch|put|delete)" sem response_model` |
| Paginação consistente (skip/limit) com bounds (`ge`/`le`) | Leitura |
| Filtros documentados via Pydantic ou Query | Leitura |
| `HTTPException` levantadas com `from exc` para preservar traceback | `rg "raise HTTPException" -A1` |
| Docstrings com exemplo curto para cada endpoint | Auditoria visual |
| `B904` (sem `from exc`) — já flagado em `meals.py:101` | ruff |

**Achados pré-identificados:**
- 🟡 `dashboard.py:46` — import de `from datetime import timedelta` dentro da função (preguiça circular ou esquecimento? Pode mover para topo).
- 🟡 `users.py:30-44` — atualização de campos do `User` faz `setattr` direto. Não chama service. Se aparecer auditoria de campo (created_at, etc.) vai pular hooks. Mover para `UserService.update`.
- 🟡 `push.py:147-149` — `from sqlalchemy import func as sa_func` dentro da função. Limpar.
- 🟡 `push.py:193` — `from sqlalchemy import update` dentro da função. Limpar.

### B.3 Services

- [ ] Auditar **N+1**: `MealService.list_meals` usa `selectinload(Meal.items)` ✅. Conferir todos os outros lugares.
  - `context_builder._get_recent_meals_of_type` usa `selectinload` ✅
  - `dispatch_due_reminders` em `workers/tasks/reminders.py` faz `selectinload(Reminder.user)` ✅
- [ ] **Loops com queries**: já mapeado e corrigido em `MealService.get_macros_by_date_range` e `HydrationService.get_history`. Conferir `_send_hydration_reminders_async` que chama `HydrationService.get_day_summary` em loop por usuário (N queries).
- [ ] `MealService.create_meal` faz: `flush` → `add` items → `commit` → `refresh` → SELECT extra com `selectinload`. Possível otimização para `await self.db.refresh(meal, attribute_names=["items"])`.
- [ ] `MealService.delete_meal_item` carrega a meal inteira com items só para encontrar um item — `DELETE FROM meal_items WHERE id = :item_id AND meal_id IN (SELECT id FROM meals WHERE user_id = :user_id)` é uma query só.

**Padronização — `correct_calories`:**
- 🟠 `services/ai/utils.py:18` — assinatura `list` sem parametrização e `# type: ignore[type-arg]`. Tipar como `list[ParsedFoodItem]` ou usar `TypeVar`.
- 🟡 `MealItemNotFound` (`meal_service.py:15`) — ruff `N818` exige sufixo `Error`. Renomear para `MealItemNotFoundError`.

### B.4 Schemas (Pydantic v2)

- [ ] Verificar `model_config = {"from_attributes": True}` em **todos** os response schemas. (TokenResponse não precisa.)
- [ ] Field validators usados onde adequado (`UserCreate.strip_name` ✅).
- [ ] Inputs com `Field(...)` constraints (gt, min_length, max_length). Auditar `MealItemCreate` — quantidade não tem `gt=0`.
- [ ] **Discrepância contrato**: `auth.py:login` retorna `TokenResponse` (sem `user`), mas `frontend/app/api/auth/[...nextauth]/route.ts:64` lê `data.user?.id` e `data.user?.name` — bug ativo. Padronizar:
  - **Opção 1**: backend retornar também `user` no login (mais conveniente).
  - **Opção 2**: frontend chamar `/auth/me` após login (mais REST puro).

### B.5 Type checking strict

- [ ] Rodar `mypy --strict app/` e zerar warnings. Hoje há 12 `# type: ignore` espalhados.
- [ ] Substituir `# type: ignore[no-untyped-call, no-any-return]` em `auth_service._redis_client` por wrapper tipado.
- [ ] Tipar `_run` em workers (`Any` → `Coroutine[Any, Any, T]`).

---

## Frente C — Pipeline de IA

### C.1 `AIClient` (`services/ai/ai_client.py`)

- [ ] Verificar uso de `redis.asyncio.from_url(...)` em **context manager** — fecha conexão? Hoje sim (`async with`), mas há *connection leaks* se a função propagar exception antes do `__aexit__`. Considerar pool global.
- [ ] Cache: chave SHA-256 dos primeiros 24 hex chars — colisão 1 em 2^96, OK.
- [ ] Retry só em 429 (`if "429" in str(exc)`). Frágil — extrair status code do tipo de exception específico do SDK Groq.
- [ ] Retry 4 tentativas com 15s→30s→60s→120s — total ~3.75min. Em produção pode estourar timeout uvicorn (default 60s sem keepalive). Documentar e/ou alinhar.
- [ ] Tokens são logados via `logger.info` mas sem agregação — adicionar contador via Redis para monitorar free tier.

### C.2 `MealParser` e `VisionParser` (~550 LOC duplicado)

- [ ] **Refactor candidato**: extrair classe base `BaseParser` com `_lookup_and_fill`, `_estimate_macros_batch`, sanity check. Cada subclasse implementa só `_identify_foods`.
- [ ] Sanity check de 35% — magic number. Mover para constante nomeada com justificativa em comentário.
- [ ] Threshold de confiança 0.6 — duplicado em `meal_parser.py:103` e `vision_parser.py:98`.
- [ ] **Robustez do JSON parsing**: `extract_json_from_ai_response` aceita só array. Se a IA retornar `{"items": [...]}` quebra. Aceitar ambos os formatos.
- [ ] **Atwater + tolerância 10%**: `correct_calories` corrige se divergência > 10%. Validar com refeições reais — pode ser agressivo demais para alimentos com gordura alta (ovos, queijos).

### C.3 `FoodLookup` (`services/ai/food_lookup.py`)

- [ ] N-gramas de 1 a 4 palavras × por candidato → 1 query SQL cada. Refeição com texto longo (10 palavras) gera ~30 queries. Avaliar:
  - Single query com `array_agg` sobre n-gramas via `unnest`.
  - Ou usar `tsvector` + `ts_rank` em vez de pg_trgm.
- [ ] Threshold mínimo `0.18` para descartar lixo, `0.65` para match definitivo. Criar tabela de regressão com 100 alimentos populares para validar threshold.
- [ ] `_SOURCE_BOOST = {"taco": 1.40}` — explicitar no plano que outras fontes (USDA, OFF) têm boost 1.0.
- [ ] Função `_normalize` remove acentos e lowercase — confirmar que `search_text` no banco também está normalizado (em todas as migrações).

### C.4 `ContextBuilder` (`services/ai/context_builder.py`)

- [ ] 5 queries sequenciais por chamada (`UserService.get_by_id`, `cal_today`, `prot_today`, `food_rows`, `_get_meal_type_averages`, opcionalmente `_get_recent_meals_of_type`). Avaliar paralelizar com gather (cuidado: AsyncSession não é thread-safe; precisa de N sessions).
- [ ] Inferência de meal_type por keyword tem ordem dependente do dict — confirmar que `_MEAL_TYPE_KEYWORDS.items()` em Python 3.7+ preserva ordem de inserção.
- [ ] Edge cases: usuário sem perfil retorna "usuário sem histórico". Validar que IA não rejeita string sem contexto.

### C.5 `InsightsGenerator` (511 LOC)

- [ ] 6 métodos públicos: `daily_insight`, `weekly_insight`, `answer_question`, `suggest_meal`, `nutritional_alerts`, `goal_adjustment_suggestion`, `monthly_report`. Quebrar em estratégias separadas por tipo de insight (`InsightStrategy` ABC) reduz superfície.
- [ ] Vários prompts inline com f-strings — extrair para `prompts/` ou usar templates separados (testes unitários ficam mais simples).
- [ ] `monthly_report` calcula 4 semanas — verificar bordas (meses com 28-31 dias) e edge case de mês corrente incompleto.
- [ ] `suggest_meal` espera JSON — usar `extract_json_from_ai_response` (já usa `json.loads` direto, falha em markdown wrapper).

### C.6 `PatternAnalyzer`

- [ ] Agregação cliente-side de meals + moods — sem teste unitário hoje.
- [ ] Saída como `EatingPattern` schema — auditar campos opcionais vs obrigatórios.

### C.7 Determinismo dos prompts

- [ ] `temperature=0.1` para análise, `0.3` para chat (bom). Documentar.
- [ ] Confirmar que `system` prompt é sempre passado quando há expectativa de JSON estrito. Há risco de `extract_json_from_ai_response` falhar quando a IA "explica" antes do JSON.

---

## Frente D — Frontend (Next.js + React)

### D.1 Estrutura de páginas

- [ ] **Páginas grandes**: `refeicoes/page.tsx` (1055 LOC, 22 hooks), `insights/page.tsx` (611), `relatorios/page.tsx` (548). Quebrar em sub-componentes:
  - `MealList`, `MealRow`, `MealAddModal`, `MealEditModal`, `MealStatsSidebar` para `refeicoes`.
  - `InsightCard`, `InsightChat`, `InsightAlerts` para `insights`.
- [ ] `QuickAddModals.tsx` (657 LOC, 18 hooks, 4 disable de any) — mesmo problema, isolar SpeechRecognition em hook customizado `useSpeechRecognition`.
- [ ] Server Components vs Client Components: hoje **tudo é client**. Avaliar quais páginas podem ser server (estatísticas pré-calculadas).

### D.2 Hooks customizados (`lib/hooks/`)

- [ ] Padrão TanStack Query: `useQuery` para reads, `useMutation` com `onSuccess` invalidando cache. Consistente nos 8 hooks ✅.
- [ ] `staleTime`/`gcTime` definidos no provider global — verificar `app/providers.tsx`.
- [ ] `useCreateMeal.onSuccess` faz `data.items.reduce(...)` — se backend retornar items vazio, `.toFixed(0)` em `0` funciona. OK.
- [ ] Optimistic updates ausentes — refeições, peso, hidratação podem se beneficiar (`onMutate` + `onSettled`).

### D.3 Camada de API (`lib/api.ts`)

- [ ] Cache de token em memória + dedupe de `getSession()` — implementação cuidadosa ✅.
- [ ] `console.log`/`console.error` em produção — gate com `if (process.env.NODE_ENV !== 'production')` ou usar lib de log.
- [ ] Retry transparente em 401 — testar com mock para garantir que não loops infinito (`_retry` flag protege ✅).
- [ ] **Race condition pequena**: `_pendingSession` pode ficar pendente se `signOut` redirecionar — sem cleanup explícito. Pode causar memory leak em SPA longo.

### D.4 Auth (NextAuth)

- [ ] Login espera `data.user.id` que **não existe** no `TokenResponse` do backend. Corrigir contrato (ver B.4).
- [ ] `ACCESS_TOKEN_LIFETIME_MS` hardcoded em 29min — ler do backend (via header ou endpoint `/auth/config`).
- [ ] `refreshAccessToken` tem timeout 5s — ok.
- [ ] `error: "RefreshAccessTokenError"` tratado no interceptor ✅.
- [ ] **Detectar runtime Docker via `existsSync('/.dockerenv')`** — frágil em runtimes não-Docker (Kubernetes pods, Podman). Usar variável de ambiente `BACKEND_URL` obrigatória.

### D.5 Acessibilidade e UI

- [ ] Auditar com Lighthouse (`pnpm lhci autorun`) e axe-core.
- [ ] Componentes shadcn/ui têm Radix por baixo → ARIA OK.
- [ ] **Verificar foco visível** em `glass-card` com baixo contraste no dark mode.
- [ ] **Suporte a teclado** em modais customizados (`refeicoes` tem combos com `Cmd+Enter`).
- [ ] Contraste cor: `text-amber-400` em `bg-emerald-950` pode falhar WCAG AA.

### D.6 Performance

- [ ] Bundle analyze (`@next/bundle-analyzer`) — verificar lazy loading. Já existe `dynamic()` em `Calendar`.
- [ ] `next/image` para imagens (atualmente `<img>` com disable do lint em 3 lugares).
- [ ] `useMemo`/`useCallback` no `refeicoes/page.tsx` — auditar dependency arrays.
- [ ] Recharts no SSR — confirmar que está só em Client Components.

### D.7 Service worker e PWA

- [ ] `public/sw.js` — auditar ciclo de vida, escopo, eventos `push` e `notificationclick`.
- [ ] `manifest.ts` — ícones em todos os tamanhos (192, 512, maskable).
- [ ] **Update strategy**: como o SW é atualizado quando o app muda? Verificar versão.

### D.8 TypeScript strictness

- [ ] `tsconfig.json` — verificar `strict: true`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`.
- [ ] Eliminar uso de `any` (5 ocorrências em SpeechRecognition + 1 em `axios` config). Tipar com Web Speech API types.

---

## Frente E — Workers Celery e Web Push

### E.1 Bootstrap e configuração

- [ ] `celery_app.py`: `task_acks_late=True` ✅, `worker_prefetch_multiplier=1` ✅, `task_max_retries=3` ✅.
- [ ] Beat schedule cobre 6 tasks. Conferir se todos os módulos são realmente carregados (`include=[...]`).
- [ ] **Single point of failure**: Celery Beat é singleton. Garantir que apenas 1 instância roda em produção (Docker Compose já garante).

### E.2 Padrão `_run` em tasks

```python
def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)
```

- 🟠 `asyncio.get_event_loop()` é **deprecated desde Python 3.10** em contexto sem loop ativo. Substituir por `asyncio.run()` ou criar nova loop a cada task.
- [ ] Auditar todos os 3 módulos (`reminders.py`, `reports.py`, `maintenance.py`).

### E.3 `dispatch_due_reminders` (a cada 60s)

- [ ] Roda `SELECT * FROM reminders WHERE active=true` — sem filtro de horário no SQL. Para 1000 lembretes, traz todos a cada minuto. **Otimização**: filtrar `time IN (current_minute, current_minute-1)` no SQL.
- [ ] **Bug de timezone**: `datetime.now()` é naive. Se servidor estiver em UTC e usuário em America/Sao_Paulo, lembrete dispara 3h adiantado. `Reminder.time` é `Time` sem TZ. Precisa **definir TZ canônica** (provavelmente do `User`) e converter.
- [ ] **DST**: Horário de verão muda; evitar duplicação ou pulos.

### E.4 Push expirado (HTTP 410)

- [ ] Padrão duplicado em `reminders.py` (2 tasks) e `reports.py` (2 tasks): `try/except WebPushException` + delete por id. Extrair para `PushService.send_with_cleanup(user_id, title, body)`.
- [ ] `expired_ids: list[int] = []` é mutado em loop — corrida com flush concorrente da mesma session. Hoje tudo serial dentro do `async with`, OK, mas frágil se introduzir paralelismo.

### E.5 Hardcode de `2000ml`

- 🟠 `_send_hydration_reminders_async` usa `if summary.total_ml >= 2000`. **Ignora** `User.water_goal_ml` que existe no modelo. Usar `user.water_goal_ml or 2000`.

### E.6 `recalculate_tdee` e `cleanup_old_conversations`

- [ ] Critério "peso mudou ≥ 2 kg" — ler do código atual (`maintenance.py`) e validar threshold.
- [ ] Cleanup roda diário 3h — verificar índice `created_at` na tabela `ai_conversations` (caso contrário full table scan).

### E.7 Push Service

- [ ] `push_service.py:40` — `except Exception as ex:  # noqa: BLE001` é genuíno (precisa pegar tudo do `pywebpush`), mas perde-se contexto. Logar `traceback.format_exc()`.
- [ ] Função síncrona `send_push_notification_sync` rodada em `asyncio.to_thread` em workers. OK.

---

## Frente F — Banco de Dados e Migrações

### F.1 Schema

- [ ] **Índices ausentes** suspeitos:
  - `meals(user_id, date)` composto — atualmente só `user_id` e `date` separados, queries do dashboard combinam ambos.
  - `meal_items(meal_id, food_id)` — usado em `dashboard_service` para joins.
  - `ai_conversations(user_id, created_at)` — para query de cleanup.
  - `notifications(user_id, read, created_at)` — para `unread-count`.
- [ ] Confirmar via `EXPLAIN ANALYZE` em queries críticas.

### F.2 Migrações

- [ ] 11 migrations. Política de **migrações reversíveis** — todas têm `downgrade()`?
- [ ] `20260315_a1b2c3d4e5f6_web_push_notifications.py` remove campos de Telegram/WhatsApp ✅.
- [ ] **Migração para enum `MealSource`** — atualmente o enum ainda tem `TELEGRAM`/`WHATSAPP` no model `meal.py:32` (memória da época), mas foram removidos no fluxo. Auditar se o enum no banco já foi reduzido (ALTER TYPE) ou se valores antigos ainda existem como dados históricos.
- [ ] `pg_trgm` extension: confirmar `CREATE EXTENSION IF NOT EXISTS pg_trgm` em alguma migration inicial.

### F.3 Pool e session

- [ ] `database.py`: `pool_size=10, max_overflow=20, pool_pre_ping=True`. Para 1 usuário ok. Para 100 concurrent users com workers + celery worker + 4 uvicorn workers, total = ~120 conexões. Postgres default `max_connections=100`. **Risco em escala**.
- [ ] Event listener loga toda query (`db_logger.info`). Cuidado em produção: 1k queries/seg = 1k linhas de log/seg. Adicionar amostragem ou silenciar em INFO em produção.

### F.4 Transações

- [ ] `expire_on_commit=False` — bom para Async, mas exige `await db.refresh()` explícito. Auditar se todos os services seguem padrão.
- [ ] Sem uso de `db.begin()` explícito — implícito em cada `commit`. OK para casos simples.

### F.5 Backups e DR

- [ ] `Roadmap.md` 9.2 marca "Backups automáticos do PostgreSQL (cron diário)" como `[ ]`. Plano de backup é ítem crítico para deploy.

---

## Frente G — Segurança

### G.1 Autenticação

- [ ] JWT HS256 com `SECRET_KEY` único — adequado para um único processo. Multi-instância exige a mesma chave (já é via env).
- [ ] Access token 30min, refresh 30 dias — razoável.
- [ ] Refresh token rotation: `auth.refresh` invalida o anterior via `blacklist_token` ✅.
- [ ] `is_token_blacklisted` usa `r.exists` — OK, mas a chave armazena o token completo (200+ chars). Considerar SHA-256 do token como chave para reduzir uso de RAM no Redis.

### G.2 Senhas

- [ ] bcrypt via `passlib`. Verificar `cost factor` (default 12, ok).
- [ ] Política de senha: `min_length=8` ✅, mas sem requisitos de complexidade (uppercase/digito/símbolo). Considerar `zxcvbn` no frontend ou validador no backend.

### G.3 Inputs e validação

- [ ] Pydantic v2 valida tipos. Confirmar `EmailStr` em todos os campos de email.
- [ ] **Quantity sem `gt=0`** em `MealItemCreate` — permite negativo.
- [ ] `image_base64` em `analyze-photo` — validar tamanho (DoS por imagem gigante). Hoje sem limite.

### G.4 Autorização horizontal

- [ ] Toda query de "minhas refeições" filtra por `user_id` ✅. Auditar 100% dos services e endpoints.
- [ ] **Edge case**: `delete_meal` retorna 404 se não pertencer — bom. Confirmar mesmo padrão em weight/hydration/mood/reminders.
- [ ] `notifications/{id}/read` filtra por `user_id` ✅.

### G.5 Rate limiting

- [ ] **Ausente.** Para projeto pessoal hoje OK; antes de abrir multi-usuário, adicionar (ex.: `slowapi` para FastAPI).
- [ ] `/auth/login` e `/auth/register` precisam rate limit forte (brute force).

### G.6 Segredos

- [ ] `.env` no `.gitignore` ✅.
- [ ] **CRÍTICO 🔴**: `frontend/e2e/auth.spec.ts:40` contém senha real `***REMOVED***` e email `gabrielnegreirossaraiva38@gmail.com`. **Trocar a senha no app + remover do código + reescrever histórico** (ou ao menos remover do HEAD e trocar a senha).
- [ ] Pesquisar histórico do git por outros segredos (`git log -p | grep -iE "api_key|secret|password"`).

### G.7 CORS

- [ ] `BACKEND_CORS_ORIGINS` configurável via env ✅. Em produção, restringir a `https://seudominio.com.br` (não `*`).

### G.8 CSP / Headers de segurança

- [ ] Caddy + Next: confirmar headers `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `Content-Security-Policy`. `next.config.mjs` não os define hoje.

### G.9 Web Push security

- [ ] Endpoints de subscription protegidos por JWT ✅.
- [ ] VAPID keys: `VAPID_PRIVATE_KEY` no `.env` (recente). Documentar rotação se vazar.

### G.10 Dependency scan

- [ ] `pip-audit` no backend (já existe `pyproject.toml`).
- [ ] `npm audit` no frontend.
- [ ] Considerar Dependabot no repo (`.github/dependabot.yml`).

### G.11 Logs

- [ ] Garantir que **logs não vazam tokens, senhas, body completos**. Atualmente o middleware HTTP loga método+path+status — OK.

---

## Frente H — Testes (unit, integração, e2e)

### H.1 Estado atual

- 49 testes unit + 49 errors (todos em test_security/test_tdee/test_vision_parser por **falha de fixture**).
- 5 arquivos de integração (`test_auth`, `test_users`, `test_meals`, `test_dashboard`, `test_logs`).
- 7 arquivos unit + 3 e2e no frontend.

### H.2 Bug de fixture identificado

- 🟠 `tests/unit/conftest.py` cria fixture `setup_test_database` que é stub, mas o conftest raiz tem `clean_db(setup_test_database)` autouse que tenta `TRUNCATE TABLE meal_items, meals, ...` — falha porque tabelas não existem. Resultado: **todos os testes unit que não criam DB explicitamente (security, tdee, vision_parser) erram ao final**. Os testes em si passam (`49 passed`), mas o teardown explode (`49 errors`).
- **Fix**: ou rodar Base.metadata.create_all em unit conftest (lento), ou tornar o `clean_db` opt-in para testes que precisam (function-scoped `db` fixture pulando autouse).

### H.3 Cobertura

| Área | Cobertura atual | Meta auditoria |
|---|---|---|
| `app/services/` | A medir | ≥ 85% |
| `app/services/ai/` | meal_parser, vision_parser tem unit; insights, pattern_analyzer, food_lookup, context_builder **sem teste** | ≥ 70% |
| `app/api/v1/` | integration cobre auth, users, meals, dashboard, logs (5/11) | ≥ 80% das rotas |
| `app/workers/` | só `test_celery_tasks.py` (533 LOC — bom) | ≥ 60% |
| `frontend/components/` | MacroCards, MacroPieChart só | adicionar Sidebar, Navbar, NotificationBell |
| `frontend/lib/hooks/` | 6 dos 8 hooks ✅ | manter |
| E2E | 3 arquivos (auth, dashboard, meals) | adicionar peso, hidratação, perfil, lembretes |

Rodar `pytest --cov=app --cov-report=html` e definir thresholds em CI (`--cov-fail-under=80`).

### H.4 Áreas críticas sem teste

- 🟠 `food_lookup` — coração da precisão nutricional. **Imprescindível** ter testes de regressão com 50-100 alimentos populares e seus matches esperados.
- 🟠 `context_builder` — afeta qualidade dos prompts.
- 🟠 `insights_generator` — 511 LOC sem teste.
- 🟡 `auth_service.blacklist_token` — testar com mock Redis (fakeredis).
- 🟡 `push_service.send_push_notification_sync` — testar 410 handling.

### H.5 Tipos de testes a expandir

| Tipo | Status | Recomendação |
|---|---|---|
| Property-based (Hypothesis) | Ausente | Adicionar para `correct_calories`, `tdee` |
| Snapshot (prompts da IA) | Ausente | Snapshot dos prompts gerados — pega regressão de prompt |
| Contract (frontend ↔ backend) | Ausente | Schemathesis a partir do OpenAPI auto-gerado |
| Performance | Ausente | Locust ou k6 para `/dashboard/today` (pico de uso) |
| Mutation testing | Ausente | `mutmut` em `services/ai/utils.py` (lógica crítica) |

### H.6 E2E

- [ ] Configurar `BASE_URL` via env, **não hardcoded em Vercel** (`auth.spec.ts:3`). Padrão deveria ser `http://localhost:3000`.
- [ ] Remover credenciais do código (G.6).
- [ ] Adicionar fixture global Playwright que cria usuário de teste limpo via API antes de cada suite.

---

## Frente I — Qualidade de código e ferramentas

### I.1 Lint

- [ ] **14 erros pré-existentes ruff** (já mapeados em PR anterior):
  - `app/api/v1/meals.py:1` — I001 (import sort)
  - `app/api/v1/meals.py:101` — B904 (raise from)
  - `app/services/meal_service.py:15` — N818 (Exception sufixo Error)
  - `scripts/extract_off_brazil.py:27` — F401 unused import
  - `scripts/import_fatsecret.py:38, 58, 305` — I001 + UP
  - `scripts/import_off_local.py:51, 384, 385, 440` — F401 + B007
  - `scripts/normalize_foods.py:28, 235` — F401 + B007
  - `scripts/translate_foods.py:34` — F401
- [ ] Decisão: corrigir todos ou excluir `scripts/` do ruff (já é excluído do mypy).

### I.2 Type checking

- [ ] `mypy --strict app/` — zerar warnings (12 `# type: ignore` hoje).
- [ ] Habilitar `disallow_untyped_decorators` (alguns `@shared_task` precisam wrapper tipado).

### I.3 Frontend lint

- [ ] `next lint` — sem warnings em CI hoje. Manter.
- [ ] Adicionar regras adicionais: `@typescript-eslint/no-explicit-any` (forçar tipagem do SpeechRecognition).
- [ ] Adicionar `prettier` formal (hoje só Tailwind class sort por convenção).

### I.4 Pre-commit

- [ ] `.pre-commit-config.yaml` existe — auditar quais hooks estão ativos. Adicionar `mypy`, `eslint --max-warnings=0`, `secret-scanner` (gitleaks).

### I.5 Complexidade

- [ ] `radon cc backend/app -s -nc` — listar funções com complexidade > 10.
- [ ] Esperado: `_lookup_and_fill` em meal_parser/vision_parser (5 branches × sanity check), funções grandes em `insights_generator`.

### I.6 Dead code

- [ ] `app/services/reminders/__init__.py` — pasta vazia. Remover ou popular.
- [ ] `app/services/nutrition/__init__.py` — só TDEE; talvez expandir ou achatar.
- [ ] `vapid_private.pem` em `.gitignore` ✅.

### I.7 Dockerfiles

- [ ] Multi-stage builds em `backend/Dockerfile` e `frontend/Dockerfile` — auditar:
  - usuário não-root
  - `HEALTHCHECK` definido
  - layer caching (deps antes de copiar código)
  - `.dockerignore` cobre `.venv`, `node_modules`, `.next`

---

## Frente J — Observabilidade e operação

### J.1 Logging

- [ ] Loggers nomeados por módulo (`caloria.http`, `caloria.db`) ✅.
- [ ] **Estrutura JSON** ausente — produção ganha com `python-json-logger` para indexar campos.
- [ ] Sentry: `Roadmap.md` 9.3 marca como `[ ]`. Plano de instrumentação backend + frontend.

### J.2 Métricas

- [ ] Sem Prometheus/StatsD hoje. Roadmap não cobre.
- [ ] Mínimo viável: counter de chamadas Groq (tokens, hits, misses), counter de requests por status code.

### J.3 Health checks

- [ ] `/health` retorna `{"status": "ok"}` simples. Adicionar:
  - Postgres: `SELECT 1`
  - Redis: `PING`
  - Versão (ler de `pyproject.toml` ou env)
- [ ] Considerar `/readiness` separado de `/liveness`.

### J.4 Tracing

- [ ] Sem OpenTelemetry. Para projeto pessoal, low priority. Documentar.

### J.5 Caddy

- [ ] Auditar `Caddyfile` e `Caddyfile.backend`:
  - HTTPS forçado, HSTS
  - Logs estruturados
  - Reverse proxy headers (`X-Forwarded-For`)
- [ ] Caddyfile.backend / docker-compose.backend.yml — pendência de decisão (manter ou remover).

---

## Frente K — DX, documentação e contribuição

### K.1 Documentação

- [ ] README, CLAUDE.md, docs/ atualizados após migração para Groq ✅ (PR anterior).
- [ ] Faltam:
  - **Diagrama de sequência** do fluxo de análise de refeição (`docs/fluxos/05-analise-ia` é texto).
  - **Runbook**: o que fazer quando ai_client.GROQ_API_KEY estoura limite, quando push expira em massa, quando worker celery trava.
  - **ADR-006**: por que Groq sobre OpenAI/Anthropic/Gemini (custo, latência, free tier).

### K.2 Onboarding

- [ ] `docs/setup.md` — testar do zero em VM limpa. Cronometrar até "primeiro request 200".
- [ ] `make init` — auditar se cobre tudo (DB seed, migrations, VAPID).

### K.3 Contribuição

- [ ] `CONTRIBUTING.md` existe — auditar seções: code style, commit convention, PR template.
- [ ] Adicionar `.github/ISSUE_TEMPLATE/` e `.github/PULL_REQUEST_TEMPLATE.md`.

### K.4 Versionamento

- [ ] CHANGELOG segue Keep a Changelog ✅.
- [ ] Versão única em CHANGELOG (0.7.0). `pyproject.toml` ainda em `0.1.0`. Sincronizar.
- [ ] `version` em `app/main.py` health check (`0.1.0`) também desatualizada.

---

## 14. Cronograma sugerido

Total estimado: **~25-35 horas** distribuídas em 8 PRs.

| Sprint | Frentes | PRs | Esforço |
|---|---|---|---|
| **S1 — Críticos & quick wins** | G (segurança), I (14 ruff), B (B904) | PR1, PR2 | 4h |
| **S2 — Backend hygiene** | B (services + schemas + types) | PR3 | 6h |
| **S3 — IA + tests core** | C (refactor parsers), H (food_lookup tests) | PR4, PR5 | 8h |
| **S4 — Frontend split** | D.1 (refeicoes), D.4 (auth contract) | PR6 | 6h |
| **S5 — Workers & banco** | E (timezone, hardcode 2000ml), F (índices) | PR7 | 4h |
| **S6 — Observabilidade & docs** | J, K, ADR-006 | PR8 | 4h |

Cada PR fecha com:
- Achados resolvidos marcados na planilha.
- CI passando (ruff/mypy/eslint/pytest/jest).
- Cobertura mantida ou aumentada.

---

## 15. Critérios de saída (Definition of Done)

Auditoria considerada concluída quando:

- [x] `docs/auditoria/plano.md` (este documento) revisado e aprovado.
- [ ] `docs/auditoria/achados.md` populado e priorizado.
- [ ] **Zero achados críticos (🔴) abertos.**
- [ ] **Zero achados altos (🟠) abertos** ou plano explícito para os adiados.
- [ ] `ruff check .` passa sem warnings.
- [ ] `mypy --strict app/` passa sem warnings.
- [ ] `next lint` passa sem warnings.
- [ ] `pytest --cov=app --cov-fail-under=80` passa.
- [ ] `npm test -- --coverage` com threshold 70% configurado.
- [ ] `pip-audit` e `npm audit` sem CVEs altas/críticas.
- [ ] `docs/auditoria/relatorio-final.md` resume os ganhos: LOC removidos, cobertura +X%, bugs prevenidos, dívida quitada.

---

## Anexo A — Achados pré-identificados (snapshot do levantamento)

Lista enxuta de itens já visíveis sem rodar ferramentas — vão direto para `achados.md` quando a auditoria executar.

### Críticos 🔴
1. **`frontend/e2e/auth.spec.ts:40`** — credenciais reais hardcoded (email + senha do dono do projeto). Trocar senha + remover + auditar histórico git.

### Altos 🟠
2. **`frontend/app/api/auth/[...nextauth]/route.ts:64-67`** — login lê `data.user` que não existe no `TokenResponse` do backend. Corrigir contrato (B.4).
3. **`backend/app/workers/tasks/reminders.py:31` (`_run`)** — `asyncio.get_event_loop()` deprecated.
4. **`backend/app/workers/tasks/reminders.py:178`** — hardcode `2000ml` ignora `User.water_goal_ml`.
5. **`backend/app/workers/tasks/reminders.py:38`** — `datetime.now()` naive sem TZ vs `Reminder.time` — bug de fuso.
6. **N+1 latente** em `_send_hydration_reminders_async` — `HydrationService.get_day_summary` em loop por usuário.
7. **`backend/app/services/ai/insights_generator.py` (511 LOC)** — God class; quebrar em estratégias.
8. **`backend/tests/unit/conftest.py`** — fixture stub não impede `clean_db` autouse de tentar TRUNCATE em DB inexistente. Resultado: 49 errors em 49 passes.

### Médios 🟡
9. `app/services/meal_service.py:15` — `MealItemNotFound` deve ser `MealItemNotFoundError` (ruff N818).
10. `app/services/ai/utils.py:18` — `correct_calories(items: list)` sem parametrização.
11. `app/services/ai/meal_parser.py` ↔ `vision_parser.py` — `_lookup_and_fill` e `_estimate_macros_batch` 90% duplicados.
12. `app/api/v1/users.py:30-44` — atualização inline do User, deveria estar em `UserService.update`.
13. `app/api/v1/dashboard.py:46`, `push.py:147,193` — imports dentro de função.
14. `app/services/ai/food_lookup.py` — N queries pg_trgm por refeição (até 30); avaliar single query.
15. `app/api/v1/auth.py:101` — `raise HTTPException(...) from None` ✅ vs `meals.py:101` sem `from` (B904).
16. `frontend/app/(dashboard)/refeicoes/page.tsx` (1055 LOC) — quebrar em sub-componentes.
17. `frontend/components/dashboard/QuickAddModals.tsx` (657 LOC, 4 `any`) — extrair `useSpeechRecognition`.
18. **Pool DB**: `pool_size=10, max_overflow=20` total 30 × 4 workers + Celery = ~120 conexões; default Postgres `max_connections=100`.
19. `MealSource` enum ainda contém `TELEGRAM`/`WHATSAPP` em `models/meal.py:32` apesar dos bots removidos.
20. `_extract_candidates` gera n-gramas até 4 — texto longo pode gerar 30+ queries (food_lookup).
21. **Sem rate limit** em `/auth/login` e `/auth/register`.
22. **Sem teste** para `food_lookup`, `context_builder`, `insights_generator`, `pattern_analyzer`.
23. `backend/app/main.py` health endpoint hardcoded `version="0.1.0"` (desincronizado com CHANGELOG `0.7.0`).
24. `frontend/e2e/auth.spec.ts:3` — `BASE_URL` default é Vercel deploy, não localhost.

### Baixos 🟢
25. 5 `any` em SpeechRecognition handlers (Web Speech API tem types padrão).
26. `console.log` permanecem em produção (`lib/api.ts`, `app/providers.tsx`).
27. `_TRUNCATE_TABLES` string em conftest é frágil — usar `Base.metadata.sorted_tables` reverso.
28. `MealItem.unit` é `String(50)` sem enum — qualquer valor entra. Enum: `g`, `ml`, `un`, `colher_sopa`, etc.
29. `backend/app/services/reminders/` — pacote vazio.
30. `Caddyfile.backend` + `docker-compose.backend.yml` — origem incerta (decisão pendente).

---

## Anexo B — Métricas de baseline

Capturadas em 2026-05-10 para comparação pós-auditoria:

| Métrica | Valor |
|---|---|
| LOC backend (sem alembic, scripts, tests) | 5.708 |
| LOC frontend (sem mocks, tests, build) | 10.573 |
| LOC tests backend | 1.845 |
| LOC tests frontend | 1.553 |
| Total endpoints REST | ~50 (estimado, 11 routers) |
| Modelos SQLAlchemy | 11 |
| Migrações Alembic | 11 |
| Páginas frontend | 14 (auth + dashboard + onboarding) |
| Hooks customizados | 8 |
| Erros ruff (pré-auditoria) | 14 |
| `# type: ignore` no backend | 12 |
| `eslint-disable` no frontend | 12 |
| `any` no frontend (não-test) | 5 |
| Cobertura backend (a medir) | ? |
| Cobertura frontend (a medir) | ? |
| Páginas frontend > 500 LOC | 4 |
| Funções backend > 50 LOC (estimado) | a medir com `radon` |

---

## Anexo C — Comandos e referências

### Comandos da auditoria

```bash
# Lint backend
cd backend && uvx ruff check . && RUFF_CACHE_DIR=/tmp/r .venv/bin/python -m mypy --strict app/

# Lint frontend
cd frontend && npm run lint && npx tsc --noEmit

# Cobertura
cd backend && pytest --cov=app --cov-report=html --cov-report=term
cd frontend && npm test -- --coverage

# Análise de complexidade
cd backend && uvx radon cc app/ -s -nc
cd backend && uvx radon mi app/ -s

# Dependency scan
cd backend && uvx pip-audit
cd frontend && npm audit --audit-level=high

# Secret scan (histórico git)
git log --all --full-history -p | grep -iE "api_key|secret_key|password" | head

# Análise de bundle frontend
cd frontend && ANALYZE=true npm run build

# Performance Postgres
docker exec caloria_postgres psql -U caloria -d caloria_db \
  -c "EXPLAIN ANALYZE SELECT ... FROM meals WHERE user_id = 1 AND date = '2026-05-10';"
```

### Padrões de referência

- **Backend**: [FastAPI best practices](https://fastapi.tiangolo.com/tutorial/), [SQLAlchemy 2 async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- **Frontend**: [Next.js 14 App Router](https://nextjs.org/docs/app), [TanStack Query patterns](https://tkdodo.eu/blog/practical-react-query)
- **Segurança**: [OWASP ASVS 4.0](https://owasp.org/www-project-application-security-verification-standard/), [JWT best practices](https://datatracker.ietf.org/doc/html/rfc8725)
- **Testes**: [Testing Library principles](https://testing-library.com/docs/guiding-principles), [pytest fixtures](https://docs.pytest.org/en/stable/explanation/fixtures.html)
