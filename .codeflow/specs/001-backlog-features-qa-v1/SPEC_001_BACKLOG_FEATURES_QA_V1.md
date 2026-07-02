---
id: 001
slug: 001-backlog-features-qa-v1
title: "Backlog de features do QA (lote bugs-teste-v1): hidratação CRUD, perfil/TDEE, persistência de IA e recuperação de senha"
type: feature
status: draft
priority: P2
size: XL
risk_level: YELLOW
refine_mode: DEEP
wave: multi
domain: fullstack
bounded_context: multi
cross_context: [perfil-nutricao, hidratacao, ai-persistencia, auth]
created_at: 2026-07-02
updated_at: 2026-07-02
owner: Gabriel
linked_adr: [ADR-001, ADR-002, ADR-005, ADR-007]
related_bugs: [B8, B11, B12, B15, B16, B20]
quality_gate:
  scorer: phase-evaluator
  threshold: 8.5
---

# Backlog de features do QA — lote bugs-teste-v1

> **Nota de planning (2026-07-02):** spec construída após sondagem do codebase real.
> Consolida os **6 bugs bloqueados** do lote de QA `bugs-teste-v1` que não são bugs
> de código e sim necessidade de nova feature/mudança de escopo: **B8, B11, B12,
> B15, B16, B20** (conforme o "Backlog de specs" do ledger
> `.codeflow/bug-batches/bugs-teste-v1.md` e da decision
> `.codeflow/decisions/2026-07-02-lote-bugs-teste-v1.md`). São 4 tracks
> independentes por bounded context, executados e avaliados **em sequência**
> (B → A → C → D) via `/execute-spec-phase` + `/evaluate-spec-phase`.
>
> **Já existe e é reusado:** modelos `UserProfile`/`HydrationLog`/`AIConversation`,
> `HydrationDaySummary.entries` (já expõe logs individuais), `ProfileService`
> (já recalcula TDEE), `WeightService.latest()`, `calculate_tdee()`, pipeline
> auth (`security.py`/`auth_service.py` com blacklist Redis), hooks React Query
> por domínio. **É novo:** coluna `birth_date` + migração de dados, exposição de
> TMB, CRUD de hidratação, canal `WEB` de conversa + persistência de chat,
> serviço de e-mail SMTP + fluxo de reset de senha, telas correspondentes.
>
> **Fora do escopo desta spec:** os 3 bugs incidentais do lote (manifest.webmanifest
> inválido, testes de front pré-quebrados `MacroCards`/`MacroPieChart`, mapeamento
> Groq 500→503 no backend) → tratar por `/bugfix`, não aqui; re-verificação runtime
> de B17/B18/B19 (depende de `GROQ_API_KEY` nova, não é código); histórico
> **persistente** de insights no backend (B16 é resolvido só no frontend);
> qualquer canal de bot (Telegram/WhatsApp) — desativado por ADR-003.

## Resumo executivo (TL;DR)

| O quê | Por quê | Backend/Infra | Frontend | Decisão | Tamanho |
|---|---|---|---|---|---|
| **Track B — Hidratação CRUD** (B8) | Módulo só soma; sem editar/remover | `DELETE`/`PUT /hydration/{id}` + service c/ ownership | Lista de logs do dia com remover/editar | Reusa `entries` já exposto | M (3 fases) |
| **Track A — Perfil & TDEE** (B11+B12) | Idade fixa; TMB/TDEE nunca exibidos; `tdee` null | `age→birth_date` (migração), Mifflin-St Jeor, expor TMB | Date picker + card TMB/TDEE + fórmula | Mudança de schema quebradora | L (4 fases) |
| **Track C — Persistência de IA** (B16+B20) | Insights e chat somem ao navegar | Canal `WEB` + persistir chat em `AIConversation` | `useMutation`→`useQuery`; UI de histórico | Reusa `AIConversation` | M (3 fases) |
| **Track D — Recuperação de senha** (B15) | Sem "esqueci a senha"; copy "Gemini" desatualizada | EmailService SMTP + forgot/reset + token | Telas forgot/reset + fix copy | SMTP genérico + JWT reset | L (4 fases) |

## Sumário

1. Problema e contexto (+ 1.1 Princípios invioláveis)
2. Requisitos (FR / NFR)
3. Critérios de aceite (AC)
4. Abordagem técnica (mapa NOVO / REUSADO / REMOVIDO)
5. Plano de desenvolvimento por fases (Tracks B, A, C, D — 14 fases)
6. Riscos
7. Rollout
8. Open Questions (resolvidas)
9. Definition of Done (gate por etapa)

## 1. Problema e contexto

O lote de QA manual `bugs-teste-v1` registrou 20 achados. Os corrigíveis já foram
resolvidos; **6 saíram do loop de bugfix por exigirem design/escopo maior**. Esta
spec os transforma em features ancoradas na arquitetura real:

- **B8 — Hidratação só soma.** `POST /hydration` insere logs, mas não há como
  editar ou remover. Descoberta da sondagem: `HydrationDaySummary.entries`
  (`backend/app/schemas/logs.py:49`) **já expõe os logs individuais** do dia e
  `useHydrationToday` já os recebe — o ledger estava desatualizado nesse ponto.
  Falta apenas o CRUD (`DELETE`/`PUT`) e a UI de lista.
- **B11 — Idade fixa.** `user_profiles.age` (`backend/app/models/profile.py:38`)
  guarda idade como inteiro estático, que envelhece incorretamente. Precisa virar
  `birth_date`. **Mudança de schema quebradora** (contrato de API e coluna
  persistida).
- **B12 — TMB/TDEE não exibidos + `tdee_calculated` null.** `ProfileService`
  (`backend/app/services/profile_service.py:30-43`) **já recalcula** o TDEE quando
  `current_weight`, `height_cm`, `age`, `sex` estão presentes — mas o form nunca
  envia `current_weight`, então o `if` nunca dispara. Além disso, o TMB (BMR) é
  calculado internamente em `calculate_tdee` mas nunca exposto.
