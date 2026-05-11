# Frente E — Workers

**Plano:** ver `plano.md` § Frente E.

## Achados desta frente

- AUD-025 (🟠 alta) — `_run` em `reminders.py`, `reports.py`, `maintenance.py` chama `asyncio.get_event_loop()` deprecated desde Python 3.10; risco de `RuntimeError: Event loop is closed` em workers Celery

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

## Notas e contexto

(seções E.1, E.3-E.7 serão preenchidas nos PASSOS 6.2-6.5)
