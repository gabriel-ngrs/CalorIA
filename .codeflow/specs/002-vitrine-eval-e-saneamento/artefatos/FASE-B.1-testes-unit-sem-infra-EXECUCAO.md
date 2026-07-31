---
spec: 002-vitrine-eval-e-saneamento
fase: B.1
slug_fase: testes-unit-sem-infra
status: executado
tentativa: 1
reprovacoes: 0
sha_inicial: 4b58f76f31931aa47a5281ff0ac0bc88dec795a6
sha_final: 425830930d64a876cf1997db54d681a4f44a64fc
range: 4b58f76f31931aa47a5281ff0ac0bc88dec795a6..425830930d64a876cf1997db54d681a4f44a64fc
---

# FASE B.1 — Relatório de execução

## 1. Resumo do que foi feito

A chamada `asyncio.run(_reset_schema())` saiu do corpo do módulo
`backend/tests/conftest.py` e a criação de schema passou para dentro da fixture
`setup_test_database`, que já existia e só fazia teardown. O conftest de unit passou
a sobrepor **duas** fixtures autouse do pai — `setup_test_database` **e** `clean_db`
— porque era `clean_db` (autouse na raiz) que arrastava todo teste unitário para o
banco. Resultado: `pytest tests/unit/` roda em 2,83 s sem Postgres e sem Redis, e a
contagem de testes fica inalterada.

> **Nota de execução paralela:** esta fase foi executada concorrentemente com a A.2
> (arquivos disjuntos: `backend/tests/` vs `docs/auditoria/`). O `sha_inicial` acima
> é o HEAD no momento do commit desta fase; o HEAD no momento em que o trabalho
> começou era `cb2e4ca` (o mesmo da A.2). O `range` cobre exclusivamente o commit
> desta fase.

## 2. Arquivos CRIADOS

Nenhum.

## 3. Arquivos ALTERADOS

| Arquivo | O que mudou |
|---------|-------------|
| `backend/tests/conftest.py` | Removido `asyncio.run(_reset_schema())` do corpo do módulo e o import `asyncio`. `_reset_schema()` passou a usar o `_engine` do módulo em vez de criar um engine descartável. `setup_test_database` (session-scoped, autouse) agora faz `await _reset_schema()` antes do `yield` e mantém o `drop_all` + `dispose` no teardown, em `try/finally` aninhado. Docstring reescrita registrando o *porquê* (loop-bound). |
| `backend/tests/unit/conftest.py` | Stub de `setup_test_database` corrigido de `-> None` com `yield` + dois `type: ignore` para `-> Iterator[None]` bem tipado. **Adicionado override de `clean_db`** — a peça que faltava: sem ele, o `autouse=True` da raiz puxava `setup_test_database` e executava `TRUNCATE` no teardown de todo teste unitário. |

## 4. Confirmação do REUSO e decisões de design

- **Reuso confirmado:** a fixture `setup_test_database` **já existia** (`conftest.py:72`)
  e o stub em `tests/unit/conftest.py:12-18` **já existia** — conforme o mapa
  NOVO/REUSADO da §4 da spec ("`backend/tests/unit/conftest.py` (stub já existe)").
  Nada foi criado do zero; ambos foram corrigidos.

- **Como a intenção documentada em `conftest.py:64-68` foi preservada.** O comentário
  original justificava o import-time por três motivos, e cada um foi endereçado:
  1. *"tabelas existam antes de qualquer coleta, independentemente da ordem"* →
     preservado por `scope="session", autouse=True`. Validado rodando `tests/unit
     tests/integration` **e** `tests/integration tests/unit` — 293 passed nas duas ordens.
  2. *"engine async é loop-bound"* → o projeto já declara
     `asyncio_default_fixture_loop_scope = "session"` **e**
     `asyncio_default_test_loop_scope = "session"` no `pyproject.toml`. Logo a fixture
     de sessão, o `clean_db` e os testes compartilham um único event loop, e usar o
     mesmo `_engine` em setup/TRUNCATE/teardown é seguro. Foi exatamente por isso que
     o engine descartável pôde ser substituído pelo `_engine`: o motivo original de
     um engine separado (loop distinto no import) deixou de existir.
  3. *"uma seleção só-unit rodaria sem schema e o TRUNCATE falharia no teardown"* →
     resolvido na raiz: em seleção só-unit o TRUNCATE **não roda mais**, porque
     `clean_db` está sobreposto.

- **Decisão de design (a mais relevante):** sobrepor `clean_db` em `tests/unit/`
  **em vez de** remover o `autouse=True` de `clean_db` na raiz. Remover o autouse na
  raiz tiraria o isolamento por TRUNCATE dos testes de integração — seria "alterar o
  comportamento para acomodar a fixture", precisamente o que o escopo travado proíbe.
  O conftest mais próximo vence por resolução do pytest, então a sobreposição é local
  e não afeta integração.

- **Decisão:** manter `autouse=True` em `setup_test_database` na raiz em vez de
  torná-la sob demanda. As duas opções são equivalentes para a árvore com banco (já
  que `clean_db` depende dela), e o autouse é a leitura mais fiel de "schema antes de
  qualquer teste".

- **Nenhum teste existente foi alterado** — verificável por `git show --stat`: o
  commit toca exatamente 2 arquivos, ambos `conftest.py`. Nada em `backend/app/`.

## 5. Comandos rodados + saídas reais

### 5.1 AC-5 — o gate principal, com infra provadamente parada

