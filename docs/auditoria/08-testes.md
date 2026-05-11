# Frente H — Testes

**Plano:** ver `plano.md` § Frente H.

## Achados desta frente

- AUD-042 — Fixture `clean_db` autouse trunca tabelas após cada teste unit, falhando porque o stub de unit não cria DB (🟠 alta).
- AUD-043 — Cobertura crítica abaixo da meta em 10 módulos (`insights_generator` 14%, `context_builder` 20%, `pattern_analyzer` 27%, `push_service` 29%, etc.) (🟠 alta).
- AUD-044 — `auth.spec.ts` ignora `baseURL` do `playwright.config.ts` e default aponta para Vercel preview pública (testes E2E batem em produção) (🟠 alta).

## Notas e contexto

### § H.2 Bug de fixture nos testes unit (reproduzido)

**Sintoma observado** (`cd backend && .venv/bin/pytest tests/unit/ -q`):

```
49 passed, 49 errors in 30.79s
```

Cada teste do diretório `tests/unit/` reporta **simultaneamente** `1 passed, 1 error` — o teste em si passa, mas o teardown do fixture `clean_db` aborta com `ConnectionRefusedError: [Errno 111] Connect call failed ('127.0.0.1', 5432)` quando Postgres não está disponível (artefato `H1-unit-fixture-error.txt`).

**Causa raiz** (sequência de fixtures):

1. `tests/conftest.py:51-60` define `setup_test_database` como fixture `scope="session", autouse=True` que abre conexão asyncpg, dropa tabelas, recria via `Base.metadata.create_all` e dá `yield`.
2. `tests/conftest.py:68-75` define `clean_db` como `autouse=True` (function-scoped) que depende de `setup_test_database` e executa `TRUNCATE TABLE meal_items, meals, weight_logs, ...` **após cada teste**.
3. `tests/unit/conftest.py:12-18` sobrescreve **apenas** `setup_test_database` por um stub que retorna sem tocar o banco. O comentário do arquivo afirma que isso permite "rodar sem infraestrutura Docker".
4. O override **não desabilita** `clean_db`. O autouse continua valendo para todos os testes do diretório `unit/`. Como o stub não criou tabelas (e nem há Postgres disponível), o `TRUNCATE` tenta conectar em `127.0.0.1:5432`, e a conexão é recusada → `ConnectionRefusedError`.

**Por que a UI do pytest mostra "1 passed, 1 error" por teste:** o erro acontece no teardown, depois do `yield`. O pytest contabiliza o teste como passado (a função de teste retornou sem erro) e gera um item separado de erro para o teardown da fixture. Dobra o sinal de ruído sem indicar bug funcional.

**Impacto:**
- 🟠 alta no sinal de CI: `pytest tests/unit/` sai com código não-zero, o que provavelmente já é tolerado por hábito no projeto (testes "passam" mesmo) — bug clássico de erosão de confiança em CI.
- Sem custo funcional hoje porque os 49 testes não dependem de DB; mas qualquer teste unit que **realmente** precisar de session DB no futuro vai herdar o engano (acreditar que `clean_db` funciona quando na verdade só erra silenciosamente).
- Bloqueia a integração com `mypy --strict`: `tests/unit/conftest.py` precisa de `# type: ignore[override]` e `# type: ignore[misc]` na função stub (linhas 13 e 18) porque o tipo de retorno do override (`None`) diverge do original (`AsyncGenerator[None, None]`).

**Recomendação curta** (esforço S, < 1h):

Em `tests/unit/conftest.py`, também sobrescrever `clean_db` por um stub no-op:

```python
@pytest.fixture(autouse=True)
def clean_db() -> Iterator[None]:  # type: ignore[override]
    """No-op: testes unit não dependem de banco."""
    yield
```

Alternativa equivalente (mais cirúrgica): aplicar `pytestmark = pytest.mark.usefixtures()` ou tornar o `clean_db` raiz **não** autouse e exigi-lo explicitamente apenas nos testes de integração que precisarem (preferível a médio prazo — autouse globalmente é geralmente um anti-padrão).

**Verificação esperada após o fix:** `pytest tests/unit/ -q` deve mostrar `49 passed in <tempo>` (zero errors) sem dependência de Postgres.

