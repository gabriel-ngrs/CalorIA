# Plano de Correção — CalorIA

> **Propósito**: aplicar os 57 achados da auditoria de forma incremental, em ordem que respeita dependências e prioridade de risco. Cada tarefa é entregável como **um único PR** (alguns bundlam 2-5 AUDs com sinergia técnica).

---

## Como usar este arquivo

**Fluxo de trabalho** (para humano ou agente AI):

1. **Ler o status global** abaixo — descobrir qual tarefa é a próxima `[ ]`.
2. **Pré-flight check** antes de mexer (ver seção abaixo) — garantir que não houve drift no código.
3. **Aplicar o fix** seguindo os passos listados na tarefa.
4. **Rodar a verificação** específica da tarefa + `make check` global.
5. **Commitar** com a mensagem sugerida.
6. **Marcar a tarefa como `[x]`** neste arquivo e atualizar o status global.
7. **Próxima tarefa.**

**Regras**:

- **Uma tarefa = um PR.** Não acumular fixes em um PR só, mesmo que pareçam pequenos. A rastreabilidade é o ativo.
- **Sempre testar antes de commitar.** Se quebrou outra coisa, parar e investigar — não bypassar pre-commit com `--no-verify`.
- **Sem co-author IA, sem emojis no commit, em PT-BR** (CLAUDE.md).
- **Não pular tarefa por achar "fácil demais".** A ordem aqui foi pensada para que cada fix prepare o terreno do seguinte.
- **Se o fix revelar surpresa** (acoplamento não previsto, teste que estava errado, etc.), **pausar e perguntar**. Não corrigir "no escuro".

**Referências por achado**: cada tarefa cita `AUD-NNN` — o detalhamento completo (severidade, evidência, contexto, esforço) está em [`achados.md`](achados.md) ordenado por severidade. Use Ctrl+F com `AUD-NNN` para localizar.

**Quando este plano estiver concluído**, todos os achados estarão fechados e a Definition of Done em [`relatorio-preliminar.md`](relatorio-preliminar.md) estará 100% checada.

---

## Pré-flight check (antes de QUALQUER tarefa)

Execute estes passos para garantir consistência:

```bash
git status                          # working tree limpo
git log --oneline -5                # último commit é o esperado
grep "^- \[x\]\|^- \[ \]" docs/auditoria/plano-correcao.md | head -20   # ver progresso
```

Se houver drift inesperado (arquivos modificados não relacionados, commits não previstos), **parar e investigar** antes de prosseguir.

Para tarefas que envolvem testes, **subir os serviços primeiro**:

```bash
docker compose -f docker-compose.dev.yml up -d postgres redis
```

---

## Status global

**Última atualização**: 2026-05-11 (criação do plano)

| Severidade | Total | Concluídos | Pendentes |
|---|---|---|---|
| 🔴 Críticos | 2 | 0 | 2 |
| 🟠 Altos | 14 | 0 | 14 |
| 🟡 Médios | 21 | 0 | 21 |
| 🟢 Baixos | 20 | 0 | 20 |
| **Total** | **57** | **0** | **57** |

**Bloco atual**: Bloco 0 (manual humano) → Bloco 1 (segurança crítica + performance + workers + backup)

---

## Bloco 0 — Ação manual humana (não é PR)

> ⚠️ **Essas etapas precisam ser feitas por um humano antes de qualquer PR.** Não dá pra delegar para agente, não dá pra esperar code review.

### [ ] M0.1 — Rotar senha do mantenedor (AUD-038, etapa 1 de 4)

**Por quê primeiro de tudo**: a senha real do mantenedor (cf. AUD-038 em `achados.md` para evidência) está em texto claro no GitHub público desde 2026-04-29. Cada minuto adicional aumenta o risco. **Esta etapa não pode esperar code review.**

**O que fazer**:

1. Trocar a senha em `gabrielnegreirossaraiva38@gmail.com` (Gmail / Google account).
2. Trocar a mesma senha em **qualquer outro serviço** onde ela tenha sido reusada (banco, redes sociais, outros logins). Use um password manager para a nova senha — sem reuso.
3. Trocar a senha do usuário correspondente no app CalorIA (se já estiver em produção).
4. Habilitar 2FA na conta Google se ainda não estiver.

**Verificar**:

- Tentar login no Gmail com a senha antiga → deve falhar.
- Conferir histórico de login do Google (myaccount.google.com → Security → Recent activity) por acessos suspeitos nos últimos ~12 dias.

**Sem commit** (não há mudança de código).

**Depois disso**: prosseguir para Bloco 1.

---

## Bloco 1 — Segurança crítica + performance + workers + backup

> **Goal**: deixar o sistema seguro o suficiente para o primeiro deploy com tráfego real. Os 4 PRs abaixo são **bloqueantes** para qualquer release público.

### [ ] B1.1 — PR Segurança: remover credenciais + secret scan + validators (AUD-038 etapa 2-4, AUD-039, AUD-047, AUD-057)

**Achados fechados**: AUD-038 (🔴), AUD-039 (🟠), AUD-047 (🟡), AUD-057 (🟢) — 4 achados em 1 PR.

**Bundling motivado**: todos são "defesa em profundidade contra secrets/segredos vazados". Mover credenciais para env (038), adicionar fail-fast para defaults inseguros (039), instalar secret scan no pre-commit/CI (047) — gitleaks teria pego AUD-038 no commit original. AUD-057 é o reflexo doc disso.

**Fix**:

1. **AUD-038 etapa 2 — remover credenciais do código**:
   - Em `frontend/e2e/auth.spec.ts:37-38`, trocar para `process.env.E2E_LOGIN_EMAIL` / `process.env.E2E_LOGIN_PASSWORD`. Adicionar fallback que cria usuário via API se as envs não estiverem definidas (preferível — vide AUD-044).
   - Adicionar secret `E2E_LOGIN_EMAIL` e `E2E_LOGIN_PASSWORD` em GitHub Actions → Settings → Secrets.
   - Adicionar `E2E_LOGIN_*` em `.env.example` documentando que são opcionais (criação via API é o caminho preferido).
2. **AUD-038 etapa 3 — rewrite do histórico**:
   - Instalar `git-filter-repo` (não usar BFG, está mais bugado).
   - Rodar `git filter-repo --replace-text <replacements.txt>` com regras `<senha-real>==>***REMOVED***` (consultar `achados.md` AUD-038 para a string exata).
   - **AVISO**: reescreve histórico — todos os clones do repo ficam órfãos. Avisar colaboradores ANTES (no caso, projeto solo, então tranquilo).
   - Force-push: `git push --force origin --all && git push --force origin --tags`.
