---
spec: 001-backlog-features-qa-v1
fase: A.1
slug_fase: profile-birthdate-schema
status: executado
tentativa: 1
reprovacoes: 0
sha_inicial: e712fe12aa7054b33ed881a1afaace657f727e4a
sha_final: 95fcbb0b6364831df4a12fe380d2175db34fa30d
range: e712fe12aa7054b33ed881a1afaace657f727e4a..95fcbb0b6364831df4a12fe380d2175db34fa30d
---

# FASE A.1 — Relatório de execução

## 1. Resumo do que foi feito

`UserProfile.age` (inteiro estático) foi substituído por `birth_date: date | None`
no modelo, e uma migração Alembic (`b8c9d0e1f2a3`) converte os registros
existentes derivando `birth_date = 01/01/(ano_atual − age)` e dropa `age`. O
`downgrade` recria `age` a partir de `birth_date`. AC-A1 é coberto por um teste de
migração que roda a conversão real contra Postgres. Migração aplicada e
round-trip (upgrade → downgrade → upgrade) validados no PG de dev.

## 2. Arquivos CRIADOS

| Arquivo | Propósito |
|---------|-----------|
| `backend/alembic/versions/20260702_b8c9d0e1f2a3_profile_birthdate.py` | Migração age→birth_date (add coluna, `UPDATE make_date`, drop age); `downgrade` inverso. SQLs de conversão expostas como constantes de módulo (`UPGRADE_SET_BIRTHDATE`/`DOWNGRADE_SET_AGE`) para reuso no teste. |
| `backend/tests/integration/test_migration_profile_birthdate.py` | Teste AC-A1: conversão real em PG, ano relativo (`date.today().year - 30`), verifica derivação e drop de `age`; cobre upgrade e downgrade. |

## 3. Arquivos ALTERADOS

| Arquivo | O que mudou |
|---------|-------------|
| `backend/app/models/profile.py` | `age: Mapped[int \| None]` → `birth_date: Mapped[date \| None]` (`Date`, nullable); imports `date`/`Date`. |

## 4. Confirmação do REUSO e decisões de design

- **Reuso confirmado:** a migração segue o padrão das migrações do repo
  (`20260702_a7b8c9d0e1f2_*`): `op.add_column`/`op.execute`/`op.drop_column`,
  `down_revision` encadeado ao head anterior (`a7b8c9d0e1f2`). O teste reusa o
  harness Postgres do `conftest.py` (fixture `db`) e o padrão `tests/integration/`.
- **Cast `::int` obrigatório (§5/A.1):** `EXTRACT(YEAR FROM …)` retorna
  `double precision`; sem `::int`, `make_date` falha em runtime. O cast está na SQL
  e é exatamente a que o teste exercita (fonte única — a SQL é importada da
  migração, não reescrita no teste).
- **Ano relativo no assert (§5/A.1):** o teste usa `date.today().year - 30`, nunca
  ano hard-coded, para não apodrecer na virada de ano.
- **Decisão do teste de migração (transacional):** em vez de só um teste de modelo,
  o teste leva `user_profiles` ao estado pré-migração (coluna `age`), semeia
  `age=30`, aplica a conversão real e confere a derivação **e** o drop de `age`;
  depois cobre o `downgrade`. Tudo dentro de uma transação **revertida no `finally`**
  — DDL no Postgres é transacional, então a tabela compartilhada volta ao formato do
  modelo e não contamina os demais testes. Isso dá evidência forte de AC-A1 (a spec
  permitia "teste de migração OU teste de modelo"; escolhi o mais faithful).
- **Desvio/nota de escopo (transitório, esperado):** remover `age` do modelo deixa
  referências a `profile.age` **fora do escopo travado de A.1** em
  `app/services/profile_service.py` (linhas 34, 40) e
  `app/workers/tasks/maintenance.py` (linhas 109, 115 — task `recalculate_tdee`).
  A.1 **não** as tocou (escopo travado: só `models/profile.py` + migração). Elas
  são resolvidas em A.2 (`tdee-mifflin-calc`), que passa a derivar a idade de
  `birth_date`. **Atenção ao avaliador:** `maintenance.py` **não** está na lista de
  "Arquivos alterados" de A.2 na spec — a spec subespecificou esse call-site; ele
  será tratado em A.2 como consequência necessária da mudança quebradora e
  documentado lá.

