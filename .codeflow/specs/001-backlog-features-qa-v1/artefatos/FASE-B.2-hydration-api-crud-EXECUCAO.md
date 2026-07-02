---
spec: 001-backlog-features-qa-v1
fase: B.2
slug_fase: hydration-api-crud
status: rework
tentativa: 2
reprovacoes: 1
sha_inicial: 19469a23bc5efbc8adb14b21b8139cb3febb9086
sha_final: 0bfebc9329536e0b66a2c87da03b6bd472c18457
range: 19469a23bc5efbc8adb14b21b8139cb3febb9086..0bfebc9329536e0b66a2c87da03b6bd472c18457
---

> **Nota de range (batch B):** as três fases da Track B foram executadas em
> sequência antes da avaliação, então os commits de B.3 (`5287aa4`, `fa902e5`,
> `6fc3ca9`) ficam **entre** o `sha_inicial` de B.2 e este `sha_final`. Eles tocam
> só frontend (`types/`, `useLogs.ts`, `hidratacao/page.tsx`) — **nenhum** arquivo
> de B.2. O diff efetivo deste rework é o commit **`0bfebc9`** (só
> `schemas/logs.py` + `tests/integration/test_logs.py`).

# FASE B.2 — Relatório de execução

## 1. Resumo do que foi feito

Expus `DELETE /api/v1/hydration/{log_id}` (204) e `PUT /api/v1/hydration/{log_id}`
(200, `HydrationLogResponse`), ambos endpoints finos que só orquestram o
`HydrationService.delete/update` de B.1. Log inexistente ou de outro usuário ⇒
`HTTPException(404)`. Cobertura por 5 testes de API (httpx `AsyncClient`), incluindo
posse cruzada com um **segundo usuário** autenticado.

## 2. Arquivos CRIADOS

Nenhum (adições a arquivos existentes).

## 3. Arquivos ALTERADOS

| Arquivo | O que mudou |
|---------|-------------|
| `backend/app/api/v1/hydration.py` | Novos handlers `delete_hydration` (204/404) e `update_hydration` (200/404); import de `HTTPException` e `HydrationLogUpdate`. |
| `backend/app/schemas/logs.py` | **(rework)** `HydrationLogUpdate` ganhou `model_validator(mode="after")` que rejeita `null` explícito (`amount_ml`/`date`/`time`) via `model_fields_set` → 422, distinguindo campo omitido (manter) de `null` (inválido em coluna NOT NULL). |
| `backend/tests/integration/test_logs.py` | Classe `TestHydrationCrudAPI`: 5 testes originais (204/200/404) **+ 4 do rework**: `test_put_amount_null_retorna_422`, `test_put_date_null_retorna_422`, `test_put_vazio_e_no_op_retorna_200`, `test_put_atualiza_time` (happy-path de `time`). |

## 4. Confirmação do REUSO e decisões de design

- **Reuso confirmado:** os handlers reusam `HydrationService.delete/update` (B.1) —
  nenhuma regra de negócio no router, apenas mapear `False`/`None` → 404 (constitution
  "endpoints finos"). Padrão de `Depends(get_current_user_id)`/`Depends(get_db)`
  idêntico aos handlers `POST`/`GET` já existentes.
- **Decisão de design:** ordem de rotas — `DELETE`/`PUT /{log_id}` não colidem com
  `GET /today` e `GET /history` (métodos e/ou paths distintos; `/{log_id}` só casa
  DELETE/PUT). `POST`/`GET` existentes intocados. Nenhum desvio da spec.

## 5. Comandos rodados + saídas reais

```text
# testes da fase (API CRUD) — após o rework, 9 testes
$ pytest tests/integration/test_logs.py::TestHydrationCrudAPI -v
...::test_delete_do_proprio_log_retorna_204 PASSED
...::test_put_edita_amount_e_reflete_no_total PASSED
...::test_delete_de_log_de_outro_usuario_retorna_404 PASSED
...::test_put_de_log_de_outro_usuario_retorna_404 PASSED
...::test_delete_log_inexistente_retorna_404 PASSED
...::test_put_amount_null_retorna_422 PASSED     # ← o antigo 500, agora 422
...::test_put_date_null_retorna_422 PASSED
...::test_put_vazio_e_no_op_retorna_200 PASSED
...::test_put_atualiza_time PASSED
9 passed in 9.03s

# suíte de logs completa (B.1 + B.2, sem regressão)
$ pytest tests/integration/test_logs.py -q
............................                                             [100%]
28 passed in 21.15s

# reconferência de B.3 (o fix encosta em schema/service — pedido do avaliador)
$ docker exec caloria_frontend npx jest __tests__/lib/hooks/useLogs.test.ts
Tests: 13 passed, 13 total

# lint
$ ruff check app/schemas/logs.py tests/integration/test_logs.py
All checks passed!

# ruff format --check
2 files already formatted

# type-check
$ mypy app/   → 6 erros, todos em app/services/ai/ai_client.py (PRÉ-EXISTENTES);
#   nenhum em schemas/logs.py / hydration.py / log_service.py.

# grep de segredo/PII (esperado: 0) — nenhum segredo tocado.
```

