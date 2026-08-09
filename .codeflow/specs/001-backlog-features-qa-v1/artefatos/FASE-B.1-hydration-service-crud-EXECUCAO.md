---
spec: 001-backlog-features-qa-v1
fase: B.1
slug_fase: hydration-service-crud
status: executado
tentativa: 1
reprovacoes: 0
sha_inicial: cd062907825ea150344a399c426821297d48e6a7
sha_final: 134fb7c9cbcb83573fc0e0bdd259d174618ebc3f
range: cd062907825ea150344a399c426821297d48e6a7..134fb7c9cbcb83573fc0e0bdd259d174618ebc3f
---

# FASE B.1 — Relatório de execução

## 1. Resumo do que foi feito

Adicionei ao `HydrationService` os métodos `get_by_id`, `delete` e `update`, todos
com **posse obrigatória por `user_id`** (log inexistente ou de outro usuário ⇒
`None`/`False`, nunca operação por `id` puro). Criei o schema `HydrationLogUpdate`
(campos `amount_ml`/`date`/`time` opcionais, mesmos `Field` do `Create`). Nenhum
endpoint foi exposto (isso é B.2). Cobertura por 6 testes de service.

## 2. Arquivos CRIADOS

Nenhum arquivo novo (apenas adições a arquivos existentes).

## 3. Arquivos ALTERADOS

| Arquivo | O que mudou |
|---------|-------------|
| `backend/app/schemas/logs.py` | Novo `HydrationLogUpdate` (opcionais). Aliases `_DateType`/`_TimeType` para os campos `date`/`time` não sombrearem o tipo homônimo ao resolver a anotação. |
| `backend/app/services/log_service.py` | `HydrationService.get_by_id/delete/update` com filtro por `id` **e** `user_id`; import de `HydrationLogUpdate`. |
| `backend/tests/integration/test_logs.py` | Classe `TestHydrationServiceCRUD` com 6 testes (get/delete/update do próprio log + rejeição de log alheio). |

## 4. Confirmação do REUSO e decisões de design

- **Reuso confirmado:** modelo `HydrationLog` e o padrão `select(...).where(...)` /
  `scalar_one_or_none()` já usado em `WeightService.get_by_date`; `model_dump(
  exclude_unset=True)` já usado no padrão upsert do arquivo. `get_by_id` centraliza
  a checagem de posse — `delete`/`update` o reusam (não reimplementam o filtro).
- **Decisão de design (desvio menor, justificado):** o campo Pydantic `date`
  sombreava o tipo `date` quando recebe default (`= None`), quebrando a resolução da
  anotação (`TypeError: unsupported operand for |: NoneType, NoneType`). Introduzi
  os aliases de módulo `_DateType = date` / `_TimeType = time` e usei-os na anotação
  do `HydrationLogUpdate`. Alternativa `from __future__ import annotations` **não**
  resolve (Pydantic resolve o forward-ref com o namespace da classe, onde `date`
  já é `None`). É a mudança de menor diff que mantém os nomes de campo exigidos pela
  API (`amount_ml`/`date`/`time`). Fora isso, nenhum desvio da spec.

## 5. Comandos rodados + saídas reais

```text
# testes da fase (service CRUD)
$ docker exec -e TEST_DATABASE_URL=...@postgres:5432/caloria_test caloria_backend \
    pytest tests/integration/test_logs.py::TestHydrationServiceCRUD -q
......                                                                   [100%]
6 passed in 3.52s

# suíte de logs completa (sem regressão)
$ pytest tests/integration/test_logs.py -q
...................                                                      [100%]
19 passed in 13.26s

# lint
$ ruff check app/schemas/logs.py app/services/log_service.py tests/integration/test_logs.py
All checks passed!

# ruff format --check (após format do test_logs.py)
3 files already formatted

# type-check
$ mypy app/
Found 6 errors in 1 file (checked 67 source files)
# → todos os 6 erros em app/services/ai/ai_client.py (PRÉ-EXISTENTES, ver
#   manifest "mypy 6 erros em ai_client.py"); nenhum nos arquivos desta fase.

# grep de segredo/PII (esperado: 0)
# nenhum segredo tocado; apenas lógica de CRUD e schema.
```

> **Nota de ambiente (gate):** neste dev-container `make test-integration` roda
> `pytest tests/integration/` **sem** setar `TEST_DATABASE_URL`, e o default
> (`localhost:5432`) não resolve o serviço `postgres` de dentro do container (o CI
> seta a var). Rodei o equivalente exato do CI passando
> `TEST_DATABASE_URL=postgresql+asyncpg://caloria:caloria@postgres:5432/caloria_test`.
> B.1 não adiciona endpoint, então o gate crítico de integração é de B.2.

## 6. Critérios de aceite da fase (com evidência)

B.1 é a base de service; os ACs de posse são exercitados a nível de service:
- [x] **AC-B1** (posse) — `test_get_by_id_de_outro_usuario_retorna_none`,
  `test_delete_de_outro_usuario_retorna_false`, `test_update_de_outro_usuario_retorna_none`
  provam que o log de outro usuário é intocável (o log de A permanece).
- [x] **AC-B2** (delete) — `test_delete_do_proprio_log`: `delete` retorna True e o
  `get_by_id` seguinte retorna None.
- [x] **AC-B3** (update) — `test_update_amount_do_proprio_log`: 200→350 aplicado;
  campos não enviados (`date`) intactos.

## 7. Definition of Done da fase

- [x] Testes da fase verdes (6/6; suíte de logs 19/19).
- [x] Comandos de validação limpos nos arquivos tocados (mypy: só erros pré-existentes em `ai_client.py`).
- [x] Escopo travado respeitado: nenhum endpoint exposto; `WeightService`/`MoodService` intocados; ownership sempre presente.
- [x] Nenhum segredo/PII em log/DTO/exceção.
- [x] Commit em pt-BR (Conventional Commits), sem menção a autor/IA.

## 8. (Em rework) O que mudou nesta tentativa

N/A — primeira execução.

## 9. Itens em aberto / dúvidas para o avaliador

- Os testes de service usam a fixture `db` e criam `HydrationLog` direto (não via
  API) — coerente com o nível "service" de B.1; a validação de contrato HTTP fica em B.2.
- Aliases `_DateType`/`_TimeType`: se o avaliador preferir outra forma de resolver o
  shadowing (ex.: renomear o campo — impossível, o contrato exige `date`/`time`), é
  ponto de discussão. A solução atual é a de menor diff e mantém o contrato.