```text
$ docker ps -q | wc -l
0
$ (exec 3<>/dev/tcp/127.0.0.1/5432) && echo ABERTA || echo fechada    → fechada
$ (exec 3<>/dev/tcp/127.0.0.1/6379) && echo ABERTA || echo fechada    → fechada

# ANTES (conftest de HEAD~1, restaurado temporariamente, mesma infra parada)
$ .venv/bin/python -m pytest tests/unit/ -q --collect-only
/usr/lib/python3.12/asyncio/selector_events.py:651: in sock_connect
    return await fut
/usr/lib/python3.12/asyncio/selector_events.py:691: in _sock_connect_cb
    raise OSError(err, f'Connect call failed {address}')
E   ConnectionRefusedError: [Errno 111] Connect call failed ('127.0.0.1', 5432)
        ← nem a COLETA passava

# DEPOIS
$ .venv/bin/python -m pytest tests/unit/ -q
........................................................................ [ 36%]
........................................................................ [ 72%]
.......................................................                  [100%]
199 passed in 2.83s
```

### 5.2 Lint e typecheck

```text
$ .venv/bin/python -m ruff check .            → All checks passed!
$ .venv/bin/python -m ruff format --check .   → 119 files already formatted
$ .venv/bin/python -m mypy app/               → Success: no issues found in 72 source files

# bônus: os dois conftest tocados, em strict
$ mypy tests/conftest.py tests/unit/conftest.py
Success: no issues found in 2 source files
        ← e sem nenhum `type: ignore`, contra os 2 que existiam antes
```

### 5.3 Testes de integração (com a infra no ar)

```text
ANTES  (conftest original):        4 failed, 90 passed, 5 skipped
DEPOIS (conftest novo):            4 failed, 90 passed, 5 skipped   ← idênticos, os MESMOS 4 testes
DEPOIS + REDIS_URL corrigido:      94 passed, 5 skipped

Suíte completa depois da mudança:  293 passed, 5 skipped
  — nas duas ordens: `tests/unit tests/integration` e `tests/integration tests/unit`
```

Os 4 testes que falham são `test_auth.py::TestResetPassword` e falhavam **antes e
depois**, identicamente. Causa: `REDIS_URL=redis://redis:6379` no `.env` da raiz é o
hostname interno do Docker, irresolvível a partir do host. Com
`REDIS_URL=redis://localhost:6389/0` os 4 passam. **Falha de Ambiente, não regressão.**

### 5.4 Contagem de testes coletados — inalterada

| | antes | depois |
|---|---|---|
| `tests/unit/` | 199 | 199 |
| `tests/integration/` | 99 | 99 |
| **total** | **298** | **298** |

## 6. Critérios de aceite da fase (com evidência)

- [x] **AC-5** (FR-B1) — *dado* um ambiente sem Postgres e sem Redis, *quando* se roda
      `pytest tests/unit/`, *então* a coleta e a execução completam com sucesso.
      Evidência: §5.1 — portas 5432/6379 fechadas, `docker ps` vazio, `199 passed in
      2.83s`; e o mesmo comando com o conftest de `HEAD~1` falhando com
      `ConnectionRefusedError` já na coleta.

## 7. Definition of Done da fase

- [x] Testes da fase verdes — 199 unit sem infra; 293 na suíte completa com infra
- [x] Comandos de validação limpos — `ruff check`, `ruff format --check`, `mypy app/`
- [x] Escopo travado respeitado — nenhum teste marcado `skip`, nenhum teste existente
      alterado, nada em `backend/app/`; o commit toca exatamente 2 `conftest.py`
- [x] Nenhum segredo/PII em log/DTO/exceção
- [x] Commit em pt-BR: `test(backend): cria schema em fixture e libera testes unit de infra`
- [x] Critério de conclusão: contagem de testes coletados inalterada (298 antes e depois)

## 8. (Em rework) O que mudou nesta tentativa

N/A — primeira execução.

## 9. Itens em aberto / dúvidas para o avaliador

1. **A spec está desatualizada na contagem.** §1 e a Fase B.1 afirmam "129 testes
   unitários"; o número real é **199**, antes e depois. Vale corrigir na spec para
   não induzir o avaliador a suspeitar de perda de testes.

2. **`make test-integration` não foi validado pelo alvo do Makefile.** O alvo é
   `$(COMPOSE_DEV) exec backend pytest tests/integration/`, isto é, roda *dentro* do
   container. A validação acima foi feita a partir do host, com a infra subida por
   `docker compose -f docker-compose.dev.yml up -d postgres redis`. O resultado é
   equivalente, mas não é literalmente o mesmo comando.

3. **Armadilha de ambiente descoberta (fora do escopo, não corrigida):**
   `docker-compose.dev.yml` publica Postgres em **5442** e Redis em **6389**, mas o
   default de `TEST_DATABASE_URL` no conftest é `localhost:5432`. Rodar integração a
   partir do host exige `TEST_DATABASE_URL=...@localhost:5442/caloria_test`. Não
   toquei — está fora dos dois arquivos declarados.

4. **`backend/uv.lock` está desatualizado (fora do escopo, não corrigido):** não
   contém `aiosmtplib` nem os extras de dev (`ruff`, `mypy`), então
   `uv run --frozen pytest` quebra na coleta de `test_email_service.py`. A validação
   usou o `.venv` local (gitignorado). **Isso é relevante para a Fase B.2**, porque o
   CI instala dependências — se o CI usar `uv sync --frozen`, vai quebrar. Recomendo
   um `uv lock` numa fase posterior.
