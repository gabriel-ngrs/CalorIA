---
spec: 001-backlog-features-qa-v1
fase: A.1
slug_fase: profile-birthdate-schema
tentativa: 1
veredito: APROVADO
score: 9.8
threshold: 8.5
range_avaliado: e712fe12aa7054b33ed881a1afaace657f727e4a..95fcbb0b6364831df4a12fe380d2175db34fa30d
---

# FASE A.1 — Avaliação independente

## 1. Veredito e score

**Veredito:** APROVADO · **Score:** 9.8 / threshold 8.5

Migração `age → birth_date` com conversão de dados correta, `downgrade` inverso,
cadeia de revisão íntegra (`b8c9d0e1f2a3` ← `a7b8c9d0e1f2`, head único) e teste de
migração real em Postgres cobrindo AC-A1 (upgrade **e** downgrade). Escopo travado
respeitado. Nenhum BLOQUEANTE, nenhum IMPORTANTE.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 5 | AC-A1 coberto por `tests/integration/test_migration_profile_birthdate.py:44-110`; escopo travado (só `models/profile.py` + migração) respeitado; nenhuma migration existente editada |
| 2 | Arquitetura e direção de dependências | 3 | 5 | migração segue o molde do repo (`op.add_column`/`op.execute`/`op.drop_column`); `down_revision="a7b8c9d0e1f2"` = head anterior; grep confirma head único |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | só schema/SQL de datas; nenhum segredo/PII no diff |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | SQLs expostas como constantes (`UPGRADE_SET_BIRTHDATE`/`DOWNGRADE_SET_AGE`) e **importadas** pelo teste — fonte única, sem reescrita |
| 5 | Padrões de domínio/aplicação | 2 | 5 | `Mapped[date \| None]` + `mapped_column(Date, nullable=True)` no padrão SQLAlchemy 2.x do projeto |
| 6 | Local e nomes dos arquivos | 2 | 5 | `alembic/versions/20260702_b8c9d0e1f2a3_profile_birthdate.py` e teste em `tests/integration/` — convenção correta |
| 7 | Qualidade de código | 2 | 4 | limpo e comentado no "por quê" (cast `::int`); dedução leve: no commit da A.1 isolado, `profile_service`/`maintenance` ficam app-wide-red (transitório, resolvido em A.2) e a derivação `01/01` é aproximada — ambos declarados/aceitos |
| 8 | Testes e cobertura | 2 | 5 | teste roda a conversão **real** em PG, ano relativo (`date.today().year-30`), cobre drop de `age` e round-trip; rollback transacional no `finally` evita contaminação |
| 9 | Migration safety | 2 | 5 | `upgrade` popula `birth_date` **antes** de dropar `age`; `downgrade` presente; cast `::int` obrigatório aplicado; revisada à mão |

Score = (5·3+5·3+5·3+5·3+5·2+5·2+4·2+5·2+5·2) / (5·22) · 10 = 108/110 · 10 = **9.8**.

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

Nenhum.

## 5. Sugestões

- **Estado transitório do commit A.1 (não-bloqueante):** no `sha_final` isolado
  (`95fcbb0b`), `app/services/profile_service.py` e `app/workers/tasks/maintenance.py`
  ainda referenciam `profile.age` (inexistente) → `mypy app/` fica vermelho e o worker
  quebraria em runtime. É consequência intrínseca do fatiamento da mudança quebradora e
  está resolvido em A.2; a avaliação corre na ponta da branch (tudo verde). Registro
  apenas como observação de que o commit não é independentemente deployável.
- **Derivação `01/01/(ano−age)` é lossy:** aceitável e previsto (OQ2/§8, ajustável pelo
  usuário no form). Sem ação.

## 6. Comandos rodados + saídas reais

```text
$ bash ~/.codeflow/framework/core/scripts/run-structural.sh .codeflow/specs/001-backlog-features-qa-v1/SPEC_001_BACKLOG_FEATURES_QA_V1.md
✓ §5 estruturalmente válida     (EXIT=0)

# cadeia de revisão Alembic (head único)
$ grep -rln "down_revision.*a7b8c9d0e1f2" alembic/versions/
alembic/versions/20260702_b8c9d0e1f2a3_profile_birthdate.py   # só a migração da A.1

$ ruff check --no-cache app/models/profile.py alembic/versions/20260702_b8c9d0e1f2a3_profile_birthdate.py tests/integration/test_migration_profile_birthdate.py
All checks passed!
$ ruff format --check <mesmos 3 (+demais da track)>
13 files already formatted

$ mypy app/
Found 6 errors in 1 file (checked 67 source files)   # só pré-existentes de ai_client.py; 0 novos

# teste da fase (AC-A1) — Postgres real (localhost:5432)
$ TEST_DATABASE_URL=postgresql+asyncpg://caloria:caloria@localhost:5432/caloria_test \
    pytest tests/integration/test_migration_profile_birthdate.py -q
1 passed
```

## 7. Itens da fase / DoD não atendidos

Nenhum. Gate da fase ("`alembic upgrade head` aplica; `age` ausente, `birth_date`
presente e derivado") comprovado pelo teste de migração real. DoD de A.1 atendida.

## 8. Divergências entre o relatório e o código real

Nenhuma. O relatório é fiel: constantes de SQL importadas pelo teste, ano relativo,
round-trip e escopo conferem com o diff `e712fe12..95fcbb0b`. O desvio de escopo
(referências residuais em `profile_service`/`maintenance`) foi honestamente sinalizado
para tratamento em A.2.