## 5. Comandos rodados + saídas reais

```text
# lint (ruff check) — arquivos da fase
$ ruff check app/models/profile.py \
    alembic/versions/20260702_b8c9d0e1f2a3_profile_birthdate.py \
    tests/integration/test_migration_profile_birthdate.py
All checks passed!

# format (ruff format --check) — arquivos da fase
$ ruff format --check <mesmos 3 arquivos>
3 files already formatted

# type-check (mypy) — arquivo da fase
$ mypy app/models/profile.py
Success: no issues found in 1 source file

# type-check app-wide (estado transitório documentado)
$ mypy app/
# 6 erros PRÉ-EXISTENTES em app/services/ai/ai_client.py (baseline do manifest)
# 4 erros TRANSITÓRIOS "UserProfile has no attribute age":
#   app/services/profile_service.py:34,40  (fora do escopo de A.1 → resolvido em A.2)
#   app/workers/tasks/maintenance.py:109,115 (idem)
# Found 10 errors in 3 files (checked 67 source files)

# teste da fase (AC-A1) — Postgres real
$ TEST_DATABASE_URL=postgresql+asyncpg://caloria:caloria@postgres:5432/caloria_test \
    pytest tests/integration/test_migration_profile_birthdate.py -v
tests/integration/test_migration_profile_birthdate.py::
  TestMigrationProfileBirthdate::test_age_converte_para_birthdate_e_volta PASSED
1 passed in 1.43s

# migração real em PG de dev (caloria_db)
$ alembic upgrade head        # a7b8c9d0e1f2 -> b8c9d0e1f2a3
# cols(user_profiles): birth_date presente, age ausente
$ alembic downgrade -1        # b8c9d0e1f2a3 -> a7b8c9d0e1f2
# cols(user_profiles): age presente, birth_date ausente
$ alembic upgrade head        # re-aplica sem erro

# grep de segredo/PII (esperado: 0)
# nenhum segredo tocado; apenas schema e SQL de conversão de datas.
```

> **Nota de ambiente (gate):** o dev-container **não** seta `TEST_DATABASE_URL`; o
> default (`localhost:5432`) não resolve o serviço `postgres` de dentro do
> container. Rodei o teste passando
> `TEST_DATABASE_URL=postgresql+asyncpg://caloria:caloria@postgres:5432/caloria_test`
> (mesmo procedimento das fases B.1/B.2).

## 6. Critérios de aceite da fase (com evidência)

- [x] **AC-A1** — `test_age_converte_para_birthdate_e_volta`: dado perfil com
  `age=30`, após a conversão real da migração `birth_date == date(ano_atual−30, 1, 1)`
  e a coluna `age` não existe mais (`information_schema.columns`); o `downgrade`
  recria `age == 30`. Verificado também via `alembic upgrade/downgrade head` no PG de
  dev.

## 7. Definition of Done da fase

- [x] Testes da fase verdes (1/1, AC-A1)
- [x] Comandos de validação limpos **nos arquivos tocados** (ruff/format/mypy do
  modelo verdes). App-wide mypy tem erros transitórios em arquivos **fora do escopo**
  travado, resolvidos em A.2 (documentado acima).
- [x] Escopo travado respeitado: só `models/profile.py` + migração; migração é a
  única forma de mudar schema; `birth_date` populado **antes** de dropar `age`;
  nenhuma migration existente editada.
- [x] Nenhum segredo/PII em log/DTO/exceção.
- [x] Commit em pt-BR (Conventional Commits), sem menção a autor/IA.

## 8. (Em rework) O que mudou nesta tentativa

N/A — primeira execução.

## 9. Itens em aberto / dúvidas para o avaliador

- **Mudança quebradora (declarada):** `age→birth_date` altera o schema persistido e
  (nas fases A.2/A.3) o contrato de API. Está prevista e resolvida na spec (OQ2/§8) e
  a migração tem `downgrade`. CI/CD desabilitado (§7): a migração foi aplicada **à
  mão** no PG de dev; em produção seguir o mesmo (rollout §7).
- **`maintenance.py` fora da lista de arquivos de A.2 na spec:** sinalizo desde já
  que a task `recalculate_tdee` referencia `profile.age` e precisará ser ajustada em
  A.2. Trato como extensão de escopo necessária da mudança quebradora.