3. **AUD-039 — fail-fast para SECRET_KEY e NEXTAUTH_SECRET**:
   - Em `backend/app/core/config.py`, adicionar `@model_validator(mode="after")`:
     ```python
     @model_validator(mode="after")
     def _validate_secrets(self) -> "Settings":
         if self.APP_ENV != "development":
             if self.SECRET_KEY == "insecure-default-key-change-in-production" or len(self.SECRET_KEY) < 32:
                 raise ValueError("SECRET_KEY must be set and >= 32 chars in non-dev environments")
         return self
     ```
   - Em `frontend/next.config.mjs`, adicionar validação no boot:
     ```js
     if (process.env.NODE_ENV === "production" && (!process.env.NEXTAUTH_SECRET || process.env.NEXTAUTH_SECRET === "insecure-secret-change-in-production")) {
       throw new Error("NEXTAUTH_SECRET must be set in production");
     }
     ```
   - Considerar também `VAPID_PUBLIC_KEY` e `VAPID_CLAIMS_EMAIL` no mesmo validator (defaults vazios silenciam push).
4. **AUD-047 — adicionar mypy, eslint, gitleaks ao pre-commit**:
   - Em `.pre-commit-config.yaml`, adicionar 3 repos (snippet completo em `docs/auditoria/09-qualidade.md § I.4`).
   - Rodar `pre-commit run --all-files` e tratar achados imediatos (provavelmente vai trigar AUD-045 — então é a hora de bundlar a decisão sobre `scripts/`).
   - Adicionar workflow `gitleaks` em `.github/workflows/ci.yml` (job separado, falha o CI se achar segredo).
5. **AUD-057 — alinhar `CONTRIBUTING.md:42`**:
   - Após item 4 acima, a linha 42 vira verdadeira sem editar. Apenas conferir.

**Verificar**:

```bash
# 1. Credenciais sumiram do código atual:
rg "<senha-vazada>|<email-vazado>" .
# Deve retornar 0 hits (a não ser que esteja nos docs da auditoria — esse é histórico, aceitável)

# 2. Credenciais sumiram do histórico:
git log --all --full-history -p | rg "<senha-vazada>"
# Deve retornar 0 hits após filter-repo

# 3. Fail-fast funciona:
cd backend && APP_ENV=production SECRET_KEY=curtaedemais python -c "from app.core.config import settings"
# Deve raise ValueError

# 4. Pre-commit roda os 3 hooks novos:
pre-commit run --all-files
# mypy + eslint + gitleaks devem aparecer na saída

# 5. CI gitleaks:
# Push o branch e ver no GitHub Actions
```

**Commit**: `feat(seguranca): remove credenciais, valida secrets e adiciona secret scan`

> Use múltiplos commits no PR se preferir granularidade. Mas como é um bloqueante, prefiro um commit grande do que 5 commits pequenos que precisam ser revertidos juntos se algo der errado.

**Cuidados**:
- Antes do force-push, fazer backup do `.git/` local (`cp -r .git .git.backup`) caso algo dê errado.
- Avisar `Roadmap.md § 9.3` que "logs estruturados" + "Sentry" + "monitoring" ainda estão abertos — vão ser fechados no Bloco 2.

---

### [ ] B1.2 — PR Performance: food_lookup 70× mais rápido (AUD-016, AUD-006)

**Achados fechados**: AUD-016 (🔴), AUD-006 (🟠) — 2 achados em 1 PR.

**Bundling motivado**: AUD-016 isola elimina o Seq Scan (585ms→8ms), AUD-006 elimina o N+1 (25 queries → 1 query). Junto: refeição típica vai de **~14.6s** para **~50ms** em food lookup. Não fazer juntos é perder o ganho composto.

**Fix**:

1. **AUD-016 — usar threshold dinâmico do pg_trgm**:
   - Em `backend/app/services/ai/food_lookup.py:90-104`, na função que executa a query:
     - Antes da query principal, executar `SET LOCAL pg_trgm.similarity_threshold = 0.18`.
     - Remover o `OR similarity(search_text, :q) >= :min_score` do `WHERE`, deixar só `WHERE search_text %>> :q`.
   - O operador `%>>` (strict word similarity) respeita o threshold dinâmico **e** usa o índice GIN — performance volta a 8ms.
2. **AUD-006 — batch query para todos os termos da refeição**:
   - Em vez de loop `for term in terms: lookup(term)`, montar uma única query com `UNION ALL` ou usar `ANY(:terms_array)` com window functions para ranking por termo:
     ```sql
     WITH ranked AS (
       SELECT *,
              similarity(search_text, q) AS score,
              ROW_NUMBER() OVER (PARTITION BY q ORDER BY similarity(search_text, q) DESC) AS rn
       FROM foods, unnest(:terms) AS q
       WHERE search_text %>> q
     )
     SELECT * FROM ranked WHERE rn <= 5;
     ```
   - Refatorar `MealParser._lookup_and_fill` para receber a lista completa de termos e fazer 1 query.

**Verificar**:

```bash
# 1. EXPLAIN ANALYZE da query reformulada — deve ser Bitmap Index Scan:
docker exec caloria_postgres psql -U caloria -d caloria_db -c "
  SET pg_trgm.similarity_threshold = 0.18;
  EXPLAIN ANALYZE SELECT * FROM foods WHERE search_text %>> 'arroz' LIMIT 5;
"
# Procurar "Bitmap Index Scan" e tempo < 20ms

# 2. Smoke test do parser (precisa criar — vide Bloco 3):
cd backend && pytest tests/unit/test_meal_parser.py -v
# Tudo passando

# 3. Timing manual de uma análise de refeição completa:
curl -X POST http://localhost:8000/api/v1/ai/analyze-meal \
  -H "Authorization: Bearer <token>" \
  -d '{"description":"arroz feijão bife batata salada"}' \
  -w "\nTotal time: %{time_total}s\n"
# Deve cair de ~15s para < 1s
```

**Commit**: `perf(ai): usa pg_trgm threshold dinamico e batch lookup em food_lookup`

---

### [ ] B1.3 — PR Workers: TZ-aware + helper compartilhada + hardcode água + push 410 (AUD-025, AUD-026, AUD-027, AUD-028)

**Achados fechados**: AUD-025 (🟠), AUD-026 (🟠), AUD-027 (🟠), AUD-028 (🟡) — 4 achados em 1 PR.

**Bundling motivado**: todos tocam os mesmos 3 arquivos (`reminders.py`, `reports.py`, `maintenance.py`). Refatorar uma vez é melhor do que 4 PRs sequenciais reabrindo o mesmo arquivo.

**Fix**:

