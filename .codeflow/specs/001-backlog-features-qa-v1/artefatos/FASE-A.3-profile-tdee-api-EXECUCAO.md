---
spec: 001-backlog-features-qa-v1
fase: A.3
slug_fase: profile-tdee-api
status: executado
tentativa: 1
reprovacoes: 0
sha_inicial: f3bb19e82dfb3be3f92b88669cfeb6a4a373414b
sha_final: b8b15b22b32edd8b23a2533198118161a23ff1ce
range: f3bb19e82dfb3be3f92b88669cfeb6a4a373414b..b8b15b22b32edd8b23a2533198118161a23ff1ce
---

# FASE A.3 — Relatório de execução

## 1. Resumo do que foi feito

O contrato do perfil passou a expor `birth_date`, `bmr` (TMB) e `formula`
("Mifflin-St Jeor"), removendo `age`. `ProfileUpdate` aceita `birth_date`;
`ProfileResponse` inclui `bmr`/`formula`. O BMR é **recalculado** no service
(`ProfileService.compute_bmr`, reusando um helper `_effective_weight` extraído) e
anexado pela rota (endpoint fino). Consumidores backend de `profile.age`
(context_builder, seed) foram migrados para `birth_date`. Tipo front atualizado.

## 2. Arquivos CRIADOS

Nenhum (só alterações e testes em arquivo existente).

## 3. Arquivos ALTERADOS

| Arquivo | O que mudou |
|---------|-------------|
| `backend/app/schemas/profile.py` | `ProfileUpdate.age` → `birth_date: date \| None`; `ProfileResponse` remove `age`, adiciona `birth_date`, `bmr: float \| None = None`, `formula: str = "Mifflin-St Jeor"`. |
| `backend/app/services/profile_service.py` | Extraído `_effective_weight` (reuso entre TDEE e BMR); novo `compute_bmr(user_id, profile)` (Mifflin, idade derivada). |
| `backend/app/api/v1/users.py` | `GET`/`PUT /me/profile` anexam `bmr` via `svc.compute_bmr` (endpoint fino, sem regra de negócio). |
| `backend/app/services/ai/context_builder.py` | Bio do prompt usa `age_from_birthdate(profile.birth_date)` (era `profile.age`). |
| `backend/scripts/seed_all.py` | Seed do perfil usa `birth_date=date(1997, 6, 1)` (era `age=27`). |
| `backend/tests/integration/test_users.py` | Testes de perfil migrados p/ `birth_date`; novo `test_perfil_expoe_birthdate_bmr_e_formula` (AC-A2). |
| `frontend/types/index.ts` | `UserProfile`: `age` → `birth_date: string \| null`; adiciona `bmr`/`formula`. |

## 4. Confirmação do REUSO e decisões de design

