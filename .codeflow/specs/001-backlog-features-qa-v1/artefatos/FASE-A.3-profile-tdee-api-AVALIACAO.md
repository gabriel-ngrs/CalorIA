---
spec: 001-backlog-features-qa-v1
fase: A.3
slug_fase: profile-tdee-api
tentativa: 1
veredito: APROVADO
score: 9.5
threshold: 8.5
range_avaliado: f3bb19e82dfb3be3f92b88669cfeb6a4a373414b..b8b15b22b32edd8b23a2533198118161a23ff1ce
---

# FASE A.3 — Avaliação independente

## 1. Veredito e score

**Veredito:** APROVADO · **Score:** 9.5 / threshold 8.5

Contrato expõe `birth_date`, `bmr` e `formula`, remove `age`. BMR **recalculado** no
`ProfileService.compute_bmr` (endpoint fino honrado, princípio #1) reusando
`_effective_weight` extraído. AC-A2 coberto por teste de API; suíte de integração
verde. Nenhum BLOQUEANTE, nenhum IMPORTANTE.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 4 | AC-A2: `tests/integration/test_users.py::test_perfil_expoe_birthdate_bmr_e_formula` (assert `"age" not in profile`, `bmr>0`, `formula=="Mifflin-St Jeor"`). Dedução: fase estendida a `profile_service.py`, `context_builder.py`, `seed_all.py` além da lista literal (`schemas` + `users.py`) — justificado (endpoint fino + consumidores de `age`), declarado |
| 2 | Arquitetura e direção de dependências | 3 | 5 | cálculo de BMR no service, não no router (`users.py:52-60` só anexa `response.bmr`); dependência `api → service → nutrition` correta |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | `compute_bmr(user_id, …)`/`_effective_weight` sempre por `user_id`; `age` não vaza (assert explícito); sem segredo/PII |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | `_effective_weight` extraído e reusado por TDEE (`update_profile`) e BMR (`compute_bmr`) — elimina duplicação do fallback de peso |
| 5 | Padrões de domínio/aplicação | 2 | 5 | `response_model` Pydantic; front espelha em `types/index.ts`; defaults em `ProfileResponse.bmr/formula` permitem `model_validate(from_attributes)` |
| 6 | Local e nomes dos arquivos | 2 | 5 | `schemas/profile.py`, `api/v1/users.py`, `services/profile_service.py`, `types/index.ts` — corretos |
| 7 | Qualidade de código | 2 | 4 | limpo e anotado; dedução leve: `compute_bmr` recomputa `_effective_weight`, que quando `current_weight is None` dispara **outra** query `WeightService.latest()` — no `PUT` isso soma à consulta já feita em `update_profile` (até 2 lookups do último peso). Micro-ineficiência, não bug |
| 8 | Testes e cobertura | 2 | 5 | teste de API do novo contrato + `test_perfil_calcula_tdee`; integração completa 69/69 (reexecutei o subconjunto: 8/8 em `test_users.py`) |
| 9 | Migration safety | 2 | — | não se aplica (BMR recalculado, sem coluna nova — decisão da spec "recalculado ou persistido") |

Score = (4·3+5·3+5·3+5·3+5·2+5·2+4·2+5·2) / (5·20) · 10 = 95/100 · 10 = **9.5**.

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

Nenhum.

## 5. Sugestões

- **Query dupla do último peso no `PUT` (não-bloqueante):** `update_profile` já resolve
  `_effective_weight` (podendo consultar `WeightService.latest`) e, na sequência, a rota
  chama `compute_bmr`, que resolve `_effective_weight` de novo. Quando `current_weight`
  é `None`, são dois `SELECT` do mesmo último `WeightLog` por request. Opcional: fazer a
  rota reusar o `effective_weight`/`bmr` já computado no service. Impacto pequeno (índice
  por `user_id`), fora do escopo travado — deixo como melhoria.
- **`context_builder.py`/`seed_all.py` fora da lista da spec (aceito):** consumidores de
  `profile.age` que quebrariam em runtime/seed; migrados com diff mínimo. Confirmei que
  `date` já está importado em `seed_all.py:5`. Tratamento correto.
- **Divergência `current_weight_kg` (front) × `current_weight` (backend):** pré-existente,
  visível em `types/index.ts`; não é desta fase.

## 6. Comandos rodados + saídas reais

```text
$ ruff check --no-cache app/schemas/profile.py app/api/v1/users.py \
    app/services/profile_service.py app/services/ai/context_builder.py \
    scripts/seed_all.py tests/integration/test_users.py
All checks passed!

$ mypy app/
Found 6 errors in 1 file (checked 67 source files)   # só pré-existentes de ai_client.py; 0 novos

$ TEST_DATABASE_URL=…@localhost:5432/caloria_test pytest tests/integration/test_users.py -q
8 passed        # inclui test_perfil_expoe_birthdate_bmr_e_formula e test_perfil_calcula_tdee

$ grep -n "from datetime" scripts/seed_all.py
5:from datetime import date, time, timedelta     # `date` disponível para birth_date=date(1997,6,1)
```

## 7. Itens da fase / DoD não atendidos

Nenhum quanto ao backend. O `tsc` do front ficou vermelho **ao fim de A.3** (3 erros em
`perfil.tsx`/`onboarding.tsx`) — estado transitório declarado e fechado em A.4 (verifiquei
`tsc --noEmit` = 0 na ponta da branch). Gate de A.3 ("contrato coberto por teste de API;
`make test-integration`/`make check` backend verdes") atendido.

## 8. Divergências entre o relatório e o código real

Nenhuma. `compute_bmr` no service, `_effective_weight` reusado, `age` fora do contrato e
migração dos consumidores conferem com o diff `f3bb19e8..b8b15b22` e com a suíte
reexecutada.