1. **AUD-025 — extrair helper `_run` e usar `asyncio.run`**:
   - Criar `backend/app/workers/_utils.py`:
     ```python
     import asyncio
     from typing import Any, Coroutine
     def run_async(coro: Coroutine[Any, Any, Any]) -> Any:
         return asyncio.run(coro)
     ```
   - Remover as 3 cópias de `_run` em `reminders.py:21`, `reports.py:19`, `maintenance.py:21`. Importar `run_async` e usar.
   - Adicionar `PYTHONWARNINGS=error::DeprecationWarning` em CI para pegar regressões.
2. **AUD-026 — `dispatch_due_reminders` TZ-aware**:
   - Em `reminders.py:36-71`, trocar `datetime.now()` por `datetime.now(ZoneInfo("America/Sao_Paulo"))`.
   - Atualizar comparação de `Reminder.time` (que é `Time` sem TZ) para extrair hora/minuto do `now` TZ-aware.
   - **Adiar para outro PR**: adicionar `User.timezone` (campo + migração + UI) e pré-computar `Reminder.next_fire_at` — fora de escopo desta tarefa.
3. **AUD-027 — usar `User.water_goal_ml`**:
   - Em `reminders.py:174,179`, trocar `2000` por `user.water_goal_ml or 2000`.
4. **AUD-028 — consolidar handling de 410 em `PushService.send_with_cleanup`**:
   - Em `backend/app/services/push_service.py`, adicionar método:
     ```python
     async def send_with_cleanup(self, user_id: int, title: str, body: str, url: str) -> int:
         """Envia push para todas as subs do user; remove subs com 410. Retorna count enviadas."""
         subs = await self._db.execute(select(PushSubscription).where(PushSubscription.user_id == user_id))
         expired_ids = []
         sent = 0
         for sub in subs.scalars():
             try:
                 send_push_notification_sync(sub, title, body, url)
                 sent += 1
             except WebPushException as exc:
                 if exc.response and exc.response.status_code == 410:
                     expired_ids.append(sub.id)
                 else:
                     logger.warning("Push falhou para sub %d: %s", sub.id, exc)
         if expired_ids:
             await self._db.execute(delete(PushSubscription).where(PushSubscription.id.in_(expired_ids)))
             await self._db.commit()
         return sent
     ```
   - Substituir os 4 sites duplicados (`reminders.py:100-137`, `:194-228`, `reports.py:80-118`, `:179-217`) por uma chamada `await PushService(db).send_with_cleanup(...)`.
   - Remover os `try: from pywebpush import WebPushException; except ImportError: pass` repetidos.

**Verificar**:

```bash
# 1. Testes do worker (assume Bloco 3 já passou — fixture clean_db OK):
cd backend && pytest tests/unit/test_celery_tasks.py -v

# 2. Deprecation warning sumiu:
cd backend && PYTHONWARNINGS=error::DeprecationWarning python -c "
from app.workers.tasks.reminders import dispatch_due_reminders
print('OK')
"

# 3. TZ-aware funciona:
docker exec caloria_backend python -c "
from datetime import datetime
from zoneinfo import ZoneInfo
print(datetime.now(ZoneInfo('America/Sao_Paulo')))
"

# 4. Hardcode 2000 sumiu:
rg "2000\b" backend/app/workers/tasks/reminders.py
# Deve retornar 0 hits

# 5. Duplicação 410 sumiu:
rg "status_code == 410" backend/app/workers/
# Deve retornar 0 hits (só na PushService)
```

**Commit**: `fix(workers): tz-aware, asyncio.run, water goal e consolida push 410`

---

### [ ] B1.4 — PR Backup Postgres automatizado (AUD-037)

**Achados fechados**: AUD-037 (🟠) — 1 achado.

**Por que separado**: toca infraestrutura/scripts de servidor, não código da app. PR mais simples e específico.

**Fix**:

1. Adicionar script `scripts/backup-postgres.sh`:
   ```bash
   #!/usr/bin/env bash
   set -euo pipefail
   STAMP=$(date +%Y%m%d-%H%M%S)
   BACKUP_DIR=/opt/caloria-backups
   mkdir -p "$BACKUP_DIR"
   docker exec caloria_postgres pg_dump -U caloria -d caloria_db | gzip > "$BACKUP_DIR/caloria-$STAMP.sql.gz"
   # Retenção local: 30 dias
   find "$BACKUP_DIR" -name "caloria-*.sql.gz" -mtime +30 -delete
   # Sync offsite (Hetzner Storage Box, rclone, etc.)
   rclone sync "$BACKUP_DIR" hetzner:caloria-backups/
   ```
2. Adicionar entrada de cron em `scripts/setup-server.sh`:
   ```bash
   (crontab -l 2>/dev/null; echo "0 3 * * * /opt/caloria/scripts/backup-postgres.sh >> /var/log/caloria-backup.log 2>&1") | crontab -
   ```
3. Adicionar seção `## Backup e Restore` em `docs/deploy.md`:
   - Onde os backups ficam (local + offsite).
   - Retenção (30d local, 90d offsite).
   - **Procedimento de restore** (com `pg_restore` ou `gunzip | psql`).
   - Mencionar que `pg_trgm` extension precisa estar criada antes do restore.
4. Criar issue ou TODO em `docs/runbook-prod.md` (criado em B4.X) para testar restore em staging trimestralmente.

**Verificar**:

```bash
# 1. Script roda sem erro (em ambiente com docker dev rodando):
bash scripts/backup-postgres.sh
ls -la /tmp/caloria-backups/ # ou wherever BACKUP_DIR aponta

# 2. Restore funciona (em ambiente staging):
gunzip -c /opt/caloria-backups/caloria-LATEST.sql.gz | docker exec -i caloria_postgres psql -U caloria -d caloria_db_test

# 3. Cron entry:
crontab -l | grep backup-postgres
```

**Commit**: `feat(deploy): adiciona backup automatizado do postgres com offsite e retencao`

**Marker**: este PR **destrava o primeiro deploy seguro**. Antes dele, o sistema não tem disaster recovery.

---

## Bloco 2 — Resiliência e observabilidade

> **Goal**: ver o sistema sob carga real. Sem isso, qualquer incidente em produção é "voo cego". Esses 5 PRs podem ser feitos em paralelo após o Bloco 1.

### [ ] B2.1 — PR Pool Redis persistente (AUD-014, AUD-046 parcial)

**Achados fechados**: AUD-014 (🟢), AUD-046 (🟢 — 3 dos 6 erros mypy) — 1.5 achados em 1 PR pequeno mas com sinergia grande.

**Por que primeiro nesta onda**: AUD-049 (logs estruturados), AUD-050 (health /ready) e AUD-051 (Sentry) **todos** se beneficiam de um pool Redis já configurado. Fazer aqui evita re-trabalho.

**Fix**:

1. Em `backend/app/services/ai/ai_client.py`, criar pool no `__init__`:
   ```python
   from redis.asyncio import ConnectionPool, Redis
   self._redis_pool = ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True, max_connections=10)
   ```