- **B15 — Sem recuperação de senha.** `backend/app/api/v1/auth.py` só tem
  register/login/refresh/logout/me. Não há infraestrutura de e-mail (confirmado:
  nenhuma var SMTP em `config.py`/`.env.example`).
- **B16 — Insights somem ao navegar.** Os hooks de IA (`frontend/lib/hooks/useAI.ts`)
  usam `useMutation`, cujo resultado vive em `mutation.data` e é descartado ao trocar
  de rota. O precedente do fix já existe no próprio repo: `useProfile`
  (`frontend/lib/hooks/useProfile.ts`) usa `useQuery` + `staleTime`.
- **B20 — Chat "Pergunte à IA" sem histórico.** O modelo `AIConversation`
  (`backend/app/models/ai_conversation.py`) existe mas foi modelado para bots
  (`channel` só `telegram`/`whatsapp`); o chat web usa `POST /ai/insights`
  `type=question` sem persistir nada.

Incidentalmente, a copy de marketing do login ("Gemini 2.5 Flash" em
`frontend/components/auth/AuthLeftPanel.tsx:10-11` e `AuthBackground.tsx:31`)
contradiz o **ADR-002** (o projeto migrou de Gemini para Groq/Llama) — corrigida
junto com o Track D.

### 1.1 Princípios invioláveis

Cada princípio rastreia a uma rule/ADR/constitution real do repositório:

1. **Lógica de negócio vive em `services/`, endpoints são finos.** (constitution
   do projeto — "Regras invariantes"). Todo CRUD/regra nova entra em service.
2. **`GROQ_API_KEY` nunca é exposta ao frontend.** (constitution do projeto +
   ADR-002). Track C não muda esse contrato.
3. **`mypy app/` (strict) e `ruff` limpos; tudo anotado.** (constitution — DoD).
4. **Mudança de schema exige migration Alembic revisada; migrations aplicadas são
   imutáveis.** (constitution — áreas de alto risco). Vale para A.1 (`birth_date`)
   e C.2 (novo label de enum).
5. **Auth é área de alto risco:** mudança em `security.py`/fluxo de auth exige
   teste e revisão cuidadosa. (constitution — áreas de alto risco). Vale para o
   Track D.
6. **Mudança quebradora é detectada e confirmada antes de aplicada.**
   (constitution universal). B11 (`age→birth_date`) é quebradora e está declarada
   e resolvida (OQ2/§8).
7. **Código em inglês; mensagens ao usuário final em pt-BR.** (rule naming). Vale
   para o corpo dos e-mails de reset e a copy.
8. **Diff mínimo, sem refatoração lateral.** (rule code-quality). Nenhuma fase
   toca código adjacente fora do seu escopo travado.
9. **Commits em Conventional Commits pt-BR, sem menção a autor/IA nem
   `Co-Authored-By`.** (constitution do projeto).
10. **Telas novas seguem o design system glass/neu.** (ADR-007).

## 2. Requisitos

### Funcionais

**Track B — Hidratação CRUD (B8)**
- **FR-B1:** `HydrationService` oferece `get_by_id`, `delete` e `update` que
  operam **somente** sobre logs do próprio usuário (log inexistente ou de outro
  usuário ⇒ erro tratável como 404).
- **FR-B2:** `DELETE /api/v1/hydration/{id}` remove um log (204) e
  `PUT /api/v1/hydration/{id}` edita `amount_ml`/`date`/`time` (200), ambos com
  checagem de posse.
- **FR-B3:** A página de hidratação lista os logs individuais do dia (a partir de
  `entries`) com ação de **remover** e **editar**; o resumo diário (`total_ml`) e
  o dashboard refletem a mudança após a ação.

**Track A — Perfil & TDEE (B11 + B12)**
- **FR-A1:** `user_profiles` passa a armazenar `birth_date` (`Date`, nullable) no
  lugar de `age`; uma migração converte os registros existentes
  (`birth_date ≈ 01/01 do ano = ano_atual − age`) e remove a coluna `age`.
- **FR-A2:** A idade usada no cálculo é **derivada** de `birth_date`; o TDEE passa
  a usar a fórmula **Mifflin-St Jeor**; o TMB (BMR) é calculado e exposto
  separadamente do TDEE.
- **FR-A3:** Quando o form não envia `current_weight`, o `ProfileService` o popula
  a partir do último `WeightLog` (`WeightService.latest()`), permitindo o cálculo
  do TDEE.
- **FR-A4:** `ProfileResponse` expõe `birth_date`, `bmr` (TMB), `tdee_calculated`
  (TDEE) e o nome da fórmula usada; o endpoint `PUT/GET /users/me/profile` reflete
  o novo contrato.
- **FR-A5:** A página de perfil usa **seletor de data de nascimento** (não idade)
  e exibe um card com **TMB e TDEE** e a explicação do cálculo (Mifflin-St Jeor).

**Track C — Persistência de IA (B16 + B20)**
- **FR-C1:** Os hooks de insights (`useDailyInsight`, `useWeeklyInsight`,
  `useEatingPatterns`, `useNutritionalAlerts`, `useGoalAdjustment`,
  `useMonthlyReport`) usam `useQuery` com `queryKey` estável + `staleTime`, de modo
  que o resultado **persiste ao navegar** e voltar dentro da sessão.
- **FR-C2:** O enum `ConversationChannel` inclui o valor `WEB`; cada pergunta do
  chat "Pergunte à IA" e sua resposta são persistidas em `AIConversation` com
  `channel=WEB` e `external_chat_id="web:{user_id}"`.
- **FR-C3:** `GET /api/v1/ai/conversations` retorna o histórico de chat web do
  usuário autenticado; a rota que responde a `type=question` grava o par
  `user`/`model` na conversa web.
