# Frente J — Observabilidade

**Plano:** ver `plano.md` § Frente J.

## Achados desta frente

- AUD-049 — Logging do backend é texto humano (não estruturado) e `logging.basicConfig` global em `main.py` ignora `LOG_LEVEL` — sem agregação possível por `user_id`/`request_id`/módulo (🟡 média).
- AUD-050 — `/health` retorna `{"status":"ok","version":"0.1.0"}` hardcoded — sem readiness check de Postgres/Redis e versão dessincronizada do CHANGELOG (0.7.0) (🟡 média).
- AUD-051 — Ausência total de Sentry/APM em backend e frontend — erros em produção são invisíveis até o usuário reportar (🟡 média; acknowledged como `[ ]` no Roadmap 9.3).

## Notas e contexto

### § J.1 Logging atual (de `artefatos/J1-loggers.txt`)

**15 loggers nomeados mapeados no backend.** Distribuição:

| Namespace | Onde | Padrão |
|---|---|---|
| `caloria.db` | `app/core/database.py:15` | logger nomeado custom; usado pelos listeners SQLAlchemy (AUD-036 — log de toda query em INFO) |
| `caloria.http` | `app/main.py:19` | logger nomeado custom; usado pelo `timing_middleware` |
| `app.workers.tasks.reports` | `workers/tasks/reports.py:14` | `__name__` (padrão Python) |
| `app.workers.tasks.maintenance` | `workers/tasks/maintenance.py:16` | `__name__` |
| `app.workers.tasks.reminders` | `workers/tasks/reminders.py:16` | `__name__` |
| `app.services.auth_service` | `services/auth_service.py:11` | `__name__` |
| `app.services.push_service` | `services/push_service.py:8` | `__name__` |
| `app.services.ai.insights_generator` | `services/ai/insights_generator.py:27` | `__name__` |
| `app.services.ai.utils` | `services/ai/utils.py:7` | `__name__` |
| `app.services.ai.ai_client` | `services/ai/ai_client.py:13` | `__name__` |
| `app.services.ai.food_lookup` | `services/ai/food_lookup.py:22` | `__name__` |
| `app.services.ai.pattern_analyzer` | `services/ai/pattern_analyzer.py:16` | `__name__` |
| `app.services.ai.vision_parser` | `services/ai/vision_parser.py:16` | `__name__` |
| `app.services.ai.meal_parser` | `services/ai/meal_parser.py:15` | `__name__` |

**Configuração global** (`backend/app/main.py:14-18`):

```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
```

**Pontos detectados:**

1. **Formato é texto humano**, não JSON estruturado. Cada linha tem apenas: hora, level, logger name, mensagem livre. Sem campos para `user_id`, `request_id`, `meal_id`, `duration_ms`, `model`, etc. — impossível agregar/filtrar por dimensão no destino (ELK, Loki, CloudWatch Logs Insights, BigQuery sink). Cross-ref direto com:
    - **AUD-013** — `ai_client.py:111` faz `logger.info("Groq tokens — entrada: %d, saída: %d", ...)` sem dimensão para agregar custo por usuário/modelo.
    - **AUD-027** — silenciamento do hardcode `2000` de água é mais difícil debugar sem logs estruturados.
    - **AUD-028** — duplicação 410 em 4 sites loga textos similares mas não correlatos.
    - **AUD-040** — sem rate limit + logs sem `user_id` significa que abuso é invisível até virar incidente.
2. **`LOG_LEVEL` não é lido**. `basicConfig(level=logging.INFO)` é hardcoded. Em produção, baixar para WARNING ou subir para DEBUG temporariamente requer mudança de código + redeploy. `Settings` (em `core/config.py`) tem `APP_ENV: str = "development"` mas não `LOG_LEVEL`.
3. **`datefmt="%H:%M:%S"`** sem data — em logs de produção rodando 24h, perde rastro de qual dia uma linha aconteceu. Único container que o evita é o Caddy (formato padrão ISO 8601 — verificar PASSO 11.4).
4. **`logger` em alguns módulos passa kwargs ao stream** (`logger.info("%s %s", a, b)`) ✅ — bom para evitar interpolação custosa; em outros usa f-string interpolada (`logger.info(f"...")`) ❌ — formatação acontece mesmo se o level estiver acima. Inconsistente.
5. **Bom sinal**: usar `logging.getLogger(__name__)` na maioria dos módulos (12/14) — permite ajuste de level por namespace via `logging.getLogger("app.services.ai").setLevel(logging.WARNING)`. Cobre o caso real do AUD-036 (`caloria.db` em INFO loga toda query, infla volume — basta `getLogger("caloria.db").setLevel(WARNING)` para silenciar sem deletar listener).
6. **Sem correlação cross-request**. Não há `X-Request-Id` no middleware, sem `contextvars` para propagar. Quando o `timing_middleware` loga `[HTTP] POST /meals 200  823ms`, e 50ms depois `ai_client.py` loga `Groq tokens — entrada: 1200, saída: 80`, não há como saber que os dois pertencem ao mesmo request.