2. Em `_get_cached` e `_set_cached`, usar `Redis(connection_pool=self._redis_pool)` em vez de `aioredis.from_url(...)` por chamada.
3. Mesmo padrão para `auth_service.blacklist_token` (cria pool no `__init__` ou compartilha via singleton).
4. Confirmar que os 3 erros mypy (linhas 135, 136, 143) desaparecem após o refactor.

**Verificar**:

```bash
# 1. Mypy passa em ai_client.py:
cd backend && mypy app/services/ai/ai_client.py
# Espera-se 3 errors em vez de 6

# 2. Cache ainda funciona (smoke):
# acessar uma análise IA duas vezes; segunda chamada deve ser < 100ms (cache hit)

# 3. Não tem conn leak — abrir/fechar várias vezes:
docker exec caloria_redis redis-cli CLIENT LIST | wc -l
# Não deve crescer indefinidamente entre chamadas
```

**Commit**: `refactor(ai): usa pool persistente de redis em vez de from_url por chamada`

---

### [ ] B2.2 — PR Logs estruturados + request_id + LOG_LEVEL (AUD-049, AUD-013)

**Achados fechados**: AUD-049 (🟡), AUD-013 (🟡) — 2 achados.

**Por que aqui**: estruturação de logs é pré-requisito para Sentry tagging (B2.5) ter `user_id` / `request_id` úteis.

**Fix**:

1. Adicionar `structlog>=24.0` a `backend/pyproject.toml`.
2. Criar `backend/app/core/logging.py` com `setup_logging()` configurando:
   - Processor chain do structlog (timestamp ISO 8601, level, logger name, JSON renderer em prod / ConsoleRenderer em dev).
   - `LOG_LEVEL` lido de `settings.LOG_LEVEL` (default "INFO").
   - Bind global do `release` (versão da app — depende de B3.X de versionamento).
3. Em `backend/app/main.py`, substituir o `logging.basicConfig` por `setup_logging()`.
4. Adicionar `contextvars.ContextVar[str]` para `request_id` em `app/core/context.py`.
5. No `timing_middleware`, gerar UUID4, setar no contextvar, ecoar como header `X-Request-Id`.
6. Wrapper de `get_current_user_id` que também seta `user_id` no contextvar.
7. Adicionar processor do structlog que injeta `request_id` e `user_id` em todo log.
8. Adicionar `LOG_LEVEL: str = "INFO"` ao `Settings`.
9. Em `ai_client.py:111`, enriquecer o log de tokens: `logger.info("groq_call", model=model, prompt_tokens=..., completion_tokens=..., user_id=ctx_user_id.get(""))`.
10. Habilitar ruff rule `G004` (proíbe `logger.info(f"...")`) em `pyproject.toml`.

**Verificar**:

```bash
# 1. Logs em JSON em prod, console em dev:
APP_ENV=production docker exec caloria_backend python -c "
from app.core.logging import setup_logging
setup_logging()
import structlog; structlog.get_logger().info('teste', foo=1)
"
# Saída deve ser JSON

# 2. request_id no header:
curl -i http://localhost:8000/health | grep -i x-request-id

# 3. LOG_LEVEL respeitado:
LOG_LEVEL=WARNING docker compose up backend
# Logs de INFO devem sumir

# 4. ruff G004 pega novo log f-string:
echo 'import logging; logging.getLogger().info(f"oi {1}")' > /tmp/t.py
cd backend && ruff check /tmp/t.py --select G004
```

**Commit**: `feat(logging): adiciona structlog com request_id e log_level configuravel`

---

### [ ] B2.3 — PR Health checks separados + versão dinâmica (AUD-050, AUD-054 parcial)

**Achados fechados**: AUD-050 (🟡), AUD-054 (🟢 — fonte única de verdade da versão) — 2 achados.

**Bundling motivado**: a leitura dinâmica de versão (`importlib.metadata`) é exatamente o que resolve metade do AUD-054 e o que o `/health` precisa.

**Fix**:

1. Em `backend/app/main.py`, trocar a versão hardcoded:
   ```python
   from importlib.metadata import version as _pkg_version
   APP_VERSION = _pkg_version("caloria-backend")
   app = FastAPI(title="CalorIA", version=APP_VERSION, ...)
   ```
2. **Bumpar versão**: `backend/pyproject.toml` `version = "0.7.0"` (alinha com CHANGELOG); `frontend/package.json` idem.
3. Adicionar `/health/live` (alias do `/health` atual, retorna `APP_VERSION`):
   ```python
   @app.get("/health/live", tags=["health"])
   async def live() -> dict[str, str]:
       return {"status": "ok", "version": APP_VERSION}
   ```
4. Adicionar `/health/ready` que executa `SELECT 1` no Postgres + `PING` no Redis:
   ```python
   @app.get("/health/ready", tags=["health"])
   async def ready(db: AsyncSession = Depends(get_db)) -> JSONResponse:
       checks = {}
       try:
           await db.execute(text("SELECT 1"))
           checks["postgres"] = "ok"
       except Exception as exc:
           checks["postgres"] = f"fail: {exc.__class__.__name__}"
       try:
           async with Redis(connection_pool=_redis_pool) as r:
               await r.ping()
           checks["redis"] = "ok"
       except Exception as exc:
           checks["redis"] = f"fail: {exc.__class__.__name__}"
       ok = all(v == "ok" for v in checks.values())
       return JSONResponse(
           {"status": "ok" if ok else "degraded", "version": APP_VERSION, "checks": checks},
           status_code=200 if ok else 503
       )
   ```
5. Manter `/health` como alias de `/health/live` (retrocompat).
6. Apontar `healthcheck` em `docker-compose.backend.yml` e `docker-compose.dev.yml` para `/health/ready`.

**Verificar**:

```bash
# 1. Versão dinâmica:
curl -s http://localhost:8000/health | jq .version
# Deve retornar "0.7.0"

# 2. /health/ready com tudo ok:
curl -s http://localhost:8000/health/ready | jq
# Deve retornar checks: {postgres: ok, redis: ok}, status_code 200

# 3. /health/ready com postgres caído:
docker stop caloria_postgres
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/health/ready
# Deve retornar 503
docker start caloria_postgres

# 4. OpenAPI mostra versão correta:
curl -s http://localhost:8000/openapi.json | jq .info.version
```

**Commit**: `feat(health): separa liveness e readiness e usa versao dinamica`

---

### [ ] B2.4 — PR Rate limit + headers de segurança (AUD-040, AUD-041, AUD-052)

**Achados fechados**: AUD-040 (🟠), AUD-041 (🟡), AUD-052 (🟢) — 3 achados.

**Bundling motivado**: rate limit e security headers são "endurecer a borda" — a maioria dos arquivos tocados são o mesmo Caddyfile + middleware FastAPI.