- **FR-C4:** A tela do chat "Pergunte à IA" carrega e exibe o histórico persistido
  ao abrir.

**Track D — Recuperação de senha (B15)**
- **FR-D1:** Um `EmailService` envia e-mails via SMTP (`aiosmtplib`) com config por
  variáveis de ambiente; sem SMTP configurado (dev), loga o conteúdo/link em vez
  de falhar.
- **FR-D2:** `POST /api/v1/auth/forgot-password` gera um token de reset
  (JWT `type=reset`, expirável ≤ 1h) e dispara o e-mail; a resposta é **uniforme**,
  não revelando se o e-mail existe.
- **FR-D3:** `POST /api/v1/auth/reset-password` valida o token (single-use via
  blacklist Redis), troca a senha (bcrypt) e invalida o token.
- **FR-D4:** Existem as telas `/forgot-password` e `/reset-password` e o link
  "Esqueci minha senha" no login.
- **FR-D5:** A copy "Gemini 2.5 Flash" é substituída por Groq/Llama nos componentes
  de auth (`AuthLeftPanel.tsx`, `AuthBackground.tsx`).

### Não-funcionais
- **NFR-1:** `mypy app/` (strict) e `ruff check .`/`ruff format --check .` limpos no
  backend; `npm run lint` e `npx tsc --noEmit` limpos no frontend.
- **NFR-2:** Toda mudança de schema (A.1, C.2) acompanha migração Alembic gerada e
  revisada; nenhuma migration já aplicada é editada.
- **NFR-3:** `forgot-password` não vaza a existência do e-mail (resposta e latência
  uniformes); o token de reset expira em ≤ 1h e é single-use.
- **NFR-4:** `GROQ_API_KEY` nunca chega ao frontend; e-mails e mensagens ao usuário
  em pt-BR; segredos SMTP só em `.env` (nunca commitados; `.env.example` só com
  placeholders).
- **NFR-5:** Cada mudança de comportamento tem teste correspondente (pytest no
  backend, jest no frontend); `make check` verde antes do PR.
- **NFR-6:** Telas novas seguem o design system glass/neu (ADR-007).

## 3. Critérios de aceite

- **AC-B1 (FR-B1/B2):** *Given* um log de hidratação do usuário A, *When* o usuário
  B chama `DELETE /hydration/{id}` desse log, *Then* recebe 404 e o log permanece.
- **AC-B2 (FR-B2):** *Given* um log do próprio usuário, *When* chama
  `DELETE /hydration/{id}`, *Then* recebe 204 e o log some do `get_day_summary`.
- **AC-B3 (FR-B2):** *Given* um log de 200 ml, *When* chama `PUT /hydration/{id}`
  com 350 ml, *Then* recebe 200 e `total_ml` do dia reflete 350.
- **AC-B4 (FR-B3):** *Given* a página de hidratação com 3 registros no dia, *When*
  removo um pela lista, *Then* a lista e o total do dia atualizam sem reload.
- **AC-A1 (FR-A1):** *Given* um perfil com `age=30` antes da migração, *When* a
  migração `…_profile_birthdate` roda, *Then* `birth_date` = 01/01/(ano_atual−30) e
  a coluna `age` não existe mais.
- **AC-A2 (FR-A2/A4):** *Given* um perfil com peso/altura/sexo/`birth_date`
  completos, *When* consulto `GET /users/me/profile`, *Then* recebo `bmr` e
  `tdee_calculated` calculados por Mifflin-St Jeor e o nome da fórmula.
- **AC-A3 (FR-A3):** *Given* um usuário com `WeightLog` mas sem `current_weight` no
  perfil, *When* atualizo o perfil sem enviar `current_weight`, *Then* o service usa
  o último peso registrado e o TDEE deixa de ser null.
- **AC-A4 (FR-A5):** *Given* a página de perfil, *When* abro o formulário, *Then*
  vejo um seletor de data de nascimento (não campo de idade) e um card TMB/TDEE com
  a fórmula explicada.
- **AC-C1 (FR-C1):** *Given* que gerei o insight semanal, *When* navego para outra
  página e volto, *Then* o insight ainda está visível (sem regenerar).
- **AC-C2 (FR-C2/C3):** *Given* que faço uma pergunta no chat, *When* consulto
  `GET /ai/conversations`, *Then* a conversa web contém o par pergunta/resposta.
- **AC-C3 (FR-C4):** *Given* um histórico de chat existente, *When* reabro a tela do
  chat, *Then* as mensagens anteriores aparecem.
- **AC-D1 (FR-D2):** *Given* um e-mail cadastrado e um não cadastrado, *When* chamo
  `forgot-password` para cada, *Then* a resposta HTTP é idêntica em ambos.
- **AC-D2 (FR-D3):** *Given* um token de reset válido, *When* chamo `reset-password`
  duas vezes com ele, *Then* a primeira troca a senha (200) e a segunda falha
  (token single-use).
- **AC-D3 (FR-D3):** *Given* uma senha trocada via reset, *When* faço login com a
  nova senha, *Then* autentico com sucesso; a antiga falha.
- **AC-D4 (FR-D5):** *Given* a tela de login, *When* inspeciono a copy, *Then* não
  há menção a "Gemini" e sim a Groq/Llama.

## 4. Abordagem técnica

### Mapa NOVO / REUSADO / REMOVIDO

**REUSADO (existe no repo, verificado):**
- `backend/app/models/profile.py` — `UserProfile` (campos `current_weight`,
  `tdee_calculated`, `sex`, `activity_level`; enums `Sex`/`ActivityLevel`).
- `backend/app/services/nutrition/tdee.py` — `calculate_tdee` (será trocada a
  fórmula) + `_ACTIVITY_MULTIPLIERS`.
