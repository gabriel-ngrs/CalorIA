---
spec: 001-backlog-features-qa-v1
fase: A.2
slug_fase: tdee-mifflin-calc
tentativa: 1
veredito: APROVADO
score: 9.7
threshold: 8.5
range_avaliado: 1c476222314f1a974bbfa5be5a703a4de458506a..cdda6538da015d5435b10b45eae413875bb43e18
---

# FASE A.2 — Avaliação independente

## 1. Veredito e score

**Veredito:** APROVADO · **Score:** 9.7 / threshold 8.5

Mifflin-St Jeor com fórmula em fonte única (`_bmr_mifflin`), `calculate_bmr`,
`calculate_tdee` e `age_from_birthdate`. FR-A3 honrado: `effective_weight` local, sem
sobrescrever `current_weight`, provado por teste. AC-A2 (cálculo) e AC-A3 cobertos.
Nenhum BLOQUEANTE, nenhum IMPORTANTE.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 4 | AC-A2(cálculo)/AC-A3 cobertos (`tests/unit/test_tdee.py`, `tests/integration/test_profile_service.py`); `_ACTIVITY_MULTIPLIERS` intocado; endpoint sem regra. Dedução: `maintenance.py` está fora da lista literal de arquivos de A.2 — extensão necessária da mudança quebradora, declarada e com diff mínimo |
| 2 | Arquitetura e direção de dependências | 3 | 5 | regra em `services/`; `WeightService.latest()` reusado; `tdee.py` puro (sem I/O) |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | `WeightService.latest(user_id)` sempre por `user_id`; sem segredo/PII no diff |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | `_bmr_mifflin` centraliza a fórmula; `calculate_bmr`/`calculate_tdee` derivam dela; TDEE usa o BMR **não** pré-arredondado (evita arredondamento duplo) |
| 5 | Padrões de domínio/aplicação | 2 | 5 | `ProfileService.update_profile` mantém o padrão de service com `AsyncSession` |
| 6 | Local e nomes dos arquivos | 2 | 5 | `nutrition/tdee.py`, `profile_service.py`, testes em `unit/` e `integration/` — corretos |
| 7 | Qualidade de código | 2 | 5 | `age_from_birthdate` com lógica de aniversário correta e testada; anotações completas |
| 8 | Testes e cobertura | 2 | 5 | valores conhecidos (BMR 1648.75; TDEE 1978.5), branch de aniversário futuro via `monkeypatch`, datas relativas; AC-A3 prova `current_weight is None` pós-cálculo |
| 9 | Migration safety | 2 | — | não se aplica (fase sem schema) |

Score = (4·3+5·3+5·3+5·3+5·2+5·2+5·2+5·2) / (5·20) · 10 = 97/100 · 10 = **9.7**.

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

Nenhum.

## 5. Sugestões

- **`maintenance.py` fora da lista de arquivos da spec (aceito):** a task
  `recalculate_tdee` referenciava `profile.age` (removido em A.1); sem o ajuste,
  `mypy app/` não fecharia e o worker quebraria. A correção é o diff mínimo (só a
  derivação da idade) e a lógica de sync de peso — que legitimamente escreve
  `current_weight` num contexto diferente do fluxo de update — foi preservada. Tratamento
  correto de consequência de mudança quebradora (constitution universal); a spec
  subespecificou o call-site. Sem ação.
- **Ruído de teardown nos testes unitários:** `13 passed, 13 errors` — os "errors" são no
  TRUNCATE do teardown (`conftest` raiz vs stub de `tests/unit/conftest.py`), quirk
  pré-existente do harness; as 13 asserções passam. Fora do escopo desta fase.

## 6. Comandos rodados + saídas reais

```text
$ ruff check --no-cache app/services/nutrition/tdee.py app/services/profile_service.py \
    app/workers/tasks/maintenance.py tests/unit/test_tdee.py tests/integration/test_profile_service.py
All checks passed!

$ mypy app/
Found 6 errors in 1 file (checked 67 source files)   # só pré-existentes de ai_client.py;
                                                      # os 4 erros transitórios de "age" da A.1 estão RESOLVIDOS

$ pytest tests/unit/test_tdee.py -q
13 passed, 13 errors        # errors = teardown TRUNCATE (quirk pré-existente); asserções passam

$ TEST_DATABASE_URL=…@localhost:5432/caloria_test pytest tests/integration/test_profile_service.py -q
3 passed                    # usa último peso sem sobrescrever; sem peso→null; current_weight tem precedência
```

Verificação adicional: em `maintenance.py:98-99`, `profile.current_weight` é atribuído
com `latest_wl.weight_kg` (não-None, garantido por `continue`) **antes** do `calculate_tdee`
— o guard sem checagem de `current_weight` é seguro e é o mesmo padrão pré-existente.

## 7. Itens da fase / DoD não atendidos

Nenhum. Gate ("testes verdes; TDEE deixa de ser null quando há `WeightLog`") comprovado
por `test_usa_ultimo_peso_sem_sobrescrever_current_weight`.

## 8. Divergências entre o relatório e o código real

Nenhuma. Fonte única da fórmula, uso do BMR não-arredondado no TDEE e não-sobrescrita de
`current_weight` conferem com o diff `1c476222..cdda6538` e com os testes reexecutados.