**Fix**:

1. **AUD-040 backend** — adicionar `slowapi` a `pyproject.toml`. Em `app/main.py`:
   ```python
   from slowapi import Limiter, _rate_limit_exceeded_handler
   from slowapi.util import get_remote_address
   limiter = Limiter(key_func=get_remote_address, storage_uri=settings.REDIS_URL)
   app.state.limiter = limiter
   app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
   ```
   Decorar endpoints sensíveis:
   - `/auth/login`: `@limiter.limit("5/minute")`
   - `/auth/register`: `@limiter.limit("3/hour")`
   - `/ai/analyze-*`: `@limiter.limit("30/minute", key_func=lambda r: get_current_user_id(r))`
2. **AUD-041 + AUD-052 — bloco `header` e logs JSON no Caddy**:
   - Em `Caddyfile.backend` (deploy ativo), adicionar:
     ```caddy
     {$APP_DOMAIN} {
         header {
             X-Frame-Options "DENY"
             X-Content-Type-Options "nosniff"
             Referrer-Policy "strict-origin-when-cross-origin"
             Permissions-Policy "camera=(), microphone=(self), geolocation=()"
             Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; frame-ancestors 'none'"
             -Server
         }
         # ... resto
         log {
             output stdout
             format json    # <-- trocar de "console" para "json"
             level INFO
         }
     }
     ```
3. **AUD-052 rate limit no edge** (opcional, defesa em profundidade):
   - Instalar plugin `caddy-ratelimit` na imagem custom.
   - Adicionar diretiva `rate_limit` para `/api/auth/*` (5 req/s/IP).

**Verificar**:

```bash
# 1. Rate limit retorna 429 após N tentativas:
for i in $(seq 1 10); do curl -s -o /dev/null -w "%{http_code} " http://localhost:8000/api/v1/auth/login -d '{"email":"a","password":"b"}' -H "Content-Type: application/json"; done
# Deve aparecer 429 após a 5ª

# 2. Headers de segurança:
curl -sI https://seudominio.com/ | grep -E "X-Frame|X-Content|Referrer|Permissions|Content-Security"
# Todos presentes

# 3. Caddy log em JSON:
docker logs caloria_caddy | head -5 | jq .
# Deve ser JSON válido
```

**Commit**: `feat(seguranca): adiciona rate limit slowapi e headers de seguranca no caddy`

---

### [ ] B2.5 — PR Sentry + APM (AUD-051)

**Achados fechados**: AUD-051 (🟡) — 1 achado.

**Por que separado**: independente, gated por env var, esforço médio mas isolado.

**Fix**:

1. Criar conta Sentry (ou subir GlitchTip self-hosted). Pegar DSN.
2. Adicionar `sentry-sdk[fastapi,celery,sqlalchemy]>=2.0` a `backend/pyproject.toml`.
3. Em `backend/app/main.py`, antes do `app = FastAPI(...)`:
   ```python
   if settings.SENTRY_DSN:
       sentry_sdk.init(
           dsn=settings.SENTRY_DSN,
           environment=settings.APP_ENV,
           release=APP_VERSION,
           traces_sample_rate=0.1,
           profiles_sample_rate=0.0,
           integrations=[FastApiIntegration(), CeleryIntegration(), SqlalchemyIntegration()],
       )
   ```
4. Adicionar `SENTRY_DSN: str | None = None` ao `Settings`.
5. Tagging com `user_id` no `get_current_user_id`: `sentry_sdk.set_user({"id": user_id})`.
6. Tagging com `request_id` no `timing_middleware`: `sentry_sdk.set_tag("request_id", req_id)`.
7. Frontend: adicionar `@sentry/nextjs`, rodar `npx @sentry/wizard@latest -i nextjs`, gating pelo env `NEXT_PUBLIC_SENTRY_DSN`.

**Verificar**:

```bash
# 1. Dispara erro intencional e verifica no Sentry dashboard:
curl http://localhost:8000/api/v1/debug-error  # endpoint temporário que raise
# Conferir https://sentry.io/.../issues/

# 2. Tag user_id presente em eventos autenticados.
# 3. Tag request_id correlaciona logs ↔ Sentry events.
```

**Commit**: `feat(observabilidade): adiciona sentry para backend e frontend`

---

### [ ] B2.6 — PR Validação de inputs (AUD-009, AUD-010)

**Achados fechados**: AUD-009 (🟠), AUD-010 (🟡) — 2 achados.

**Por que aqui**: pequeno mas crítico para DoS — `image_base64` sem max_length é vetor de exhaustion. Encaixa bem depois de rate limit.

**Fix**:

1. Em `backend/app/schemas/ai.py`, `PhotoAnalysisRequest`:
   ```python
   image_base64: str = Field(..., max_length=10 * 1024 * 1024)  # 10 MB
   mime_type: Literal["image/jpeg", "image/png", "image/webp"]   # em vez de str livre
   ```
2. Aplicar `max_length` em campos texto livre identificados:
   - `notes` (vários schemas): `max_length=2000`
   - `MealAnalysisRequest.description`: já tem `max_length=2000` ✅
   - `AIQuestionRequest.question`: `max_length=1000`
   - `Reminder.message`: `max_length=500`
   - `raw_input` de qualquer schema: `max_length=5000`
3. Remover `meal_type: str | None` dead field em `ai/*` schemas (não é usado pelos parsers — confirmado no PASSO 8.3).

**Verificar**:

```bash
# 1. Payload muito grande → 422:
curl -X POST http://localhost:8000/api/v1/ai/analyze-photo \
  -H "Content-Type: application/json" \
  -d "{\"image_base64\":\"$(head -c 20000000 /dev/urandom | base64 -w0)\",\"mime_type\":\"image/jpeg\"}"
# Deve retornar 422 Unprocessable Entity

# 2. mime_type inválido → 422:
curl ... -d '{"mime_type":"text/plain","image_base64":"..."}'
```

**Commit**: `feat(schemas): adiciona max_length e mime_type literal em inputs sensiveis`

---

## Bloco 3 — Refatoração IA + cobertura de testes + índices

> **Goal**: deixar evolução segura. Cada um destes PRs entrega valor independente — podem ser feitos em ordem livre, exceto B3.1 que **bloqueia** todos os outros de testes.

### [ ] B3.1 — PR Fix fixture clean_db (AUD-042)

**Achados fechados**: AUD-042 (🟠) — 1 achado.

**Por que primeiro nesta onda**: hoje `pytest tests/unit/` reporta `49 passed, 49 errors`. Antes de adicionar **qualquer** teste novo, precisa parar de mentir.

**Fix**:

Em `backend/tests/unit/conftest.py`, adicionar:
```python
@pytest.fixture(autouse=True)
def clean_db() -> Iterator[None]:  # type: ignore[override]
    """No-op: testes unit nao dependem de banco."""
    yield
```