- **Endpoint fino (princípio inviolável #1):** o cálculo do BMR vive no
  `ProfileService` (`compute_bmr`), não no router. Isso exigiu **estender A.3 a
  `profile_service.py`** (fora da lista literal da spec, que citava só
  `schemas/profile.py` + `users.py`). Alternativa rejeitada: computar BMR no
  endpoint — violaria "endpoint fino" e duplicaria a lógica de `effective_weight`.
- **Sem coluna `bmr`:** o BMR é **recalculado** (não persistido) — decisão da spec
  ("recalculado ou persistido") que evita nova migração; usa o mesmo
  `effective_weight` do TDEE (fonte única via `_effective_weight`).
- **`ProfileResponse.bmr`/`formula` com default:** permitem `model_validate(profile)`
  (from_attributes) mesmo sem esses atributos no modelo; a rota preenche `bmr` depois.
- **Desvio de escopo declarado — consumidores backend de `age`:** removê-lo do
  modelo (A.1) quebrou dois call-sites **não listados na spec**:
  `context_builder.py:223` (runtime — `profile` é `Any`, então mypy não pegava, mas
  quebraria ao montar o prompt da IA) e `seed_all.py:702` (kwarg `age=` inválido).
  Ambos migrados a `birth_date`/idade derivada — diff mínimo, consequência da
  mudança quebradora. Sinalizado.
- **Estado transitório do frontend (esperado):** a troca de `age`→`birth_date` em
  `UserProfile` deixa **3 erros de `tsc`** em consumidores de UI —
  `perfil/page.tsx:88` e `onboarding/page.tsx:406` (leem `profile.age`). São
  **território de A.4** (fase de UI). A.3 tocou só `types/index.ts` (conforme spec);
  A.4 fecha `perfil/page.tsx` + `onboarding/page.tsx` e deixa o `tsc` verde. Backend
  está 100% verde.

## 5. Comandos rodados + saídas reais

```text
# type-check backend (mypy) — app-wide
$ mypy app/
# Só os 6 erros PRÉ-EXISTENTES de app/services/ai/ai_client.py. Sem novos.
Found 6 errors in 1 file (checked 67 source files)

# lint (ruff check) — arquivos da fase
$ ruff check app/schemas/profile.py app/api/v1/users.py \
    app/services/profile_service.py app/services/ai/context_builder.py \
    scripts/seed_all.py tests/integration/test_users.py
All checks passed!

# format (ruff format --check) — arquivos da fase
6 files already formatted

# testes de API do perfil (AC-A2) — Postgres real
$ TEST_DATABASE_URL=…@postgres:5432/caloria_test pytest tests/integration/test_users.py -v
... test_cria_ou_atualiza_perfil PASSED
    test_perfil_calcula_tdee PASSED
    test_perfil_expoe_birthdate_bmr_e_formula PASSED
8 passed in 7.68s

# suíte de integração completa (sem regressão — inclui context_builder)
$ TEST_DATABASE_URL=…@postgres:5432/caloria_test pytest tests/integration/ -q
69 passed in 54.61s

# type-check frontend (tsc) — ESTADO TRANSITÓRIO (resolvido em A.4)
$ npx tsc --noEmit
app/(dashboard)/perfil/page.tsx(88,22): error TS2339: Property 'age' does not exist on type 'UserProfile'.
app/onboarding/page.tsx(406,22): error TS2339: Property 'age' does not exist on type 'UserProfile'.
app/onboarding/page.tsx(406,51): error TS2339: Property 'age' does not exist on type 'UserProfile'.
# 3 erros, todos leitura de profile.age em telas → corrigidos em A.4.

# grep de segredo/PII (esperado: 0)
# nenhum segredo; só schema/derivação de idade.
```

## 6. Critérios de aceite da fase (com evidência)

- [x] **AC-A2** — `test_perfil_expoe_birthdate_bmr_e_formula`: `GET
  /users/me/profile` retorna `birth_date` (ecoado), `bmr` (>0), `tdee_calculated` e
  `formula == "Mifflin-St Jeor"`; `age` ausente do JSON. `test_perfil_calcula_tdee`
  confirma TDEE calculado por Mifflin via API.

## 7. Definition of Done da fase

- [x] Testes de API cobrindo o novo contrato em `tests/integration/` (8/8;
  integração completa 69/69)
- [x] **Backend** `make check`-equivalente verde: ruff + `ruff format --check` +
  `mypy app/` (só pré-existentes) + integração
- [~] **Frontend** `tsc`: 3 erros transitórios em `perfil`/`onboarding`
  (consumidores de UI), **resolvidos em A.4**. Documentado; é consequência esperada
  da mudança quebradora fatiada. `npm run lint`/jest do front não regridem por A.3.
- [x] `age` não vaza no contrato (assert explícito `"age" not in profile`)
- [x] Endpoint fino; nenhum segredo/PII
- [x] Commit em pt-BR (Conventional Commits), sem menção a autor/IA

## 8. (Em rework) O que mudou nesta tentativa

N/A — primeira execução.

## 9. Itens em aberto / dúvidas para o avaliador

- **`compute_bmr` em `profile_service.py`:** extensão além da lista literal de
  arquivos de A.3, justificada por "endpoint fino" (§4). Se o avaliador discordar,
  a alternativa (BMR no router) viola princípio #1.
- **`tsc` do front vermelho ao fim de A.3:** intencional e limitado a
  `perfil.tsx`/`onboarding.tsx`; A.4 fecha. `onboarding.tsx` **não** está na lista de
  arquivos de A.4 na spec — será tratado lá como extensão (consumidor do tipo).
- **`context_builder.py`/`seed_all.py`:** consumidores de `age` não previstos pela
  spec; migrados aqui para não deixar runtime/seed quebrados.