- `backend/app/services/profile_service.py` — `ProfileService.update_profile`
  (já recalcula TDEE).
- `backend/app/services/log_service.py` — `HydrationService`,
  `WeightService.latest()` (fonte de `current_weight`), padrão upsert/`get_by_date`.
- `backend/app/schemas/logs.py` — `HydrationDaySummary.entries`,
  `HydrationLogResponse`, `HydrationLogCreate`.
- `backend/app/api/v1/hydration.py`, `.../users.py`, `.../auth.py`, `.../ai.py`.
- `backend/app/models/ai_conversation.py` — `AIConversation`, `ConversationChannel`.
- `backend/app/core/security.py` — `create_access_token`/`decode_token`/
  `hash_password` (precedente para token de reset).
- `backend/app/services/auth_service.py` — `blacklist_token`/`is_token_blacklisted`
  (precedente para token single-use).
- `frontend/lib/hooks/useAI.ts`, `useLogs.ts`, `useProfile.ts` (padrão `useQuery`).
- `frontend/app/(dashboard)/{hidratacao,perfil,insights}/page.tsx`,
  `frontend/app/(auth)/login/page.tsx`,
  `frontend/components/auth/{AuthLeftPanel,AuthBackground}.tsx`.

**NOVO:**
- Migração `…_profile_birthdate` (age→birth_date + drop) e `…_conversation_web`
  (label `WEB` no enum).
- `backend/app/services/email_service.py` (SMTP via aiosmtplib).
- Métodos `HydrationService.get_by_id/delete/update`; schema `HydrationLogUpdate`.
- Schemas de reset (`ForgotPasswordRequest`, `ResetPasswordRequest`); função
  `create_reset_token` em `security.py`.
- Endpoints `DELETE/PUT /hydration/{id}`, `GET /ai/conversations`,
  `POST /auth/forgot-password`, `POST /auth/reset-password`.
- Hooks/telas front: `useDeleteHydration`/`useUpdateHydration`, `useChatHistory`,
  telas `/forgot-password` e `/reset-password`, card TMB/TDEE, date picker.
- Vars de config SMTP em `config.py` + `.env.example`.

**REMOVIDO:**
- Coluna `user_profiles.age` (após migração de dados para `birth_date`).
- Campo `age` em `ProfileUpdate`/`ProfileResponse`.
- Copy "Gemini 2.5 Flash" em `AuthLeftPanel.tsx`/`AuthBackground.tsx`.

### Detalhamento por track
- **B:** `HydrationService.get_by_id` filtra por `id` **e** `user_id`; `delete`
  e `update` chamam-no e levantam erro→404 no endpoint. Front consome `entries`
  (já disponível) e adiciona ações; `useLogs.ts` ganha mutações que invalidam
  `["hydration"]` e `["dashboard"]` (padrão já usado).
- **A:** migração deriva `birth_date`; `tdee.py` passa a Mifflin-St Jeor e expõe
  BMR; helper `age_from_birthdate`; `ProfileService` popula `current_weight` do
  último `WeightLog`. Contrato do `ProfileResponse` ganha `bmr`/`birth_date`/
  `formula`. Front troca input de idade por date picker e renderiza o card.
- **C:** front migra os hooks de IA para `useQuery` (chaves estáveis). Backend
  adiciona `WEB` ao enum (migração `ALTER TYPE`), persiste o par user/model em
  `AIConversation` ao responder `type=question`, e expõe `GET /ai/conversations`.
  Front do chat carrega o histórico.
- **D:** `EmailService` SMTP com fallback console; `create_reset_token`
  (JWT `type=reset`); endpoints forgot/reset com resposta uniforme e token
  single-use (blacklist Redis). Telas novas seguem glass/neu; copy corrigida.

## 5. Plano de desenvolvimento por fases

> 14 fases em 4 tracks. **Execução e avaliação em sequência B → A → C → D:** a 1ª
> fase de cada track declara `Depende de` a **última fase do track anterior**, o que
> lineariza a ordem sem ciclos. Dentro de cada track as dependências são locais.
> Cada fase: teste vermelho → implementação → verde → `make check` → sem regressão.
> `id`/`slug` são canônicos (entram nos nomes dos artefatos). Threshold de
> aprovação: 8.5 (frontmatter).

### Track B — Hidratação CRUD (B8)

### Fase B.1 — Métodos de CRUD no HydrationService *(S)*
- **id:** `B.1`
- **slug:** `hydration-service-crud`
- **Objetivo:** dar ao `HydrationService` `get_by_id`, `delete` e `update` com
  posse por `user_id`.
- **Depende de:** nenhuma.
- **Arquivos alterados:** `backend/app/services/log_service.py`,
  `backend/app/schemas/logs.py` (novo `HydrationLogUpdate`).
- **Passos:** 1) adicionar `HydrationLogUpdate` (campos opcionais `amount_ml`/
  `date`/`time` com os mesmos `Field` de `HydrationLogCreate`). 2) `get_by_id(self,
  user_id, log_id) -> HydrationLog | None` filtrando por `id` e `user_id`.
  3) `delete(self, user_id, log_id) -> bool` (retorna False se não achar). 4)
  `update(self, user_id, log_id, data) -> HydrationLog | None` aplicando
  `model_dump(exclude_unset=True)` e commit.
- **Testes:** `backend/tests/…/test_logs.py` — delete/update do próprio log
  funciona; log de outro usuário retorna None (AC-B1/B2/B3).
- **Escopo travado / violações BLOQUEANTES:** não expor endpoints aqui; não tocar
  `WeightService`/`MoodService`; ownership obrigatória (jamais deletar por `id`
  puro).
- **Critério de conclusão (gate):** testes novos verdes; `mypy`/`ruff` limpos.