### § H.3 Cobertura por área (extraída de `artefatos/baseline-coverage.txt`)

Total do projeto: **62%** (2.512 statements, 942 missing). 99 passed, 1 failed (smoke `test_ai_client`, falha de conectividade externa — não funcional).

**Módulos críticos abaixo da meta (< 50%)** — todos pertencem a serviços / workers / endpoints de produção:

| Módulo | Stmts | Cobertura | Meta | Gap |
|---|---|---|---|---|
| `app/workers/celery_app.py` | 7 | **0%** | 60% | -60 |
| `app/services/ai/insights_generator.py` | 184 | **14%** | 70% | -56 |
| `app/services/ai/context_builder.py` | 75 | **20%** | 70% | -50 |
| `app/services/ai/pattern_analyzer.py` | 78 | **27%** | 70% | -43 |
| `app/services/push_service.py` | 21 | **29%** | 70% | -41 |
| `app/services/reminder_service.py` | 42 | **31%** | 80% | -49 |
| `app/workers/tasks/reports.py` | 114 | **32%** | 60% | -28 |
| `app/api/v1/ai.py` | 85 | **36%** | 80% | -44 |
| `app/services/ai/food_lookup.py` | 75 | **41%** | 70% | -29 |
| `app/services/ai/ai_client.py` | 83 | **43%** | 70% | -27 |

**Módulos em zona cinzenta (50–65%)**:

| Módulo | Cobertura |
|---|---|
| `app/api/v1/auth.py` | 51% |
| `app/api/v1/push.py` | 54% |
| `app/services/profile_service.py` | 54% |
| `app/api/v1/reminders.py` | 55% |
| `app/services/meal_service.py` | 56% |
| `app/workers/tasks/reminders.py` | 56% |
| `app/services/ai/vision_parser.py` | 60% |
| `app/services/ai/meal_parser.py` | 61% |
| `app/api/v1/users.py` | 61% |
| `app/schemas/reminder.py` | 62% |
| `app/services/log_service.py` | 63% |
| `app/services/dashboard_service.py` | 65% |

**Áreas bem cobertas (≥ 80%)**:
- Schemas (a maioria 100% — DTOs puros).
- Models (~92–97% — `__repr__`/relacionamentos cobertos pelas integration tests).
- `app/services/nutrition/tdee.py` — 100% (puro, tem unit test dedicado).
- `app/core/security.py` — 100% (cobertura via `test_security.py`).
- `app/main.py` — 85% (smoke).
- `app/workers/tasks/maintenance.py` — 82% (tem `test_celery_tasks.py`).

**Padrão**: o "buraco" da cobertura é exatamente o **núcleo de IA + push + workers periódicos** — código com efeitos colaterais (Groq, Redis, scheduler) e portanto o mais difícil de testar **e** o que mais quebra silenciosamente. Combina com AUD-013 (logs sem dimensões para agregar) — sem teste e sem log estruturado, regressões só aparecem quando o user reclama.

Recomendação consolidada está no achado AUD-043 (sob severidade 🟠). Não bloqueia release, mas qualquer ambição de "deployar com confiança" exige levar `food_lookup` + `meal_parser` + `vision_parser` + `auth_service` para ≥ 70% antes do primeiro merge em main com tráfego real.

### § H.4 Áreas críticas sem teste dedicado

Inventário cruzado entre `app/services/**` e `tests/unit/test_*.py` (artefato `H3-test-coverage.txt`):

**Subdiretório `app/services/ai/` (8 arquivos)** — coração funcional do produto:

