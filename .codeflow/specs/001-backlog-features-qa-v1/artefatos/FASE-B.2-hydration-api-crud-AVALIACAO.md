---
spec: 001-backlog-features-qa-v1
fase: B.2
slug_fase: hydration-api-crud
tentativa: 2
veredito: APROVADO
score: 9.9
threshold: 8.5
range_avaliado: 19469a23bc5efbc8adb14b21b8139cb3febb9086..0bfebc9329536e0b66a2c87da03b6bd472c18457
---

# FASE B.2 — Avaliação independente (tentativa 2 — rework)

> Reavaliação após o rework do achado IMPORTANTE da tentativa 1 (RESSALVAS 9.2). O
> histórico da avaliação anterior está preservado no git (commit `4114201`). Pareamento
> por (`fase`, `tentativa`) conforme ARTIFACTS_SPEC §2.11.2.

## 1. Veredito e score

**Veredito:** APROVADO · **Score:** 9.9 / threshold 8.5

O único achado IMPORTANTE — `PUT /hydration/{id}` com `{"amount_ml": null}` → HTTP 500
(NotNullViolation) — está **corrigido e travado por regressão**. O fix é um
`model_validator(mode="after")` em `HydrationLogUpdate` que distingue campo **omitido**
("manter") de `null` **explícito** (inválido em coluna NOT NULL) via `model_fields_set`,
devolvendo **422 antes de tocar o banco**. Reproduzi de forma independente o antigo cenário
de 500: agora é 422 verde. Escopo do rework é mínimo e correto (só `schemas/logs.py` +
`test_logs.py`; `hydration.py` e o service intocados). As duas sugestões da §5 anterior
(`date`/`time` no update; happy-path de `time`) foram incorporadas como testes. Zero
BLOQUEANTES, zero IMPORTANTES.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 5.0 | ACs B1/B2/B3 verdes; escopo do rework mínimo (só schema+testes, `git show 0bfebc9`); endpoints seguem finos (`hydration.py:50-71`, inalterado). |
| 2 | Arquitetura e direção de dependências | 3 | 5.0 | Validação declarativa no schema (`logs.py:49-61`): o FastAPI devolve 422 na parse do body, antes do handler/DB — colocação correta, sem regra no router. |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5.0 | Posse 404 mantida e testada (cross-user delete+put). **Gap de validação de input fechado:** `null` explícito → 422 (não mais 500), cumprindo `rules/security.md` ("toda entrada validada antes de uso"). Mensagem de erro sem PII. |
| 4 | Reusar/espelhar, não duplicar | 3 | 5.0 | `model_validator`/`model_fields_set` idiomático de Pydantic v2; reusa `HydrationService.delete/update` de B.1; nenhuma duplicação. |
| 5 | Padrões de domínio/aplicação | 2 | 5.0 | Handlers idênticos ao estilo `create_hydration`; validador tipado com `Self` (Py 3.12). |
| 6 | Local e nomes dos arquivos | 2 | 5.0 | Rework em `schemas/logs.py` + `tests/integration/test_logs.py`, coerente com a §5. |
| 7 | Qualidade de código | 2 | 5.0 | `ruff`/`format` limpos; `mypy app/` só o baseline `ai_client.py` (o `-> Self`/`model_validator` tipam certo). Comentário do validador registra o "por quê" não-óbvio (constitution). |
| 8 | Testes e cobertura | 2 | 4.5 | 9 testes: happy (amount, **time**), 404 (cross-user delete+put, inexistente), **422 null (amount+date)**, no-op vazio→200. Regressão do 500 travada. −0.5: não há caso de payload **misto** (campo válido + outro `null`) nem asserção da mensagem 422 — o validador é field-agnostic, então é reforço, não lacuna real. |
| 9 | Migration safety (se aplicável) | 2 | [—] | Fase não altera schema. |

Média ponderada (excluída a dim. 9): (3·5 + 3·5 + 3·5 + 3·5 + 2·5 + 2·5 + 2·5 + 2·4.5) / 20 = 99/100 → **9.9/10**.

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