**Recomendação consolidada (AUD-049)** — Esforço M (1-4h), valor alto:

1. **Migrar para logger estruturado JSON**: adicionar `structlog` ou `python-json-logger`. Cada log line vira JSON com campos típicos: `ts`, `level`, `logger`, `msg`, `user_id` (quando disponível), `request_id`, `path`, `status`, `duration_ms`.
2. **Adicionar `request_id` no middleware** via `contextvars.ContextVar[str]` setado no `timing_middleware`; todos os loggers da request passam a carregar esse id automaticamente via processor do structlog. `X-Request-Id` ecoado no response (útil para reportes de bug do front).
3. **Ler `LOG_LEVEL` do `Settings`** (`config.py`): `LOG_LEVEL: str = Field(default="INFO")` + aplicar em `setup_logging()` no startup.
4. **Trocar `datefmt="%H:%M:%S"` por ISO 8601 completo** (`%Y-%m-%dT%H:%M:%S.%fZ`) ou deixar o structlog formatar.
5. **Padronizar todos os `logger.info(f"...")` para placeholders `%s`** (lint rule no ruff: `G004`).

Fix completo desbloqueia 4 outros achados (AUD-013, AUD-027, AUD-028, AUD-040 ficam mais fáceis de debugar/medir).

### § J.3 Health check completeness

**Endpoint atual** (`backend/app/main.py:72-74`):

```python
@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}
```

**3 gaps mapeados:**

| Gap | Estado | Impacto |
|---|---|---|
| Versão hardcoded `"0.1.0"` | ❌ desalinhada com CHANGELOG (`[0.7.0] - 2026-05-10`) e com `backend/pyproject.toml:7` (`version = "0.1.0"`) | Ferramenta de monitoring que polla `/health` reporta versão errada; bisseção de incidente fica difícil — qual deploy está rodando? |
| Verificação de **Postgres** | ❌ ausente | Container fica `healthy` no Docker Swarm/K8s mesmo se Postgres caiu — load balancer continua mandando tráfego para um backend que vai 500ar em toda request. Inconsistente com o `lifespan` (linhas 23-30) que **já** executa `SELECT 1` no startup — o conhecimento de "DB está vivo" existe, só não é exposto. |
| Verificação de **Redis** | ❌ ausente | Cache de IA (AIClient), blacklist de refresh tokens (auth_service) e filas Celery dependem de Redis. Falha de Redis hoje é silenciosa: `aioredis.from_url` em `try/except` (cf. AUD-014), funcionalidade degrada sem alerta. |

**Liveness vs Readiness — convenção de orquestradores:**

- **Liveness** (processo está vivo?): o `/health` atual cobre. K8s usa para decidir se mata e recria o container.
- **Readiness** (pode receber tráfego?): hoje **não existe endpoint**. K8s/Caddy precisaria de algo como `/ready` que checa dependências externas.

Compose dev (`docker-compose.dev.yml:43`) faz `healthcheck` no serviço backend (verificado em PASSO 10.6) — provavelmente curl em `/health`. Esse healthcheck só ratifica o cenário acima: container fica `healthy` mesmo com banco caído.

**`pyproject.toml:7` versão `0.1.0`** — não é só o `/health`. `app.main:33-40` instancia `FastAPI(title="CalorIA", version="0.1.0", ...)`, então o **OpenAPI/Swagger** também reporta versão errada. Cross-ref para PASSO 12.1 (FASE 12, coerência de versões).

**Recomendação (AUD-050)** — Esforço S (<1h):

1. **Trocar versão hardcoded por leitura dinâmica**:
    ```python
    from importlib.metadata import version as pkg_version
    APP_VERSION = pkg_version("caloria-backend")
    ```
    Lê do `pyproject.toml` no install. Atualizar `app.version` na criação do FastAPI também resolve OpenAPI.
2. **Separar liveness e readiness**:
    ```python
    @app.get("/health/live", tags=["health"])
    async def live() -> dict[str, str]:
        return {"status": "ok", "version": APP_VERSION}

    @app.get("/health/ready", tags=["health"])
    async def ready(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
        checks = {}
        try:
            await db.execute(text("SELECT 1"))
            checks["postgres"] = "ok"
        except Exception as exc:
            checks["postgres"] = f"fail: {exc.__class__.__name__}"
        try:
            async with aioredis.from_url(settings.REDIS_URL) as r:
                await r.ping()
            checks["redis"] = "ok"
        except Exception as exc:
            checks["redis"] = f"fail: {exc.__class__.__name__}"
        ok = all(v == "ok" for v in checks.values())
        return JSONResponse({"status": "ok" if ok else "degraded", "checks": checks}, status_code=200 if ok else 503)
    ```