| Arquivo | Unit test? | Severidade do gap | Por quê |
|---|---|---|---|
| `meal_parser.py` | ✅ `test_meal_parser.py` | ok (61% cov) | happy path coberto, faltam edge cases (vide AUD-017) |
| `vision_parser.py` | ✅ `test_vision_parser.py` | ok (60% cov) | mesmo padrão; falta cobrir mime types inválidos |
| `utils.py` | ⚠️ transitivo (via parsers) | 🟡 média | sem teste dedicado de `extract_json_from_ai_response` — 4/9 padrões falham (AUD-017) |
| `food_lookup.py` | ❌ ausente | **🟠 alta** | é a tradução IA→banco; AUD-016 (🔴 perf) e AUD-006 (N+1) impactam aqui; teste de regressão com 50–100 alimentos é imprescindível |
| `context_builder.py` | ❌ ausente | **🟠 alta** | construtor de prompts — sem teste, qualquer regressão de prompt passa despercebida; tem CC D(25) `build_meal_context` |
| `insights_generator.py` | ❌ ausente | **🟠 alta** | 184 stmts, 14% cov; objeto de AUD-002 (decomposição); enquanto não quebra, novos testes pequenos para `daily_insight`/`weekly_insight` já capturam regressão |
| `pattern_analyzer.py` | ❌ ausente | 🟡 média | menos crítico (relatórios derivados), mas alimenta `goal_adjustment_suggestion` |
| `ai_client.py` | ⚠️ smoke only | 🟡 média | `tests/smoke_test.py::test_ai_client` requer Groq real (falha sem rede); falta unit test com mock Groq cobrindo cache, retry, ApiError |

**Subdiretório `app/services/` (raiz, 8 arquivos)** — orquestração de domínio:

| Arquivo | Unit test? | Integration? | Severidade |
|---|---|---|---|
| `auth_service.py` | ❌ | parcial via `test_auth.py` | 🟡 média — `blacklist_token` depende de Redis real, sem teste com `fakeredis` |
| `push_service.py` | ❌ | ❌ | 🟡 média — 29% cov; `send_push_notification_sync` + cleanup 410 (AUD-028) sem cobertura |
| `reminder_service.py` | ❌ | ❌ direto | 🟡 média — 31% cov; serviço usado por workers periódicos |
| `profile_service.py` | ❌ | parcial via `test_users.py` | 🟢 baixa — CRUD simples sobre `user_profiles` |
| `meal_service.py` | ❌ | ✅ `test_meals.py` | 🟢 baixa — caminho coberto, mas 56% cov sugere lacunas |
| `dashboard_service.py` | ❌ | ✅ `test_dashboard.py` | 🟢 baixa |
| `log_service.py` | ❌ | ✅ `test_logs.py` | 🟢 baixa |
| `user_service.py` | ❌ | parcial via `test_users.py` | 🟢 baixa |

**Workers (`app/workers/tasks/`, 3 arquivos)**:

| Arquivo | Unit test? | Cobertura | Severidade |
|---|---|---|---|
| `maintenance.py` | ✅ `test_celery_tasks.py` | 82% | ok |
| `reminders.py` | ⚠️ parcial em `test_celery_tasks.py` | 56% | 🟡 média — TZ (AUD-026) e hardcode `2000` (AUD-027) sem teste de regressão |
| `reports.py` | ❌ | 32% | 🟠 alta — 114 stmts, dois grandes pushes (diário e semanal) sem teste, ambos duplicam padrão 410 (AUD-028) |

**Consolidação dos gaps 🟠 alta** (5 itens): `food_lookup.py`, `context_builder.py`, `insights_generator.py`, `workers/tasks/reports.py`, `ai_client.py` (ao menos para cache/retry). Todos absorvidos no plano de AUD-043 (Onda 1 e Onda 2).

**Próximas ações concretas sugeridas no PR de cobertura**:
1. Adicionar `pytest-mock` ao `[project.optional-dependencies].dev` se ainda não tiver (verificar).
2. Adicionar `fakeredis>=2.20` para testar `auth_service.blacklist_token` e `push_service` sem container.
3. Criar `tests/unit/test_food_lookup.py` com fixtures de 50 alimentos populares (semente a partir de `app/services/ai/food_lookup.py` + alimentos comuns brasileiros conhecidos do TACO).
4. Criar `tests/unit/test_context_builder.py` com snapshot do prompt gerado para 3 personas (atleta 25a, sedentário 50a, criança 8a) — qualquer mudança de prompt vira diff explícito.
5. Criar `tests/unit/test_ai_client.py` com mock do `groq.AsyncGroq` — exercita: cache hit/miss, retry em 429, retry em 503, erro permanente em 401.

### § H.6 E2E — BASE_URL, credenciais e setup

**Arquivos analisados:** `playwright.config.ts` (26 linhas), `e2e/auth.spec.ts` (43), `e2e/dashboard.spec.ts` (66), `e2e/meals.spec.ts` (72).