### Fase B.2 — Endpoints DELETE/PUT de hidratação *(S)*
- **id:** `B.2`
- **slug:** `hydration-api-crud`
- **Objetivo:** expor `DELETE`/`PUT /api/v1/hydration/{id}` com 404 por posse.
- **Depende de:** `B.1`.
- **Arquivos alterados:** `backend/app/api/v1/hydration.py`.
- **Passos:** 1) `DELETE /{log_id}` → `HydrationService.delete`; se False, `HTTPException
  404`; senão `204`. 2) `PUT /{log_id}` recebendo `HydrationLogUpdate` →
  `update`; se None, `404`; senão `HydrationLogResponse` (200).
- **Testes:** testes de API (httpx AsyncClient) para 204, 200, 404 de outro usuário
  (AC-B1/B2/B3).
- **Escopo travado / violações BLOQUEANTES:** endpoint fino (só orquestra); nenhuma
  regra de negócio no router; sem alterar `POST`/`GET` existentes.
- **Critério de conclusão (gate):** testes de API verdes; `make check` backend verde.

### Fase B.3 — UI de lista/edição de hidratação *(M)*
- **id:** `B.3`
- **slug:** `hydration-ui-list`
- **Objetivo:** listar os logs do dia com remover/editar na página de hidratação.
- **Depende de:** `B.2`.
- **Arquivos alterados:** `frontend/lib/hooks/useLogs.ts`,
  `frontend/app/(dashboard)/hidratacao/page.tsx`; tipos em `frontend/types/index.ts`
  se necessário.
- **Passos:** 1) hooks `useDeleteHydration`/`useUpdateHydration` (mutações que
  invalidam `["hydration"]` e `["dashboard"]`, com toast — padrão do arquivo).
  2) renderizar `entries` de `useHydrationToday` como lista com botão remover e
  edição inline/modal. 3) estados de loading/erro coerentes com o design system.
- **Testes:** jest de componente/hook cobrindo remoção otimista/erro; ou teste de
  render da lista (AC-B4).
- **Escopo travado / violações BLOQUEANTES:** não persistir foto; não mexer no
  gráfico de histórico; seguir glass/neu (ADR-007).
- **Critério de conclusão (gate):** `npm run lint`/`tsc`/jest verdes; remoção/edição
  refletem no total do dia.

### Track A — Perfil & TDEE (B11 + B12)

### Fase A.1 — Schema e migração age → birth_date *(M)*
- **id:** `A.1`
- **slug:** `profile-birthdate-schema`
- **Objetivo:** substituir `age` por `birth_date` no modelo e migrar os dados.
- **Depende de:** `B.3`.
- **Arquivos alterados:** `backend/app/models/profile.py`; **novo**
  `backend/alembic/versions/…_profile_birthdate.py`.
- **Passos:** 1) trocar `age: Mapped[int | None]` por `birth_date: Mapped[date |
  None]` (`Date`, nullable). 2) migração: `add_column birth_date`; `UPDATE` setando
  `birth_date = make_date(extract(year, current_date) - age, 1, 1)` onde `age` não
  é null; `drop_column age`. `downgrade` recria `age` a partir do ano de
  `birth_date`. 3) revisar a migração à mão (não confiar 100% no autogenerate).
- **Testes:** `backend/tests/` — teste de migração (upgrade/downgrade num perfil
  seed) OU teste de modelo confirmando o campo (AC-A1). Rodar em Postgres (ADR-001).
- **Escopo travado / violações BLOQUEANTES:** não editar migrations já aplicadas;
  não remover `age` sem antes popular `birth_date`; migração é a única forma de
  mudar schema (constitution).
- **Critério de conclusão (gate):** `alembic upgrade head` aplica sem erro em PG de
  teste; `age` ausente, `birth_date` presente e derivado.

### Fase A.2 — Cálculo: Mifflin-St Jeor + TMB + idade derivada + current_weight *(M)*
- **id:** `A.2`
- **slug:** `tdee-mifflin-calc`
- **Objetivo:** calcular BMR/TDEE por Mifflin-St Jeor a partir de `birth_date` e
  popular `current_weight` do último peso.
- **Depende de:** `A.1`.
- **Arquivos alterados:** `backend/app/services/nutrition/tdee.py`,
  `backend/app/services/profile_service.py`.
- **Passos:** 1) em `tdee.py`, criar `calculate_bmr(weight, height, age, sex)` com
  Mifflin-St Jeor (`10*peso + 6.25*altura − 5*idade + s`, s=+5 masc / −161 fem) e
  `calculate_tdee` reusando `calculate_bmr * multiplicador`; helper
  `age_from_birthdate(birth_date) -> int`. 2) em `ProfileService.update_profile`,
  derivar idade de `birth_date`, e se `current_weight` vier null, buscar
  `WeightService(self.db).latest(user_id)` e usar `weight_kg`. Persistir `tdee_calculated`.
- **Testes:** unit de `calculate_bmr`/`calculate_tdee` (valores conhecidos) +
  `test` de `ProfileService` populando current_weight do último log (AC-A2/A3).
- **Escopo travado / violações BLOQUEANTES:** não alterar `_ACTIVITY_MULTIPLIERS`
  sem necessidade; manter tipos anotados (mypy strict); sem regra de negócio no
  endpoint.
- **Critério de conclusão (gate):** testes verdes; TDEE deixa de ser null quando há
  `WeightLog`.

### Fase A.3 — Contrato de API do perfil (birth_date + BMR/TDEE) *(S)*
- **id:** `A.3`
- **slug:** `profile-tdee-api`
- **Objetivo:** expor `birth_date`, `bmr`, `tdee_calculated` e a fórmula no schema.
- **Depende de:** `A.2`.
- **Arquivos alterados:** `backend/app/schemas/profile.py`,
  `backend/app/api/v1/users.py` (se necessário para montar `bmr`/`formula`).