**Médio prazo (opcional, fora deste PR)**: remover `autouse=True` do `clean_db` raiz e exigir explicitamente via `@pytest.mark.usefixtures("clean_db")` nos integration tests.

**Verificar**:

```bash
cd backend && pytest tests/unit/ -q
# Esperado: "49 passed in <tempo>" (zero errors)
```

**Commit**: `test(unit): corrige fixture clean_db que truncava sem db disponivel`

---

### [ ] B3.2 — PR Cobertura crítica Onda 1 (AUD-043 parcial)

**Achados fechados**: AUD-043 (🟠 — parcial, Onda 1 do plano interno).

**Fix**:

1. Adicionar `fakeredis>=2.20` e `pytest-mock` a `pyproject.toml [dev]`.
2. Criar `backend/tests/unit/test_food_lookup.py` com 50-100 alimentos populares e seus matches esperados (baseline de regressão).
3. Criar `backend/tests/unit/test_context_builder.py` com snapshots de prompt gerado para 3 personas (atleta 25a, sedentário 50a, criança 8a).
4. Criar `backend/tests/unit/test_ai_client.py` com mock de `groq.AsyncGroq`: cache hit/miss, retry em 429, retry em 503, erro permanente em 401.
5. Criar `backend/tests/unit/test_auth_service.py` com fakeredis: blacklist_token (TTL correto), token reusado.
6. Travar em CI: `pytest --cov=app --cov-fail-under=70` no `ci.yml`.

**Verificar**:

```bash
cd backend && pytest --cov=app --cov-report=term --cov-fail-under=70 -q
# Deve passar (cobertura ≥ 70%)
```

**Commit**: `test(ai): adiciona unit tests para food_lookup, context_builder, ai_client, auth_service`

---

### [ ] B3.3 — PR Refator IA: decompor InsightsGenerator + BaseAIFoodParser + retry tipado (AUD-002, AUD-015, AUD-012, AUD-046 restante)

**Achados fechados**: AUD-002 (🟡), AUD-015 (🟡), AUD-012 (🟡), AUD-046 (🟢 — 3 erros restantes de tipo Groq) — 4 achados em 1 PR grande.

**⚠️ Risco médio**: pode revelar acoplamentos não previstos. Começar com AUD-015 (`BaseAIFoodParser`) que é independente, depois AUD-002.

**Fix**:

1. **AUD-015 — `BaseAIFoodParser`**:
   - Criar `backend/app/services/ai/_base_parser.py` com classe abstrata contendo `_lookup_and_fill` e `_estimate_macros_batch` (idênticos hoje em meal_parser e vision_parser).
   - `MealParser` e `VisionParser` herdam — só `_identify_foods` é abstrato.
2. **AUD-002 — quebrar `InsightsGenerator`**:
   - Criar `PeriodicInsightsService` com `daily_insight`, `weekly_insight`, `monthly_report`.
   - Criar `RecommendationsService` com `suggest_meal`, `nutritional_alerts`, `goal_adjustment_suggestion`.
   - Criar `QuestionAnsweringService` com `answer_question`.
   - Manter `insights_generator.py` como facade temporária se houver muitos callers.
3. **AUD-012 — retry tipado**:
   - Em `ai_client.py`, substituir `if "429" in str(exc)` por `except groq.RateLimitError`.
   - Substituir 4 tentativas × até 120s por 3 tentativas × até 30s (evita timeout do reverse proxy).
4. **AUD-046 restante — tipos Groq**:
   - Importar `ChatCompletionMessageParam` da `groq.types.chat`.
   - Anotar `messages: list[ChatCompletionMessageParam]` nos 3 sites.

**Verificar**:

```bash
# 1. Mypy 0 errors:
cd backend && mypy app/services/ai/

# 2. Testes IA passam (assume B3.2 já passou):
cd backend && pytest tests/unit/test_meal_parser.py tests/unit/test_vision_parser.py tests/unit/test_ai_client.py -v

# 3. Cobertura sobe (AUD-043 progride):
cd backend && pytest --cov=app/services/ai --cov-report=term
# Deve cobrir > 70% em cada arquivo de services/ai/
```

**Commit**: `refactor(ai): extrai base parser, decompoe insights_generator e tipa groq messages`

---

### [ ] B3.4 — PR Índices compostos no banco (AUD-030, AUD-031, AUD-032)

**Achados fechados**: AUD-030 (🟡), AUD-031 (🟡), AUD-032 (🟢) — 3 achados.

**Fix**:

1. Criar migração Alembic `alembic revision -m "indices compostos user_id_date e user_id_read"`.
2. Na migração:
   ```python
   def upgrade():
       op.create_index("ix_meals_user_id_date", "meals", ["user_id", sa.text("date DESC")])
       op.create_index("ix_weight_logs_user_id_date", "weight_logs", ["user_id", sa.text("date DESC"), sa.text("created_at DESC")])
       op.create_index("ix_mood_logs_user_id_date", "mood_logs", ["user_id", sa.text("date DESC")])
       op.create_index("ix_hydration_logs_user_id_date", "hydration_logs", ["user_id", sa.text("date DESC")])
       op.create_index("ix_notifications_user_id_read", "notifications", ["user_id", "read"], postgresql_where=sa.text("read = false"))
       # Drop UNIQUE legado de foods.name (AUD-032):
       op.drop_constraint("taco_foods_name_key", "foods", type_="unique")
   ```
3. `downgrade` correspondente (drop dos índices novos, recria UNIQUE).
4. Rodar `alembic upgrade head` e validar com EXPLAIN ANALYZE.

**Verificar**:

```bash
# 1. EXPLAIN das queries críticas usa o novo índice composto:
docker exec caloria_postgres psql -U caloria -d caloria_db -c "
  EXPLAIN ANALYZE SELECT * FROM meals WHERE user_id=1 AND date BETWEEN '2026-05-01' AND '2026-05-31' ORDER BY date DESC;
"
# Procurar "Index Scan using ix_meals_user_id_date"

# 2. Migration round-trip:
alembic downgrade -1
alembic upgrade head
```

**Commit**: `perf(db): adiciona indices compostos user_id_date e remove unique legado de foods`

---

### [ ] B3.5 — PR Frontend modularização + Web Speech API tipada (AUD-018, AUD-022)

**Achados fechados**: AUD-018 (🟡), AUD-022 (🟢) — 2 achados.

**Fix**:

1. Extrair de `frontend/app/(dashboard)/refeicoes/page.tsx` (1055 LOC):
   - Hook `useVoiceCapture()` em `frontend/lib/hooks/useVoiceCapture.ts` (resolve duplicação SpeechRecognition em 2 arquivos).
   - Componente `<MealAddByText />`, `<MealAddByPhoto />`, `<MealList />`, `<MealEditInline />`.
   - Objetivo: `refeicoes/page.tsx` ≤ 200 LOC.