> **Gate de integração (NFR-5):** B.2 adiciona endpoints, cujos testes vivem em
> `tests/integration/`. `make check` **não** roda essa pasta; rodei o equivalente
> ao `make test-integration` do CI passando
> `TEST_DATABASE_URL=postgresql+asyncpg://caloria:caloria@postgres:5432/caloria_test`
> (o dev-container não seta a var por padrão — ver nota de ambiente em FASE-B.1).
> Resultado: 24/24 verdes em `tests/integration/test_logs.py`.

## 6. Critérios de aceite da fase (com evidência)

- [x] **AC-B1** — `test_delete_de_log_de_outro_usuario_retorna_404` e
  `test_put_de_log_de_outro_usuario_retorna_404`: usuário B recebe 404 e o total de
  A permanece 200.
- [x] **AC-B2** — `test_delete_do_proprio_log_retorna_204`: 204 e `total_ml` do
  `get_day_summary` vai de 200 → 0.
- [x] **AC-B3** — `test_put_edita_amount_e_reflete_no_total`: PUT 200→350 retorna 200
  e `total_ml` do dia reflete 350.

## 7. Definition of Done da fase

- [x] Testes da fase verdes (9/9; suíte de logs 28/28).
- [x] `make test-integration` (equivalente CI) + lint/format/mypy limpos nos arquivos da fase.
- [x] Escopo travado: endpoint fino, sem regra no router; `POST`/`GET` não alterados.
- [x] **Validação de input completa:** `null` explícito em campo NOT NULL → 422 (não mais 500).
- [x] Nenhum segredo/PII exposto.
- [x] Commit em pt-BR (Conventional Commits), sem menção a autor/IA.

## 8. (Em rework) O que mudou nesta tentativa

**Tentativa 2 — corrige o único achado IMPORTANTE da avaliação (tentativa 1, RESSALVAS 9.2).**

- **Achado IMPORTANTE 1** — `PUT {"amount_ml": null}` → HTTP 500 (NotNullViolation),
  porque `model_dump(exclude_unset=True)` não exclui um campo enviado como `null`
  explícito; ele chegava ao `setattr(log, "amount_ml", None)` e violava a constraint
  NOT NULL em runtime.
  - **Correção:** adicionei um `model_validator(mode="after")` em `HydrationLogUpdate`
    (`schemas/logs.py`) que percorre `model_fields_set` e **rejeita qualquer campo
    presente cujo valor seja `None`** (`amount_ml`/`date`/`time`), levantando
    `ValueError` → **422** antes de tocar o banco. Escolhi a opção "rejeitar no
    endpoint (422)" das duas sugeridas pela avaliação (em vez de `exclude_none` no
    service, que tornaria o `null` um no-op silencioso), por ser o comportamento de
    API mais correto: `null` explícito num campo NOT NULL é erro do cliente, não
    "manter". Campo **omitido** continua sendo "manter" (não entra em `fields_set`).
  - **Testes adicionados:** `test_put_amount_null_retorna_422` (trava a regressão do
    500), `test_put_date_null_retorna_422` (cobre `date`/`time`, sugestão §5 da
    avaliação), `test_put_vazio_e_no_op_retorna_200` (garante que `{}` continua 200
    no-op) e `test_put_atualiza_time` (happy-path de `time`, que antes só exercitava
    `amount_ml` — sugestão §5).
- **Reconferência de B.3** (o avaliador alertou que o fix poderia encostar em B.3):
  a UI já valida `ml > 0` antes do PUT e não muda; `jest useLogs.test.ts` segue 13/13.
- **Sem ampliação de escopo:** só `schemas/logs.py` (o validador) e `test_logs.py`
  (os 4 testes). `hydration.py` e o service não mudaram.

## 9. Itens em aberto / dúvidas para o avaliador

- O 404 usa `HTTPException(status_code=404)` sem `detail` custom (resposta genérica).
  Coerente com "não vazar posse", mas se o avaliador quiser uma mensagem pt-BR, é
  ajuste trivial (sugestão §5 da avaliação, não bloqueante — deixei como está).
- O validador de `null` mora no **schema** (`HydrationLogUpdate`), não no router — é a
  materialização de "rejeitar payload nulo no endpoint": o FastAPI valida o body pelo
  schema e devolve 422 antes de entrar no handler. Se o avaliador preferir a checagem
  explícita dentro do handler, é reorganização, não mudança de comportamento.
- Testes de posse criam o 2º usuário inline (via fixture `db`) porque o conftest só
  provê `test_user`; padrão consistente com o resto do arquivo.