- **Passos:** 1) `ProfileUpdate`: trocar `age` por `birth_date: date | None`.
  2) `ProfileResponse`: remover `age`, adicionar `birth_date`, `bmr: float | None`,
  `formula: str = "Mifflin-St Jeor"`. 3) endpoint retorna BMR (recalculado ou
  persistido). 4) atualizar tipos front (`frontend/types/index.ts`) para casar.
- **Testes:** teste de API `GET/PUT /users/me/profile` verificando os novos campos
  (AC-A2).
- **Escopo travado / violações BLOQUEANTES:** não vazar `age` no contrato; endpoint
  fino.
- **Critério de conclusão (gate):** contrato novo coberto por teste; `make check`
  backend verde.

### Fase A.4 — UI de perfil: date picker + card TMB/TDEE *(M)*
- **id:** `A.4`
- **slug:** `profile-tdee-ui`
- **Objetivo:** trocar idade por data de nascimento e exibir TMB/TDEE + fórmula.
- **Depende de:** `A.3`.
- **Arquivos alterados:** `frontend/app/(dashboard)/perfil/page.tsx`,
  `frontend/lib/hooks/useProfile.ts` (payload), tipos.
- **Passos:** 1) substituir o input de idade por seletor de data de nascimento.
  2) enviar `birth_date` no `useUpdateProfile`. 3) card com TMB (`bmr`), TDEE
  (`tdee_calculated`) e texto curto explicando "Mifflin-St Jeor". 4) tratar estado
  em que TDEE ainda é null (sem peso).
- **Testes:** jest de render do card com dados mockados (AC-A4).
- **Escopo travado / violações BLOQUEANTES:** não reintroduzir campo idade; seguir
  glass/neu; não recalcular TDEE no front (vem do backend).
- **Critério de conclusão (gate):** `lint`/`tsc`/jest verdes; formulário salva
  `birth_date` e o card exibe TMB/TDEE.

### Track C — Persistência de IA (B16 + B20)

### Fase C.1 — Insights persistentes via useQuery (B16) *(M)*
- **id:** `C.1`
- **slug:** `insights-usequery-cache`
- **Objetivo:** insights param de sumir ao navegar.
- **Depende de:** `A.4`.
- **Arquivos alterados:** `frontend/lib/hooks/useAI.ts`,
  `frontend/app/(dashboard)/insights/page.tsx`.
- **Passos:** 1) migrar `useDailyInsight`/`useWeeklyInsight`/`useEatingPatterns`/
  `useNutritionalAlerts`/`useGoalAdjustment`/`useMonthlyReport` de `useMutation`
  para `useQuery` com `queryKey` estável (ex: `["ai","weekly"]`, incluindo params
  como `days`/`month`) + `staleTime` (padrão do `useProfile`) e `enabled` sob
  demanda quando fizer sentido. 2) ajustar `insights/page.tsx` para ler de
  `query.data` em vez de `mutation.data`; preservar botões de "regenerar"
  (`refetch`).
- **Testes:** jest confirmando que o hook expõe `data` cacheada; ou teste de página
  que re-render mantém o insight (AC-C1).
- **Escopo travado / violações BLOQUEANTES:** não criar tabela/endpoint backend
  aqui (histórico persistente está fora de escopo — §8/OQ4); não mudar o contrato
  dos endpoints de IA.
- **Critério de conclusão (gate):** navegar e voltar mantém o insight; `lint`/`tsc`/
  jest verdes.

### Fase C.2 — Persistência de chat web em AIConversation (B20 backend) *(M)*
- **id:** `C.2`
- **slug:** `chat-persistence-backend`
- **Objetivo:** persistir o chat "Pergunte à IA" e listá-lo.
- **Depende de:** `C.1`.
- **Arquivos alterados:** `backend/app/models/ai_conversation.py` (enum),
  `backend/app/api/v1/ai.py`, `backend/app/schemas/ai.py`; **novo**
  `backend/alembic/versions/…_conversation_web.py`; possível service
  `backend/app/services/ai/conversation_service.py`.
- **Passos:** 1) adicionar `WEB = "web"` a `ConversationChannel`. 2) migração
  `ALTER TYPE conversationchannel ADD VALUE 'WEB'` — **atenção ao case**: usar o
  label que o SQLAlchemy persiste (nome do membro, coerente com a migração
  `corrige_case_enums`); verificar no repo qual case os labels de
  `conversationchannel` já usam e seguir. 3) ao responder `type=question`
  (`generate_insight`), fazer upsert da `AIConversation` `channel=WEB`,
  `external_chat_id=f"web:{user_id}"`, anexando `{role:"user"}` e `{role:"model"}`
  a `messages`. 4) `GET /ai/conversations` retorna a conversa web do usuário.
- **Testes:** teste de API: pergunta grava par user/model; `GET /ai/conversations`
  retorna o histórico (AC-C2). Rodar em PG (enum real).
- **Escopo travado / violações BLOQUEANTES:** não quebrar canais `telegram`/
  `whatsapp`; não tornar `external_chat_id` nullable; lógica de persistência em
  service, não no router; migração de enum revisada à mão.
- **Critério de conclusão (gate):** migração aplica em PG; par gravado e listável.

### Fase C.3 — UI de histórico do chat (B20 frontend) *(S)*
- **id:** `C.3`
- **slug:** `chat-history-ui`
- **Objetivo:** exibir o histórico do chat ao abrir.
- **Depende de:** `C.2`.
- **Arquivos alterados:** `frontend/lib/hooks/useAI.ts` (novo `useChatHistory`),
  `frontend/app/(dashboard)/insights/page.tsx` (ou o componente do chat).
- **Passos:** 1) `useChatHistory` (`useQuery` em `GET /ai/conversations`). 2)
  renderizar as mensagens anteriores acima do input; ao enviar, invalidar/atualizar
  o histórico. 3) reusar o `MarkdownLite` já existente para o texto do modelo.
