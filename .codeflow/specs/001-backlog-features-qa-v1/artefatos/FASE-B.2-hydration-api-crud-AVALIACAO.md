---
spec: 001-backlog-features-qa-v1
fase: B.2
slug_fase: hydration-api-crud
tentativa: 1
veredito: RESSALVAS
score: 9.2
threshold: 8.5
range_avaliado: 19469a23bc5efbc8adb14b21b8139cb3febb9086..6c2f1d5a6371b0b32e8cee4b456585096deb3eb7
---

# FASE B.2 — Avaliação independente

## 1. Veredito e score

**Veredito:** RESSALVAS · **Score:** 9.2 / threshold 8.5

Os endpoints `DELETE`/`PUT /api/v1/hydration/{log_id}` estão finos, corretos e fiéis à
spec: delegam ao `HydrationService`, mapeiam `False`/`None` → 404 por posse, não tocam
`POST`/`GET`. Os 3 ACs (B1/B2/B3) passam e verifiquei-os de forma independente. **Porém**,
uma sondagem própria do endpoint `PUT` (que não constava do relatório) confirmou um
defeito **alcançável pela API pública**: `PUT {"amount_ml": null}` gera um **500
(NotNullViolationError)** não tratado, em vez de um 4xx. É um IMPORTANTE (gap de validação
de input — `rules/security.md`), tratável com um one-liner. Como há ≥1 IMPORTANTE e o
score ≥ threshold com zero BLOQUEANTES, o veredito é **RESSALVAS**: a fase precisa de
rework + reavaliação antes de fechar.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 5.0 | `hydration.py:50-71` DELETE(204/404)+PUT(200/404); ACs B1/B2/B3 verdes (`TestHydrationCrudAPI` 5/5). `POST`/`GET` intocados; sem regra no router. |
| 2 | Arquitetura e direção de dependências | 3 | 5.0 | Handlers só orquestram `HydrationService.delete/update` (`hydration.py:56,68`); zero lógica de negócio no router (constitution "endpoints finos"). |
| 3 | Segurança / LGPD / multi-tenant | 3 | 3.5 | Posse correta e testada: log alheio ⇒ 404 antes de qualquer efeito (o `get_by_id` do service precede). **Mas** validação de input incompleta: `PUT {"amount_ml": null}` → 500 não tratado (ver Achado IMPORTANTE 1). |
| 4 | Reusar/espelhar, não duplicar | 3 | 5.0 | Reusa métodos de B.1; espelha o padrão `Depends(get_current_user_id)`/`Depends(get_db)` dos handlers existentes. |
| 5 | Padrões de domínio/aplicação | 2 | 5.0 | Idêntico ao estilo de `create_hydration`; `HydrationLogResponse.model_validate`. |
| 6 | Local e nomes dos arquivos | 2 | 5.0 | Exatamente `api/v1/hydration.py` + `tests/integration/test_logs.py` (§5). |
| 7 | Qualidade de código | 2 | 4.0 | `ruff`/`format`/`mypy` limpos nos arquivos da fase (mypy: só baseline `ai_client.py`). −1.0 pelo path do `PUT` que aceita `null` e cai em 500. |
| 8 | Testes e cobertura | 2 | 4.0 | 5 testes cobrem 204, 200+total, 404 cross-user (DELETE+PUT) e 404 inexistente. Faltou o caso de payload inválido (`null`/vazio) — exatamente o que teria pego o 500. |
| 9 | Migration safety (se aplicável) | 2 | [—] | Fase não altera schema. |

Média ponderada (excluída a dim. 9): (3·5 + 3·5 + 3·3.5 + 3·5 + 2·5 + 2·5 + 2·4 + 2·4) / 20 = 91.5/100 → **9.2/10**.

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

