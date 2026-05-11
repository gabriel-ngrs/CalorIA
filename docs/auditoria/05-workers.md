# Frente E — Workers

**Plano:** ver `plano.md` § Frente E.

## Achados desta frente

- AUD-025 (🟠 alta) — `_run` em `reminders.py`, `reports.py`, `maintenance.py` chama `asyncio.get_event_loop()` deprecated desde Python 3.10; risco de `RuntimeError: Event loop is closed` em workers Celery
- AUD-026 (🟠 alta) — `dispatch_due_reminders` usa `datetime.now()` naive: hoje funciona porque todos os containers são `TZ=America/Sao_Paulo`, mas qualquer migração para UTC ou usuário fora de São Paulo quebra silenciosamente

## E.2 Padrão `_run` em tasks

Comando: `rg -n "asyncio\.get_event_loop\(\)" backend/app/`. Artefato: `artefatos/E1-get-event-loop.txt`.

| Arquivo | Linha | Trecho |
|---|---|---|
| `backend/app/workers/tasks/reminders.py` | 19-21 | `def _run(coro): return asyncio.get_event_loop().run_until_complete(coro)` |
| `backend/app/workers/tasks/reports.py` | 17-19 | idem |
| `backend/app/workers/tasks/maintenance.py` | 19-21 | idem |

As 3 cópias são **textualmente idênticas** — mesma assinatura, mesma docstring (`"""Executa uma coroutine de dentro de uma task Celery (thread síncrona)."""`), mesma implementação. Cada módulo declara sua própria função em vez de importar de um util comum.

### Por que é problema (Python 3.12)

`asyncio.get_event_loop()` tem 3 comportamentos possíveis:

1. **Há loop rodando na thread atual** → retorna esse loop. Não é o caso aqui (thread Celery síncrona).
2. **Há loop "current" registrado mas não rodando** → retorna ele. Acontece em invocações subsequentes na mesma thread se o loop não foi fechado.
3. **Não há loop registrado** → emite `DeprecationWarning` e cria um novo loop. Acontece na primeira chamada da thread.

Combinações que produzem **erro real**:

- Se uma task anterior chamou `loop.close()` ou houve exceção dentro de `run_until_complete` que fechou o loop → próxima `_run` na mesma thread lança `RuntimeError: Event loop is closed` em qualquer `await` interno.
- Em `Python 3.14`+ o caminho 3 será removido (passa a `RuntimeError: There is no current event loop in thread`).

O default do worker (`prefork` + `worker_prefetch_multiplier=1`) mitiga porque cada task tende a reusar o mesmo processo (não thread), mas **não elimina** — se a configuração migrar para `gevent`/`eventlet`/`solo` com pool de threads, ou se alguma task tiver bug que feche o loop, todas as tasks subsequentes falham até reinício do worker.

### Correção

Trocar por `asyncio.run(coro)`:

```python
def _run(coro: Any) -> Any:
    return asyncio.run(coro)
```

Cria event loop novo, executa a coroutine, fecha o loop. Semântica correta para "executar coroutine raiz a partir de código síncrono". É exatamente o caso de uso das tasks Celery aqui (cada task tem 1 coroutine `_*_async()` no topo).

Caveat: `asyncio.run()` falha com `RuntimeError` se já houver loop rodando na thread atual. Não acontece em workers Celery `prefork` (síncronos), mas se um dia migrar para `gevent`/`eventlet` (que monkey-patcham asyncio) precisará revisitar.

### Refator estrutural sugerido

As 3 cópias idênticas pedem um util compartilhado:

```python
# app/workers/_utils.py
def run_coro(coro: Any) -> Any:
    return asyncio.run(coro)
```

Cada task module: `from app.workers._utils import run_coro as _run`. Reduz duplicação e centraliza a política de event loop.

### Defesa em CI

Para pegar regressões análogas no futuro, adicionar `PYTHONWARNINGS=error::DeprecationWarning` no ambiente de testes (ou pelo menos `default::DeprecationWarning`) faria com que `asyncio.get_event_loop()` (e similares) falhassem o teste em vez de passar silenciosamente.

## E.3 `dispatch_due_reminders`: timezone

Comando de apoio: `docker exec caloria_postgres psql -U caloria -d caloria_db -c "SHOW timezone"` + `docker inspect caloria_postgres ...`. Artefato: `artefatos/E2-tz.txt`.