- **Testes:** jest de render do histórico mockado (AC-C3).
- **Escopo travado / violações BLOQUEANTES:** não expor chave de IA; seguir glass/neu.
- **Critério de conclusão (gate):** reabrir o chat mostra as mensagens; `lint`/`tsc`/
  jest verdes.

### Track D — Recuperação de senha (B15)

### Fase D.1 — EmailService (SMTP + fallback console) *(M)*
- **id:** `D.1`
- **slug:** `email-service`
- **Objetivo:** habilitar envio de e-mail transacional.
- **Depende de:** `C.3`.
- **Arquivos novos:** `backend/app/services/email_service.py`. **Alterados:**
  `backend/app/core/config.py`, `.env.example`, `backend/pyproject.toml`
  (dependência `aiosmtplib`).
- **Passos:** 1) vars `SMTP_HOST`/`SMTP_PORT`/`SMTP_USER`/`SMTP_PASSWORD`/
  `SMTP_FROM` em `Settings` (defaults vazios). 2) `EmailService.send(to, subject,
  html)`: se `SMTP_HOST` vazio, `logger.info` do conteúdo (dev) e retorna; senão
  envia via `aiosmtplib`. 3) placeholders correspondentes em `.env.example`.
- **Testes:** unit com SMTP mockado + caso "sem SMTP loga e não falha".
- **Escopo travado / violações BLOQUEANTES:** nunca commitar credenciais reais;
  `.env.example` só placeholders; corpo do e-mail em pt-BR (rule naming).
- **Critério de conclusão (gate):** testes verdes; sem SMTP não quebra.

### Fase D.2 — Endpoints forgot/reset + token de reset *(M)*
- **id:** `D.2`
- **slug:** `password-reset-backend`
- **Objetivo:** fluxo backend de recuperação de senha.
- **Depende de:** `D.1`.
- **Arquivos alterados:** `backend/app/core/security.py` (novo
  `create_reset_token`/validação), `backend/app/api/v1/auth.py`,
  `backend/app/schemas/user.py`; reuso de `auth_service` (blacklist).
- **Passos:** 1) `create_reset_token(user_id)` = JWT `type=reset`, exp ≤ 1h.
  2) `POST /auth/forgot-password` (`ForgotPasswordRequest{email}`): busca usuário;
  se existe, gera token e `EmailService.send` com link; **resposta uniforme**
  (mesmo corpo/HTTP exista ou não). 3) `POST /auth/reset-password`
  (`ResetPasswordRequest{token,new_password}`): valida `type=reset` + não
  blacklistado; troca `password_hash` (`hash_password`); blacklista o token
  (single-use, reusa `blacklist_token`).
- **Testes:** API: forgot uniforme p/ email inexistente (AC-D1); reset single-use
  (AC-D2); login com nova senha (AC-D3).
- **Escopo travado / violações BLOQUEANTES:** não vazar existência de e-mail;
  token single-use obrigatório; auth é alto risco — cobrir com teste; sem regra no
  router além de orquestração.
- **Critério de conclusão (gate):** os 3 ACs verdes; `make check` backend verde.

### Fase D.3 — Telas de forgot/reset + link no login *(M)*
- **id:** `D.3`
- **slug:** `password-reset-ui`
- **Objetivo:** UX de recuperação de senha.
- **Depende de:** `D.2`.
- **Arquivos novos:** `frontend/app/(auth)/forgot-password/page.tsx`,
  `frontend/app/(auth)/reset-password/page.tsx`. **Alterados:**
  `frontend/app/(auth)/login/page.tsx`, hook/API client.
- **Passos:** 1) tela forgot (input e-mail → `POST /auth/forgot-password`, sempre
  mensagem de "se existir, enviamos o link"). 2) tela reset (lê `token` da query →
  `POST /auth/reset-password`). 3) link "Esqueci minha senha" no login. Seguir
  glass/neu.
- **Testes:** jest de render/submit das telas (mocks).
- **Escopo travado / violações BLOQUEANTES:** não exibir se e-mail existe; seguir
  ADR-007; não logar token no console de produção.
- **Critério de conclusão (gate):** fluxo E2E manual funciona em dev; `lint`/`tsc`/
  jest verdes.

### Fase D.4 — Corrigir copy "Gemini 2.5 Flash" *(S)*
- **id:** `D.4`
- **slug:** `fix-gemini-copy`
- **Objetivo:** alinhar a copy de auth ao provedor real (ADR-002).
- **Depende de:** `C.3`.
- **Arquivos alterados:** `frontend/components/auth/AuthLeftPanel.tsx`,
  `frontend/components/auth/AuthBackground.tsx`.
- **Passos:** 1) substituir "Gemini 2.5 Flash" por "Groq · Llama" (ou equivalente
  fiel ao ADR-002) nos 3 pontos (`AuthLeftPanel.tsx:10,11`, `AuthBackground.tsx:31`).
- **Testes:** grep/asserção de que "Gemini" não aparece mais nos componentes de auth
  (AC-D4).
- **Escopo travado / violações BLOQUEANTES:** só a copy; nenhuma mudança de layout
  ou lógica.
- **Critério de conclusão (gate):** "Gemini" ausente; `lint`/`tsc` verdes.

## 6. Riscos

| # | Risco | Prob. | Impacto | Mitigação |
|---|---|---|---|---|
| 1 | Migração age→birth_date perde precisão (01/01 aproximado) | Alta | Baixo | Documentado (OQ2); usuário pode ajustar no form; downgrade recria `age` |
| 2 | `ALTER TYPE … ADD VALUE` de enum não roda em transação em PG antigo | Média | Médio | PG 16 (compose) suporta; migração isolada, revisada à mão em PG de teste |
| 3 | Troca de fórmula (Harris→Mifflin) muda valores exibidos ao usuário | Média | Baixo | Documentado (OQ1); testes com valores conhecidos; card explica a fórmula |
| 4 | Reset de senha vaza existência de e-mail por timing/resposta | Média | Alto | NFR-3: resposta uniforme; teste AC-D1; token single-use |
| 5 | SMTP mal configurado quebra forgot em prod | Média | Médio | Fallback console em dev; erro de envio não vaza; validar SMTP no rollout |
| 6 | Migração de hooks para `useQuery` quebra telas de insights | Baixa | Médio | Fase isolada (C.1) com testes; sem mudança de contrato de API |