3. **Manter `/health` como alias de `/health/live`** para retrocompat com o healthcheck do compose atual.
4. **Apontar o healthcheck do compose** para `/health/ready` no serviço backend — load balancer só roteia para containers prontos.

Combina com AUD-014 (pool Redis persistente facilita o ping); combina com AUD-039 (validator de SECRET_KEY pode usar o mesmo `lifespan` que já roda `SELECT 1`).

### § J.4 Sentry / APM / Tracing (ausência confirmada)

**Busca executada**: `rg -l "sentry" /home/gabriel/projetos/CalorIA/ | grep -v node_modules` (artefato `J3-sentry.txt`).

**Resultado**: 2 matches, **ambos referenciais (não instrumentação)**:

| Arquivo | Por que aparece |
|---|---|
| `docs/auditoria/runbook.md` | menção ao próprio PASSO 11.3 — este passo |
| `data/processed/alimentos_final.csv` | string casual em algum nome de alimento (ex.: "pão sentry"? — irrelevante; CSV importado de Open Food Facts/TACO) |

**Conclusão**: zero código de instrumentação Sentry/APM no projeto, em backend ou frontend.

**Roadmap § 9.3 acknowledge** (`Roadmap.md:417`):

```
- [ ] Sentry para erros em produção (backend + frontend)
- [ ] Health check endpoint monitorado (UptimeRobot ou similar)
- [ ] Logs estruturados com nível configurável
```

Os 3 itens da seção "Observabilidade" estão abertos. **Logs estruturados** já é AUD-049; **health check monitorado** se relaciona com AUD-050 (precisa do `/health/ready` primeiro). **Sentry** é o item restante — é o que este passo registra.

**Pontos onde a ausência dói mais hoje:**

1. **Erros 500 não-tratados** no FastAPI viram apenas tracebacks no stdout (formato texto humano, AUD-049). Sem alerta, sem agregação por endpoint, sem volume histórico. O usuário fica vendo "Erro inesperado" no toast e a equipe só descobre quando ele reclama.
2. **`groq.APIConnectionError` (visto no smoke test)** — erros transientes da Groq são logados como warning durante retry e re-elevados após 4 tentativas (`ai_client.py:122`). Em prod, isso quebra silenciosamente o pipeline de IA até alguém manualmente ver o log.
3. **Frontend** — exceções JavaScript não capturadas (rejected promises, React errors) caem no `console.error` do browser. Zero telemetria do que está quebrando para usuários em campo.
4. **Workers Celery** — `dispatch_due_reminders`, `cleanup_old_conversations`, `send_daily_summaries`. Falha de qualquer task hoje só aparece se alguém ler o log do `celery_worker`. Combina mal com AUD-026 (TZ latente) — se o bug ativar (mudança de TZ no container), todos os lembretes do dia ficam errados e ninguém percebe até usuário reclamar.

**Plano de instrumentação proposto (AUD-051)** — Esforço M (1-4h):

1. **Backend** — adicionar `sentry-sdk[fastapi,celery,sqlalchemy]` a `pyproject.toml`. No `app/main.py`:
    ```python
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.APP_ENV,
            release=APP_VERSION,  # mesma fonte do AUD-050
            traces_sample_rate=0.1,
            profiles_sample_rate=0.1,
            integrations=[FastApiIntegration(), CeleryIntegration(), SqlalchemyIntegration()],
        )
    ```
    `SENTRY_DSN` opcional em `Settings` — não inicializa em dev sem DSN.
2. **Frontend** — `@sentry/nextjs`. `sentry.client.config.ts` + `sentry.server.config.ts` + `sentry.edge.config.ts` (padrão Next 14). Mesmo padrão de `dsn` opcional via env.
3. **Tagging consistente**: enriquecer eventos com `user_id` (via Sentry's `setUser({id})`) quando autenticado. Combina com AUD-049 (request_id no contextvar) — passar como `request_id` tag.
4. **Sampling agressivo em prod**: `traces_sample_rate=0.1` (10%) ou menos para começar; `profiles_sample_rate=0.0` enquanto tráfego baixo (custo do Sentry é por evento).
5. **Beneficiários colaterais**: AUD-013 (custo Groq) — Sentry pode receber events customizados com tokens; AUD-016 (food_lookup lento) — Sentry profiling pega o hotspot sem precisar do EXPLAIN manual.

**Custo**: Sentry free tier dá 5k errors/mês — suficiente para projeto pessoal. Caso adoção cresça, GlitchTip self-hosted é alternativa free clone.
