---
spec: 001-backlog-features-qa-v1
fase: B.2
slug_fase: hydration-api-crud
status: executado
tentativa: 1
reprovacoes: 0
sha_inicial: 19469a23bc5efbc8adb14b21b8139cb3febb9086
sha_final: 6c2f1d5a6371b0b32e8cee4b456585096deb3eb7
range: 19469a23bc5efbc8adb14b21b8139cb3febb9086..6c2f1d5a6371b0b32e8cee4b456585096deb3eb7
---

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
| `backend/tests/integration/test_logs.py` | Classe `TestHydrationCrudAPI` (5 testes): 204 + resumo zera; PUT 350 reflete no total; DELETE/PUT de log alheio → 404; DELETE inexistente → 404. |

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
# testes da fase (API CRUD)
$ pytest tests/integration/test_logs.py::TestHydrationCrudAPI -q
.....                                                                    [100%]
5 passed in 5.48s

# suíte de logs completa (B.1 + B.2, sem regressão)
$ pytest tests/integration/test_logs.py -q
........................                                                 [100%]
24 passed in 18.02s

# lint
$ ruff check app/api/v1/hydration.py tests/integration/test_logs.py
All checks passed!

# ruff format --check (após format do test_logs.py)
1 file already formatted

# type-check
$ mypy app/   → 6 erros, todos em app/services/ai/ai_client.py (PRÉ-EXISTENTES);
#   nenhum em hydration.py / log_service.py / schemas/logs.py.

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

- [x] Testes da fase verdes (5/5; suíte de logs 24/24).
- [x] `make test-integration` (equivalente CI) + lint/format/mypy limpos nos arquivos da fase.
- [x] Escopo travado: endpoint fino, sem regra no router; `POST`/`GET` não alterados.
- [x] Nenhum segredo/PII exposto.
- [x] Commit em pt-BR (Conventional Commits), sem menção a autor/IA.

## 8. (Em rework) O que mudou nesta tentativa

N/A — primeira execução.

## 9. Itens em aberto / dúvidas para o avaliador

- O 404 usa `HTTPException(status_code=404)` sem `detail` custom (resposta genérica).
  Coerente com "não vazar posse", mas se o avaliador quiser uma mensagem pt-BR, é
  ajuste trivial.
- Testes de posse criam o 2º usuário inline (via fixture `db`) porque o conftest só
  provê `test_user`; padrão consistente com o resto do arquivo.