## 7. Rollout

- **Ordem operacional:** B → A → C → D, uma fase por vez
  (`/execute-spec-phase` → `/evaluate-spec-phase`, gate 8.5). O grafo de
  dependências (§5) força essa ordem.
- **Migrações:** A.1 (`birth_date`) e C.2 (`WEB`) rodam via `alembic upgrade head`
  no deploy (o `cd.yml` já aplica Alembic ao mergear `main`). Rodar em PG de teste
  antes.
- **Config nova:** vars SMTP entram no `.env` do servidor no rollout do Track D;
  sem elas o forgot degrada para log (não quebra).
- **Rollback:** cada migração tem `downgrade`; a copy e os hooks são revertíveis por
  reverter o commit da fase. Auth (D) só ativa quando as vars SMTP estiverem
  presentes.

## 8. Open Questions

> Resolvidas por default recomendado após o owner delegar ("usa suas
> recomendações") e ausentar-se na Fase 3. Revisáveis pelo owner antes de executar
> cada track.

- **OQ1 (Track A) — Fórmula de TDEE/TMB. RESOLVIDO (2026-07-02):** adotar
  **Mifflin-St Jeor** no lugar de Harris-Benedict. Justificativa: é a fórmula que o
  ledger e a decision já prometeram, mais precisa, e B12 é justamente sobre
  transparência/correção do cálculo. Custo: muda o valor calculado (coberto por
  teste com valores conhecidos).
- **OQ2 (Track A / B11) — Migração age→birth_date. RESOLVIDO (2026-07-02):**
  **derivar** `birth_date = 01/01/(ano_atual − age)` na migração e dropar `age`.
  Justificativa: não deixa TDEE null para perfis existentes; data aproximada é
  aceitável e ajustável no form. Alternativa rejeitada: birth_date nullable exigindo
  re-preenchimento (deixaria TDEE null no meio-tempo).
- **OQ3 (Track A / B12) — Origem de `current_weight`. RESOLVIDO (2026-07-02):**
  popular automaticamente do último `WeightLog` via `WeightService.latest()`.
  Justificativa: `latest()` já existe; diff mínimo; sem novo campo no form.
- **OQ4 (Track C / B16) — Persistência de insights. RESOLVIDO (2026-07-02):**
  **frontend-only** (`useQuery` + `staleTime`), padrão do `useProfile`. Histórico
  persistente no backend fica **fora de escopo** desta spec (futura). Justificativa:
  resolve o "some ao navegar" com diff mínimo e sem migração.
- **OQ5 (Track C / B20) — Reuso de `AIConversation`. RESOLVIDO (2026-07-02):**
  adicionar valor `WEB` ao enum + `external_chat_id="web:{user_id}"`. Justificativa:
  evita tabela nova e mudança de nullability; o modelo já suporta `messages` JSON.
- **OQ6 (Track D / B15) — Provedor de e-mail e token. RESOLVIDO (2026-07-02):**
  **SMTP genérico** (`aiosmtplib`) com fallback console em dev; token de reset via
  **JWT `type=reset`** (reusa `security.py`) single-use por blacklist Redis (reusa
  `auth_service`). Justificativa: sem dependência de serviço pago, funciona offline
  em dev, reusa os precedentes de token do projeto (ADR-005).

## 9. Definition of Done (gate por etapa)

**Gate por fase (cada fase só fecha com seu critério de conclusão verde):**
- [ ] **B.1** `hydration-service-crud` — CRUD no service com ownership + testes.
- [ ] **B.2** `hydration-api-crud` — endpoints DELETE/PUT + testes de API.
- [ ] **B.3** `hydration-ui-list` — lista com remover/editar; total atualiza.
- [ ] **A.1** `profile-birthdate-schema` — migração age→birth_date aplica em PG.
- [ ] **A.2** `tdee-mifflin-calc` — Mifflin-St Jeor + TMB + current_weight do último log.
- [ ] **A.3** `profile-tdee-api` — contrato expõe birth_date/bmr/tdee/fórmula.
- [ ] **A.4** `profile-tdee-ui` — date picker + card TMB/TDEE.
- [ ] **C.1** `insights-usequery-cache` — insights persistem ao navegar.
- [ ] **C.2** `chat-persistence-backend` — canal WEB + persistência + listagem.
- [ ] **C.3** `chat-history-ui` — histórico exibido ao reabrir.
- [ ] **D.1** `email-service` — SMTP + fallback console.
- [ ] **D.2** `password-reset-backend` — forgot/reset uniforme + token single-use.
- [ ] **D.3** `password-reset-ui` — telas forgot/reset + link no login.
- [ ] **D.4** `fix-gemini-copy` — "Gemini" ausente dos componentes de auth.

**Transversais (globais):**
- [ ] Cada FR com ao menos um AC coberto por teste (pytest/jest).
- [ ] `make check` verde (ruff + mypy strict + pytest + lint/tsc/jest frontend).
- [ ] Mudanças de schema (A.1, C.2) com migração Alembic revisada; migrations
      existentes intactas.
- [ ] Nenhum segredo/SMTP/PII vazado no diff; `.env.example` só com placeholders.
- [ ] `GROQ_API_KEY` não exposta ao frontend; mensagens ao usuário em pt-BR.
- [ ] Sem regressão nos fluxos existentes de hidratação, perfil, insights e auth.