- **IMPORTANTE 1 — `PUT /hydration/{id}` com `amount_ml`/`date`/`time` `null` explícito
  retorna 500 não tratado.** `backend/app/api/v1/hydration.py:61-71` chama
  `HydrationService.update`, que (`log_service.py:145`) faz
  `model_dump(exclude_unset=True)` + `setattr`. `exclude_unset` **não** exclui um campo
  fornecido explicitamente como `null`; ele chega ao `setattr(log, "amount_ml", None)` e
  o commit viola `amount_ml NOT NULL` (`models/hydration_log.py:20-22`) →
  `IntegrityError` não capturada → **HTTP 500**. Verifiquei empiricamente (sondagem
  temporária, revertida):
  - `PUT {"amount_ml": null}` → **500** `null value in column "amount_ml" ... violates not-null constraint`.
  - `PUT {}` (vazio) → 200 no-op (ok).
  - `PUT {"amount_ml": 0}` → 422 (validador `gt=0` ok).
  Alcance real: só o **dono** do log dispara (a checagem de posse precede), sem corrupção
  (rollback) nem vazamento — por isso é IMPORTANTE, não BLOQUEANTE. Mas é um erro de
  servidor alcançável pela API pública sobre input type-válido, o que a
  `rules/security.md` ("toda entrada … validada antes de uso") pede evitar.
  **Correção sugerida (uma linha, em B.2 ou no service de B.1):** trocar para
  `data.model_dump(exclude_none=True)` no `HydrationService.update`, **ou** rejeitar
  payload com campos `null`/vazio no endpoint (422). Acrescentar um teste
  `test_put_amount_null_retorna_422` para travar a regressão.

## 5. Sugestões

- **404 sem `detail`** (`hydration.py:58,70`): coerente com "não vazar posse"; se quiser
  UX melhor, um `detail` genérico em pt-BR (sem revelar existência/posse) é aceitável.
  Não bloqueante.
- Ao corrigir o IMPORTANTE 1, considere cobrir também `date`/`time` no teste de update
  (hoje só `amount_ml` é exercitado no caminho feliz).

## 6. Comandos rodados + saídas reais

Rodados por mim na ponta de `dev` (HEAD `d90dac2`; `6c2f1d5` confirmado ancestral),
dentro de `caloria_backend`, com `TEST_DATABASE_URL` → serviço `postgres` (equivalente ao
`make test-integration` do CI, que o dev-container não seta sozinho).

```text
$ git merge-base --is-ancestor 6c2f1d5 HEAD ; echo $?
0

# Testes de API da fase (B.2)
$ pytest tests/integration/test_logs.py::TestHydrationCrudAPI -v
...::test_delete_do_proprio_log_retorna_204 PASSED
...::test_put_edita_amount_e_reflete_no_total PASSED
...::test_delete_de_log_de_outro_usuario_retorna_404 PASSED
...::test_put_de_log_de_outro_usuario_retorna_404 PASSED
...::test_delete_log_inexistente_retorna_404 PASSED
5 passed in 5.84s

# Sondagem independente do PUT (teste temporário, DEPOIS removido; árvore limpa)
[body vazio]      status=200 body={"id":1,...,"amount_ml":200,...}     # no-op, ok
[amount_ml=0]     status=422 body={"detail":[{"type":"greater_than",...}]}  # ok
[amount_ml=null]  → sqlalchemy.exc.IntegrityError: null value in column "amount_ml"
                    of relation "hydration_logs" violates not-null constraint  → HTTP 500

# Lint / type-check
$ ruff check app/api/v1/hydration.py tests/integration/test_logs.py   → All checks passed!
$ ruff format --check <mesmos>                                        → 2 files already formatted
$ mypy app/   → Found 6 errors in 1 file (todos PRÉ-EXISTENTES em ai_client.py)

$ git status --porcelain   → (vazio; temp de sondagem removido)
```

Árvore de trabalho intacta ao final; nenhuma alteração de código feita pelo avaliador.

## 7. Itens da fase / DoD não atendidos

- O critério de conclusão de B.2 (§5: "testes de API verdes; `make test-integration` +
  `make check` backend verdes") está cumprido para os ACs declarados. O que trava o
  fechamento é a **DoD transversal §9 / NFR-5 + `rules/security.md`**: a mudança de
  comportamento do `PUT` tem um caminho de input (`null` explícito) que produz 500 sem
  teste e sem validação — endereçar via IMPORTANTE 1.

## 8. Divergências entre o relatório e o código real

- O relatório descreve fielmente os handlers, o reuso de B.1 e a ausência de regra no
  router. **Lacuna, não falsidade:** o item 9 do relatório de B.1 já sinalizava o risco
  do `null`/partial-update "para B.2", e o relatório de B.2 não o retomou nem cobriu —
  o defeito passou. A independência da avaliação (sondar o endpoint em vez de confiar no
  "5/5 verdes") foi o que o expôs.
- Contagem: "suíte de logs 24/24" confere hoje (B.1+B.2 na branch).