2. Criar `frontend/types/speech.d.ts` com module augmentation para `SpeechRecognition`:
   ```ts
   declare global {
     interface Window {
       SpeechRecognition: typeof SpeechRecognition;
       webkitSpeechRecognition: typeof SpeechRecognition;
     }
   }
   ```
3. Remover os 6 `any` relacionados.
4. Mesmo padrão em `QuickAddModals.tsx`.

**Verificar**:

```bash
cd frontend
npm run lint            # 0 warnings, 0 errors (deve resolver AUD-022)
npx tsc --noEmit        # 0 errors
wc -l app/\(dashboard\)/refeicoes/page.tsx  # ≤ 200
rg ": any\b|as any\b" app components lib  # 0 hits
```

**Commit**: `refactor(frontend): extrai useVoiceCapture e componentiza pagina refeicoes`

---

## Bloco 4 — Hardening final e backlog frio

> **Goal**: zerar o backlog 🟢 e endereçar os médios remanescentes. PRs pequenos, ordem flexível, ideais para "tarefas de baixa demanda mental".

### [ ] B4.1 — PR Frente A: limpeza de routers (AUD-001, AUD-003, AUD-004, AUD-005)

**Achados fechados**: AUD-001 (🟡), AUD-003 (🟡), AUD-004 (🟢), AUD-005 (🟢) — 4 achados.

**Fix**:

1. **AUD-001** — extrair queries de `push.py` para `PushService` / criar `NotificationService` com `upsert_subscription`, `unsubscribe_by_endpoint`, `list_notifications`, `count_unread`, `mark_read`, `mark_all_read`.
2. **AUD-003** — criar `SubscribePushResponse(BaseModel)` e `MarkAllReadResponse(BaseModel { marked: int })`. Aplicar `response_model=` nos 2 endpoints.
3. **AUD-004** — em `meals.py:101`, trocar `raise HTTPException(...)` por `raise HTTPException(...) from None`.
4. **AUD-005** — em `weight.py:16`, trocar `le=200` por `le=100` para alinhar com o padrão.

**Verificar**:

```bash
cd backend && pytest tests/integration/test_meals.py tests/integration/test_logs.py -v
rg "(select|insert|update|delete)\(" app/api/v1/  # 0 hits (excluindo @router.delete)
```

**Commit**: `refactor(api): extrai queries de push para service e padroniza response models`

---

### [ ] B4.2 — PR Ruff cleanup + .dockerignore (AUD-045, AUD-048)

**Achados fechados**: AUD-045 (🟢), AUD-048 (🟡) — 2 achados.

**Fix**:

1. **AUD-045**:
   - Corrigir os 2 erros em `app/`: `app/api/v1/meals.py:1` (I001 auto-fix) + `meals.py:101` (já feito em B4.1 acima — AUD-004).
   - **Decisão sobre `scripts/`**: adicionar `extend-exclude = ["scripts/"]` em `pyproject.toml § [tool.ruff]`. Alinha com exclusão já existente do mypy. **Antes**, mover `from sqlalchemy import text as sa_text` para o topo de `scripts/import_off_local.py` (a F821 indica bug real — o import está em escopo errado).
2. **AUD-048**:
   - Criar `backend/.dockerignore` com lista do `09-qualidade.md § I.7`.
   - Criar `frontend/.dockerignore` idem.

**Verificar**:

```bash
cd backend && ruff check .   # 0 errors
docker build -t caloria-backend-test backend/  # observar redução do build context na saída
```

**Commit**: `chore: corrige ruff em app, exclui scripts e adiciona dockerignore`

---

### [ ] B4.3 — PR Versão sincronizada + ADRs novos (AUD-054 restante, AUD-055)

**Achados fechados**: AUD-054 (🟢, já parcialmente feito em B2.3), AUD-055 (🟢) — 2 achados.

**Fix**:

1. **AUD-054** — workflow de release:
   - Adicionar seção em `CONTRIBUTING.md`: "Release process — antes de mergear para main, PR de release atualiza CHANGELOG, pyproject e package.json em sincronia".
2. **AUD-055** — adicionar ADRs:
   - **ADR-009**: Frontend Vercel + backend Hetzner self-hosted (documenta o `Caddyfile.backend` como canônico; combina com AUD-053).
   - **ADR-010**: Workflow de release sincronizado.
   - **Retoque em ADR-002**: adicionar seção "Alternativas consideradas" (OpenAI gpt-4o-mini, Anthropic Claude Haiku, Ollama+Llama3.1 local) e o porquê de cada rejeição.

**Verificar**: revisão humana — não há comando automatizado.

**Commit**: `docs(adr): adiciona adr-009 deploy hybrid e adr-010 release workflow`

---

### [ ] B4.4 — PR Decidir Caddyfile dual (AUD-053)

**Achados fechados**: AUD-053 (🟢).

**⚠️ Decisão arquitetural pendente do mantenedor** — antes de implementar, escolher:

- **Opção 1** (preferida): remover `Caddyfile` + `docker-compose.yml` (full-stack). Frontend continua na Vercel. ADR-009 (B4.3) documenta a escolha.
- **Opção 2**: manter os 2, renomear para `*.fullstack.yml` e `*.backend.yml` com README explicando.

**Após decisão**, executar a opção escolhida. Atualizar `README.md` (a árvore cita `Caddyfile` — corrigir conforme decisão).

**Verificar**: visual.

**Commit**: `chore(deploy): remove caddyfile full-stack nao deployado` (ou equivalente conforme decisão)

---

### [ ] B4.5 — PR Refinos diversos backend (AUD-010 restante? AUD-011, AUD-017, AUD-029, AUD-033, AUD-034, AUD-035, AUD-036)

**Achados fechados**: 7 achados pequenos.

**Fix** (cada um < 30 min):

1. **AUD-011** — eliminar 12 `# type: ignore[arg-type]` em parsers IA: substituir por `TypedDict` ou `cast(...)`. Os 3 em `meal_service.py:45`, `utils.py:15`, `utils.py:18` são correções pontuais de tipo.
2. **AUD-017** — `extract_json_from_ai_response`: usar regex mais robusto que extrai JSON entre primeira `{`/`[` válido e último `}`/`]` correspondente; aceitar trailing comma com `json5` ou pré-processamento; testes unit cobrindo os 9 padrões documentados.
3. **AUD-029** — adicionar índice `ix_ai_conversations_updated_at` em `updated_at` (migração Alembic).
4. **AUD-033** — `20260306_adiciona_dessert_mealtype.py`: implementar `downgrade()` real (recria enum sem DESSERT, migra dados).
5. **AUD-034** — remover `MealSource.TELEGRAM` e `MealSource.WHATSAPP` do model + criar migração que altera o enum no DB (tabela vazia, sem dados a preservar).
6. **AUD-035** — ajustar `pool_size=5, max_overflow=10` em `core/database.py` (15 conn × 3 processos = 45 vs `max_connections=100`, com folga). Documentar decisão em ADR.
7. **AUD-036** — trocar `db_logger.info(...)` por `db_logger.debug(...)` em `core/database.py:52`. `LOG_LEVEL=DEBUG` reativa quando preciso.