**Achado principal — BASE_URL inconsistente entre suites:**

| Arquivo | URL alvo | Estratégia |
|---|---|---|
| `playwright.config.ts:15` | `baseURL: "http://localhost:3000"` | default sensato; combinado com `webServer.command: "npm run dev"` que sobe Next em :3000 |
| `auth.spec.ts:3` | `process.env.BASE_URL ?? "https://frontend-nine-mu-59.vercel.app"` | **ignora completamente o `baseURL` do config**; quando `BASE_URL` está vazia, bate na **Vercel preview pública** |
| `dashboard.spec.ts` | usa caminhos relativos (`/dashboard`) | ✅ herda do config |
| `meals.spec.ts` | usa caminhos relativos (`/refeicoes`) | ✅ herda do config |

Consequência operacional: rodar `npx playwright test` sem env vars dispara, na suite `auth`, requisições HTTP reais contra `frontend-nine-mu-59.vercel.app` — frontend de **preview/produção do projeto** (URL Vercel). Os outros 4 testes (dashboard + meals) rodam contra `http://localhost:3000`. Resultado: a suite de autenticação é a única que pode atingir produção em todo desenvolvimento local. Vetores combinados:

1. **Crédito de auth real consumido em CI/local** (vide AUD-038 — par email/senha real está hardcoded no mesmo arquivo).
2. **Cadastro automático de usuários** em produção a cada run via teste "deve cadastrar novo usuário" (`auth.spec.ts:24-33`) — cada execução cria um `playwright_test_<timestamp>@gmail.com` no banco de prod.
3. **Falsos verdes**: se a Vercel preview cair ou mudar de URL (deploy diferente), todos os testes da suite quebram sem nenhum efeito no backend testado localmente — o desenvolvedor "conserta" mudando a URL e perde a regressão.

**Hardcode de credenciais (cobertura cruzada com AUD-038/PASSO 8.1):**

- `auth.spec.ts:37-38` — par real `gabrielnegreirossaraiva38@gmail.com` / `***REMOVED***`.
- `auth.spec.ts:4-5` — `TEST_EMAIL`/`TEST_PASSWORD` derivados de `Date.now()` (✅ rotação automática, bom padrão).
- Mocks em `dashboard.spec.ts:32` e `meals.spec.ts:16` usam `accessToken: "fake-token"` — não vaza, apenas alimenta o mock de `next-auth`.

**Setup de usuário (mock vs real):**

| Suite | Estratégia | Trade-off |
|---|---|---|
| `auth` | usuário real (vercel preview) + email gerado por timestamp + um login com credencial fixa | testa fluxo end-to-end de verdade, mas cria registros em prod e expõe segredo |
| `dashboard` | mock total via `page.route("**/api/auth/session**")` + mock de `/api/v1/dashboard/today` | rápido, isolado, mas só valida que a página "carrega" — assertions superficiais (linha 64: `not.toHaveURL(/\/login/)`) |
| `meals` | mesmo padrão de `dashboard`, mock de `/api/v1/meals` e `/api/v1/auth/me` | idem — valida navegação, não comportamento |

**Bug latente menor (sem achado dedicado):** `auth.spec.ts:32` aceita o destino `login` no matcher (`toHaveURL(/(onboarding|dashboard|login)/)`) — significa que "voltou pro login" é considerado sucesso para "cadastrou novo usuário e redirecionou". Matcher permissivo invisibiliza falha de cadastro. Pequena correção: remover `login` do regex.

**Plano consolidado** (combina com fix de AUD-038):
1. Substituir constante `BASE_URL` por `process.env.E2E_BASE_URL ?? "http://localhost:3000"` em `auth.spec.ts`.
2. Garantir que `playwright.config.ts` aceite override via `process.env.E2E_BASE_URL` para promover, em CI, contra ambiente staging (não preview pública).
3. Adicionar fixture global (em `e2e/fixtures.ts`) que cria usuário de teste via `POST /api/v1/auth/register` antes da suite — substitui o login hardcoded.
4. Apertar o matcher do teste de cadastro: aceitar apenas `(onboarding|dashboard)`.
5. Remover credenciais reais (AUD-038), em paralelo ao filter-repo do histórico.