Nenhum. **O IMPORTANTE 1 da tentativa 1 está resolvido:**
- Antes: `PUT {"amount_ml": null}` → 500 `IntegrityError` (NotNullViolation).
- Agora: `HydrationLogUpdate._rejeita_null_explicito` (`schemas/logs.py:49-61`) levanta
  `ValueError` para qualquer campo em `model_fields_set` com valor `None` → **422** antes
  do banco. Verificado por mim: `test_put_amount_null_retorna_422` e
  `test_put_date_null_retorna_422` verdes; `test_put_vazio_e_no_op_retorna_200` confirma
  que o `{}` (omitido) segue no-op 200. A escolha de "rejeitar (422)" em vez de
  `exclude_none` (no-op silencioso) é a semântica de API mais correta e está bem
  justificada no relatório.

## 5. Sugestões

- **404 sem `detail` pt-BR** (`hydration.py:58,70`): deixado deliberadamente (documentado
  no item 9 do EXECUCAO). Não bloqueante; coerente com "não vazar posse".
- **Cobertura extra (opcional):** um caso de payload misto `{"amount_ml": 350, "time": null}`
  (deve dar 422) e uma asserção do corpo do erro fechariam 100% do contrato do validador.
  Não é pendência — o validador já é agnóstico ao campo.

## 6. Comandos rodados + saídas reais

Rodados por mim na ponta de `dev` (HEAD `6fab27e`; `0bfebc9` confirmado ancestral),
dentro de `caloria_backend`/`caloria_frontend`.

```text
$ git merge-base --is-ancestor 0bfebc9 HEAD ; echo $?
0

# Testes de API da fase (9, pós-rework)
$ pytest tests/integration/test_logs.py::TestHydrationCrudAPI -v
...::test_delete_do_proprio_log_retorna_204 PASSED
...::test_put_edita_amount_e_reflete_no_total PASSED
...::test_delete_de_log_de_outro_usuario_retorna_404 PASSED
...::test_put_de_log_de_outro_usuario_retorna_404 PASSED
...::test_delete_log_inexistente_retorna_404 PASSED
...::test_put_amount_null_retorna_422 PASSED     # ← era 500 na tentativa 1
...::test_put_date_null_retorna_422 PASSED
...::test_put_vazio_e_no_op_retorna_200 PASSED
...::test_put_atualiza_time PASSED
9 passed in 9.08s

# Suíte de logs completa (sem regressão)
$ pytest tests/integration/test_logs.py -q
............................  [100%]
28 passed in 20.97s

# Lint / type-check
$ ruff check app/schemas/logs.py app/api/v1/hydration.py tests/integration/test_logs.py  → All checks passed!
$ ruff format --check app/schemas/logs.py tests/integration/test_logs.py                  → 2 files already formatted
$ mypy app/   → Found 6 errors in 1 file (todos PRÉ-EXISTENTES em ai_client.py)

# Reconferência de B.3 (o fix encosta em schema; pedido na avaliação anterior)
$ docker exec caloria_frontend npx jest __tests__/lib/hooks/useLogs.test.ts
  Test Suites: 1 passed · Tests: 13 passed, 13 total   → B.3 intacto

$ git status --porcelain   → (vazio)
```

Árvore de trabalho intacta ao final; nenhuma alteração de código feita pelo avaliador.

## 7. Itens da fase / DoD não atendidos

Nenhum. O critério de conclusão de B.2 (§5) e a DoD transversal §9/NFR-5 +
`rules/security.md` estão agora cumpridos: endpoints finos, testes de integração verdes
(incl. o gate que `make check` não roda), e o caminho de input malformado (`null`) tratado
com 422 e coberto por teste de regressão.

## 8. Divergências entre o relatório e o código real

Nenhuma. O relatório de tentativa 2 descreve fielmente o validador, a escolha de projeto
(rejeitar vs. `exclude_none`), os 4 testes adicionados e a nota de range (os commits de B.3
entre os dois SHAs não tocam arquivos de B.2 — confirmei via `git show 0bfebc9`, que altera
só `schemas/logs.py` + `test_logs.py`). `reprovacoes: 1` coerente com um veredito
não-APROVADO anterior; este APROVADO não incrementa e fecha a fase.