### Estado atual

| Item | Valor |
|---|---|
| `Reminder.time` (modelo) | `Time` (naive — sem `timezone=True`) |
| `dispatch_due_reminders` linha 37 | `now = datetime.now()` (naive) |
| Comparação | `reminder.time.hour != current_hour` AND `reminder.time.minute != current_minute` |
| Celery config | `timezone="America/Sao_Paulo"`, `enable_utc=True` |
| Postgres `SHOW timezone` | `America/Sao_Paulo` |
| Container envs (dev e prod) | `TZ=America/Sao_Paulo` em postgres, backend, celery_worker, celery_beat |
| `User.timezone` | **não existe** (apenas `created_at/updated_at` com `DateTime(timezone=True)`) |

### Por que funciona hoje

`datetime.now()` retorna o relógio local do processo. Como o container do worker tem `TZ=America/Sao_Paulo`, "agora naive" == "agora São Paulo". O usuário típico digita "08:00" pensando em hora de São Paulo, e a comparação coincide. **Coincidência de configuração**, não acerto de design.

### Cenários de quebra

1. **Migração para UTC** — default em Heroku/Railway/Render/Fly.io e em quase todos os clusters Kubernetes (`/etc/localtime` é UTC). Lembrete das 08:00 vira disparo às 05:00 (BRT) ou 11:00 (BRT). Não há nada no código que detecte essa migração.
2. **Usuário em outro fuso** — sem campo `User.timezone`, o front salva o `Time` como string. Worker compara contra `datetime.now()` em São Paulo. Para alguém em Lisboa, o lembrete das 08:00 dispara ao 12:00 deles.
3. **DST** — Brasil aboliu em 2019, mas outros países mantém. No "fall back" duas execuções caem na mesma hora local (lembrete dispara duas vezes); no "spring forward" pula uma hora (não dispara). `datetime.now()` naive não tem como diferenciar.

### Acoplamento invisível com Celery

A configuração do Celery (`timezone="America/Sao_Paulo"`+`enable_utc=True`, `celery_app.py:18-24`) cobre apenas a interpretação de crontabs do beat — a hora do **disparo** da task é correta. O **conteúdo** da task (`datetime.now()`) depende da TZ do processo Python e ignora `enable_utc`. Mudar `enable_utc=False` ou trocar a `timezone` no Celery não muda o problema; a única coisa que sustenta o comportamento atual é a env `TZ` do container.

### Correções

**Curto prazo (S)** — fixar TZ canônica no código, parar de depender da TZ do processo:

```python
from zoneinfo import ZoneInfo

APP_TZ = ZoneInfo("America/Sao_Paulo")  # ou settings.timezone

async def _dispatch_due_reminders_async() -> None:
    now = datetime.now(APP_TZ)
    ...
```

Isso resolve o cenário 1 (migração para UTC) sem mudar schema nem dados.

**Médio prazo (M)** — suportar usuários em outros fusos:

```python
# models/user.py
timezone: Mapped[str] = mapped_column(String(64), default="America/Sao_Paulo", server_default="America/Sao_Paulo")
```

Alembic migration adiciona com `server_default`; backfill desnecessário.

```python
for reminder in reminders:
    user_tz = ZoneInfo(reminder.user.timezone)
    now_local = datetime.now(user_tz)
    if reminder.time.hour != now_local.hour or reminder.time.minute != now_local.minute:
        continue
    ...
```

Cobertura de teste com `freezegun`/`time-machine` em ≥ 3 fusos (`America/Sao_Paulo`, `UTC`, `Asia/Tokyo`).

**Longo prazo (L)** — pré-calcular próximo disparo:

Adicionar `Reminder.next_fire_at: DateTime(timezone=True)`. A query da task vira `WHERE active AND next_fire_at <= now()`. Após disparar, recalcula `next_fire_at` baseado em `time` + `days_of_week` + `user.timezone`. Escala melhor (índice em `next_fire_at` substitui o full scan minuto-a-minuto) e elimina ambiguidade de DST porque o cálculo do próximo disparo é feito uma vez.

## Notas e contexto

(seções E.1, E.4-E.7 serão preenchidas nos PASSOS 6.3-6.5)