**Verificar**:

```bash
cd backend && mypy app/                          # < 5 type ignores restantes (justificáveis)
cd backend && pytest tests/unit/ -k "extract_json" -v   # 9 padrões cobertos
alembic upgrade head && alembic downgrade -1 && alembic upgrade head  # round-trip
```

**Commit**: `refactor(backend): elimina type ignores, robustece extract_json e ajusta pool sizing`

---

### [ ] B4.6 — PR Refinos diversos frontend (AUD-019, AUD-020, AUD-023, AUD-024)

**Achados fechados**: 4 achados.

**Fix**:

1. **AUD-019** — adicionar `onMutate` com `setQueryData` (optimistic) em hooks de mutação: `useToggleReminder`, `useMarkNotificationRead`, `useUpdateWeight`. Rollback em `onError`.
2. **AUD-020** — em `frontend/lib/api.ts` e `app/providers.tsx`, gatear `console.log`/`console.error` com `if (process.env.NODE_ENV !== "production")`. Já existe pattern para `ReactQueryDevtools`.
3. **AUD-023** — Service Worker:
   ```js
   self.addEventListener("install", () => self.skipWaiting());
   self.addEventListener("activate", (e) => e.waitUntil(self.clients.claim()));
   ```
   Atualizar `manifest.ts`: adicionar `icons` para 144 e 384, `apple-touch-icon`, `screenshots`.
4. **AUD-024** — `npm install --save-dev @next/bundle-analyzer`; configurar em `next.config.mjs` gated por `process.env.ANALYZE`. Documentar em CONTRIBUTING como rodar (`ANALYZE=true npm run build`).

**Verificar**:

```bash
cd frontend && ANALYZE=true npm run build
# Abre report em new tab
rg "console\.(log|error)" lib/api.ts app/providers.tsx
# Todos devem estar gated com NODE_ENV
```

**Commit**: `feat(frontend): optimistic updates, console em prod gateado, sw skipwaiting e bundle analyzer`

---

### [ ] B4.7 — PR Frontend bug login + e2e baseURL (AUD-021, AUD-044)

**Achados fechados**: AUD-021 (🟠), AUD-044 (🟠) — 2 achados.

**Por que aqui**: AUD-021 é cosmético hoje mas combina bem com refator da e2e (AUD-044).

**Fix**:

1. **AUD-021** — em `frontend/app/api/auth/[...nextauth]/route.ts`, parar de ler `data.user.*`. Tirar `id` (não usado) e usar `email` em vez de "nome" para o session. **OU** atualizar backend `TokenResponse` em `app/api/v1/auth.py:37-50` para incluir `user: {id, name, email}` (mais útil futuramente).
2. **AUD-044** — `frontend/e2e/auth.spec.ts`:
   - Trocar constante `BASE_URL` por `process.env.E2E_BASE_URL ?? "http://localhost:3000"`.
   - Apertar matcher do teste de cadastro: aceitar apenas `(onboarding|dashboard)`.
   - Criar `frontend/e2e/fixtures.ts` com `createTestUser()` via `POST /api/v1/auth/register` antes da suite e cleanup no `afterAll`.

**Verificar**:

```bash
cd frontend && npx playwright test --reporter=list
# Tudo passando contra localhost
```

**Commit**: `fix(frontend): corrige contrato login e e2e baseurl com fixture global`

---

### [ ] B4.8 — PR Runbook operacional (AUD-056)

**Achados fechados**: AUD-056 (🟡) — 1 achado.

**Fix**:

Criar `docs/runbook-prod.md` com cenários no formato canônico (Sintoma / Verificar / Mitigação / Causa raiz). Mínimo: Groq 429 persistente, Push 410 em massa, Worker Celery travado, Restore Postgres (combina com B1.4), Rotação de secrets, Reset de banco em dev. Snippet de cenário-modelo em `docs/auditoria/11-dx-docs.md § K.1.b`.

**Verificar**: revisão humana.

**Commit**: `docs(deploy): adiciona runbook operacional para incidentes`

---

## Apêndice — Verificação global antes de cada push

Antes de `git push origin dev`, sempre rodar:

```bash
make check    # lint + typecheck + test-unit + test-frontend (se containers up)

# Ou manual se make check falhar por containers:
cd backend && ruff check . && mypy app/ && pytest tests/unit/ -q
cd frontend && npm run lint && npx tsc --noEmit && npm test
```

Se houver falha não-relacionada à mudança atual, **parar e investigar** (provavelmente é regressão de outra mudança ou teste flaky).

---

## Apêndice — Comandos úteis

```bash
# Reset rápido do banco dev (perde dados):
docker compose -f docker-compose.dev.yml down -v && docker compose -f docker-compose.dev.yml up -d

# Aplicar migrações:
docker compose exec backend alembic upgrade head

# Seed do banco nutricional (necessário após reset):
docker compose exec backend python -m scripts.import_off_local --from-csv /data/processed/alimentos_final.csv

# EXPLAIN de query no banco:
docker exec caloria_postgres psql -U caloria -d caloria_db -c "EXPLAIN ANALYZE SELECT ...;"

# Ver achado completo:
rg "^### AUD-016 " docs/auditoria/achados.md -A 30
```

---

## Apêndice — Referências cruzadas

- **Detalhamento completo dos achados**: [`achados.md`](achados.md)
- **Cronologia da auditoria**: [`log.md`](log.md)
- **Relatório executivo**: [`relatorio-preliminar.md`](relatorio-preliminar.md)
- **Notas por frente**:
    - [`01-arquitetura.md`](01-arquitetura.md), [`02-backend.md`](02-backend.md), [`03-ia.md`](03-ia.md)
    - [`04-frontend.md`](04-frontend.md), [`05-workers.md`](05-workers.md), [`06-banco.md`](06-banco.md)
    - [`07-seguranca.md`](07-seguranca.md), [`08-testes.md`](08-testes.md), [`09-qualidade.md`](09-qualidade.md)
    - [`10-observabilidade.md`](10-observabilidade.md), [`11-dx-docs.md`](11-dx-docs.md)
- **Artefatos brutos**: [`artefatos/`](artefatos/) — 49 arquivos (baselines + EXPLAIN ANALYZE + diffs)
