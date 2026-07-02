---
spec: 001-backlog-features-qa-v1
fase: A.2
slug_fase: tdee-mifflin-calc
status: executado
tentativa: 1
reprovacoes: 0
sha_inicial: 1c476222314f1a974bbfa5be5a703a4de458506a
sha_final: cdda6538da015d5435b10b45eae413875bb43e18
range: 1c476222314f1a974bbfa5be5a703a4de458506a..cdda6538da015d5435b10b45eae413875bb43e18
---

# FASE A.2 — Relatório de execução

## 1. Resumo do que foi feito

`tdee.py` passou a usar **Mifflin-St Jeor**: `calculate_bmr` (TMB) exposto,
`calculate_tdee` reusa a mesma fórmula bruta (`_bmr_mifflin`) × multiplicador, e
`age_from_birthdate` deriva a idade. `ProfileService.update_profile` passou a
derivar a idade de `birth_date` e a calcular sobre `effective_weight =
current_weight or último WeightLog`, **sem sobrescrever** `current_weight`
(FR-A3). A task Celery `recalculate_tdee` (não listada na spec, mas dependente da
mudança quebradora) foi ajustada para derivar a idade de `birth_date`.

## 2. Arquivos CRIADOS

| Arquivo | Propósito |
|---------|-----------|
| `backend/tests/integration/test_profile_service.py` | AC-A3: TDEE usa último peso sem sobrescrever `current_weight`; sem peso permanece null; `current_weight` informado tem precedência. |

## 3. Arquivos ALTERADOS

| Arquivo | O que mudou |
|---------|-------------|
| `backend/app/services/nutrition/tdee.py` | Harris-Benedict → Mifflin-St Jeor; `_bmr_mifflin` (fonte única da fórmula), `calculate_bmr` (TMB, arredondado), `calculate_tdee` (TMB×multiplicador), `age_from_birthdate`. |
| `backend/app/services/profile_service.py` | Deriva idade de `birth_date`; `effective_weight = current_weight or WeightService.latest()`; guard passa a checar `effective_weight`/`birth_date`; **não** escreve `current_weight`. |
| `backend/app/workers/tasks/maintenance.py` | Task `recalculate_tdee`: guard usa `birth_date`; `age=age_from_birthdate(profile.birth_date)` (era `profile.age`). |
| `backend/tests/unit/test_tdee.py` | Valores conhecidos recalculados p/ Mifflin; testes de `calculate_bmr` e `age_from_birthdate` (inclui branch de aniversário futuro via `monkeypatch` de `date.today`). |

## 4. Confirmação do REUSO e decisões de design

- **Reuso confirmado (§4):** `WeightService.latest()` já existia e é a fonte do peso
  efetivo (OQ3); `_ACTIVITY_MULTIPLIERS` mantido intacto; padrão de service com
  `AsyncSession` preservado.
- **Fórmula em fonte única:** `_bmr_mifflin` centraliza `10*peso + 6.25*altura −
  5*idade + s` (s=+5 masc / −161 fem); `calculate_bmr` e `calculate_tdee` derivam
  dela (sem duplicar a fórmula) — o TDEE usa o BMR **não** pré-arredondado, evitando
  arredondamento duplo.
- **FR-A3 respeitado:** `current_weight` **não** é sobrescrito no fluxo de update;
  `effective_weight` é local ao cálculo. Teste
  `test_usa_ultimo_peso_sem_sobrescrever_current_weight` prova `current_weight is
  None` após o recálculo.
- **Idade derivada determinística:** `age_from_birthdate` conta anos completos
  (`(mês,dia) >= (mês,dia)`); testes usam datas relativas ao ano corrente e
  `monkeypatch` para o branch de aniversário futuro — não apodrecem na virada de ano.
- **Desvio de escopo declarado — `maintenance.py`:** a spec lista para A.2 apenas
  `tdee.py` e `profile_service.py`, mas a task `recalculate_tdee`
  (`app/workers/tasks/maintenance.py:107-118`) referenciava `profile.age`, que
  deixou de existir em A.1. Sem o ajuste, `mypy app/` não fecharia e o worker
  quebraria em runtime. **Decisão:** tratá-lo aqui como consequência necessária da
  mudança quebradora `age→birth_date`, com **diff mínimo** (só a derivação da idade;
  a lógica de sync de peso da task, que legitimamente escreve `current_weight`, foi
  preservada — é contexto diferente do fluxo de update do perfil). Sinalizado ao
  avaliador (já anunciado no relatório de A.1).

## 5. Comandos rodados + saídas reais

```text
# lint (ruff check) — arquivos da fase
$ ruff check app/services/nutrition/tdee.py app/services/profile_service.py \
    app/workers/tasks/maintenance.py tests/unit/test_tdee.py \
    tests/integration/test_profile_service.py
All checks passed!

# format (ruff format --check) — arquivos da fase
$ ruff format --check <mesmos 5 arquivos>
5 files already formatted

# type-check (mypy) — app-wide
$ mypy app/
# Apenas os 6 erros PRÉ-EXISTENTES em app/services/ai/ai_client.py (baseline do
# manifest). Os 4 erros transitórios de "age" (profile_service/maintenance) da
# fase A.1 estão RESOLVIDOS.
Found 6 errors in 1 file (checked 67 source files)

# testes unitários (Mifflin + bmr + age_from_birthdate)
$ pytest tests/unit/test_tdee.py -q
13 passed, 13 errors in 8.89s
#   → os 13 "errors" são no TEARDOWN (fixture clean_db do conftest raiz tenta
#     TRUNCATE, mas tests/unit/conftest.py stuba setup_test_database e não cria
#     tabelas). Quirk PRÉ-EXISTENTE do harness (ver FASE-B.1 nota de ambiente);
#     as 13 asserções passam.

# testes de integração (ProfileService, AC-A3) — Postgres real
$ TEST_DATABASE_URL=postgresql+asyncpg://caloria:caloria@postgres:5432/caloria_test \
    pytest tests/integration/test_profile_service.py -v
test_usa_ultimo_peso_sem_sobrescrever_current_weight PASSED
test_sem_peso_algum_tdee_permanece_null PASSED
test_current_weight_informado_tem_precedencia PASSED
3 passed in 4.68s

# grep de segredo/PII (esperado: 0)
# nenhum segredo tocado; apenas cálculo nutricional.
```

## 6. Critérios de aceite da fase (com evidência)

- [x] **AC-A2 (parcial — cálculo)** — `calculate_bmr`/`calculate_tdee` por Mifflin
  com valores conhecidos (`test_homem_valor_conhecido` BMR 1648.75;
  `test_homem_sedentario_valor_conhecido` TDEE 1978.5). A exposição via API
  (`bmr`/`tdee_calculated`/`formula` no `GET /users/me/profile`) é a fase **A.3**.
- [x] **AC-A3** — `test_usa_ultimo_peso_sem_sobrescrever_current_weight`: usuário com
  `WeightLog` e sem `current_weight` → após update, `tdee_calculated` != null e
  `current_weight` permanece `None`.

## 7. Definition of Done da fase

- [x] Testes da fase verdes (unit 13/13 asserções; integração 3/3)
- [x] Validação limpa nos arquivos tocados (ruff/format OK; mypy sem novos erros —
  só os 6 pré-existentes de `ai_client.py`)
- [x] Escopo travado respeitado quanto ao núcleo (`tdee.py`/`profile_service.py`);
  extensão a `maintenance.py` declarada e justificada (mudança quebradora);
  `_ACTIVITY_MULTIPLIERS` intocado; sem regra de negócio no endpoint.
- [x] Nenhum segredo/PII.
- [x] Commit em pt-BR (Conventional Commits), sem menção a autor/IA.

## 8. (Em rework) O que mudou nesta tentativa

N/A — primeira execução.

## 9. Itens em aberto / dúvidas para o avaliador

- **`maintenance.py` fora da lista da spec:** decisão de incluí-lo em A.2 (justificada
  em §4). Se o avaliador preferir tratá-lo noutra fase, sinalizar — mas deixá-lo de
  fora manteria `mypy` vermelho e o worker quebrado.
- **Mudança de valores (Harris→Mifflin):** TDEE exibido muda (Risco #3/OQ1);
  coberto por testes de valores conhecidos. O card do front (A.4) explicará a
  fórmula.
- **Teardown noise nos testes unitários:** quirk pré-existente do harness (não
  introduzido aqui); as asserções passam. Fora do escopo desta fase corrigir o
  `conftest`.
