---
versão: 1.1
lote: bugs-teste-v1
origem: bugs-teste-v1.txt
criado: 2026-07-02
atualizado: 2026-07-02
---

# Lote de bugs: bugs-teste-v1

Rodada de QA manual (primeira versão estável). 20 bugs registrados; BUG 1-3 já
corrigidos antes deste lote (commits `03a0941`/`ae3c580`). Este lote trata os
17 restantes.

> **Documento de origem intocado:** o `bugs-teste-v1.txt` na raiz **não** foi
> alterado nem migrado — este `.md` é o artefato de rastreio (ledger). Decisão
> consolidada em `.codeflow/decisions/2026-07-02-lote-bugs-teste-v1.md`.

Legenda da coluna `verificação`: `✓` verificado; `⚠` corrigido no código mas
**verificação em runtime pendente**; `—` não verificado.

## Bugs
| id | título | status | repro/teste | fix (arquivo:linha) | decision | verificação |
|----|--------|--------|-------------|---------------------|----------|-------------|
| B1 | Seed dev enums minúsculo | corrigido | (fora do lote) | scripts/seed_dev_user.py | — | — |
| B2 | Seed dev bind params meal_items | corrigido | (fora do lote) | scripts/seed_dev_user.py | — | — |
| B3 | Seed dev não cria usuário | corrigido | (fora do lote) | scripts/seed_dev_user.py | — | — |
| B4 | Plasma getBoundingClientRect de null | corrigido | repro manual: tela auth + mover mouse → sem overlay de erro (WebGL, sem teste jsdom) | frontend/components/auth/Plasma.tsx:121 | | ✓ navegador |
| B5 | Msg de erro 503 vira "verifique conexão" | corrigido | __tests__/lib/aiErrors.test.ts (jest ✓) | frontend/lib/aiErrors.ts + QuickAddModals.tsx:384 + refeicoes/page.tsx:730 | 2026-07-02-lote-bugs-teste-v1.md | ✓ jest + 500 observado |
| B6 | Lixeira do modal exclui na hora | corrigido | repro manual: editar refeição → lixeira → Cancelar → item permanece; Salvar → persiste | frontend/app/(dashboard)/refeicoes/page.tsx:417,425,848,859 | | ✓ navegador+API |
| B7 | Peso duplica registro no mesmo dia | corrigido | test_logs.py::TestWeightLog::test_segundo_registro_no_mesmo_dia_sobrescreve | app/services/log_service.py:46 + migration a7b8c9d0e1f2 | 2026-07-02-lote-bugs-teste-v1.md | ✓ pytest+API |
| B8 | Hidratação só-adição (sem editar/remover) | bloqueado | — | feature — ver backlog de specs | | — |
| B9 | Humor duplica registro no mesmo dia | corrigido | test_logs.py::TestMoodLog::test_segundo_registro_no_mesmo_dia_sobrescreve | app/services/log_service.py:150 + migration a7b8c9d0e1f2 | 2026-07-02-lote-bugs-teste-v1.md | ✓ pytest+API |
| B10 | Notificações: enum notificationtype REMINDER | corrigido | tests/unit/test_notification_enum.py | app/models/notification.py:32 | 2026-07-02-lote-bugs-teste-v1.md | ✓ insert no DB real |
| B11 | Perfil usa Idade fixa (vs data nascimento) | bloqueado | — | feature/breaking — ver backlog de specs | | — |
| B12 | Perfil não exibe TMB/TDEE | bloqueado | — | feature — ver backlog de specs | | — |
| B13 | Selects do Perfil esvaziam na navegação SPA | corrigido | repro manual: Perfil → outro módulo → Perfil; Selects mostram valores | frontend/app/(dashboard)/perfil/page.tsx:62,65,66 | | ✓ navegador |
| B14 | "Meta atingida" ignora goal_type | corrigido | __tests__/lib/weightGoal.test.ts (jest ✓) | frontend/lib/weightGoal.ts + peso/page.tsx:56,147 | 2026-07-02-lote-bugs-teste-v1.md | ✓ navegador |
| B15 | Sem recuperação de senha | bloqueado | — | feature grande — ver backlog de specs | | — |
| B16 | Insights somem ao navegar (sem histórico) | bloqueado | — | feature — ver backlog de specs | | — |
| B17 | suggest-meal determinístico | corrigido | repro manual: 3x "Nova sugestão" → resultados diferentes (LLM) | app/services/ai/insights_generator.py:158,145 | 2026-07-02-lote-bugs-teste-v1.md | ✓ runtime (Groq real, 3/3 varia) |
| B18 | Texto da IA com markdown cru | corrigido | __tests__/components/MarkdownLite.test.tsx (jest ✓) | frontend/components/MarkdownLite.tsx + insights/page.tsx:34,381 | 2026-07-02-lote-bugs-teste-v1.md | ✓ jest + runtime (IA emite markdown) |
| B19 | Respostas da IA muito verbosas | corrigido | repro manual: gerar alertas/ajuste/relatório → textos curtos (LLM) | app/services/ai/insights_generator.py:265,318,433 | 2026-07-02-lote-bugs-teste-v1.md | ✓ runtime (textos curtos) |
| B20 | Chat "Pergunte à IA" sem histórico | bloqueado | — | feature — ver backlog de specs | | — |

## Verificação em runtime (2026-07-02)
Stack `docker-compose.dev.yml` subido; migrações aplicadas (inclui `a7b8c9d0e1f2`,
sem erros); suíte backend **100 passando**; navegador logado (`qa@example.com`).
Confirmados end-to-end: **B4, B5, B6, B7, B9, B10, B13, B14**.

## Pendências de verificação — RESOLVIDO (2026-07-03)
A `GROQ_API_KEY` nova foi reposta e validada (chave `gsk_…`, len 56, ping Groq
`200 OK`). Os 3 fixes dependentes de IA foram reexecutados em runtime contra o
Groq **real** (Llama 3.3 70B), dirigindo os métodos reais de
`InsightsGenerator` com a camada de DB mockada (Postgres/Redis indisponíveis
nesta máquina; cache Redis degrada sem quebrar, como esperado):

- **B17** — `suggest_meal` 3× → **3/3 nomes distintos** (Frango c/ Feijão →
  Salada de Quinoa → Frango c/ Arroz e Queijo). Variação (random foco +
  `use_cache=False`) confirmada. `verificação: ✓`.
- **B19** — Alertas (8 linhas / 94 chars), Ajuste de metas (3 frases / 255
  chars), Relatório mensal (6 linhas / 375 chars) → todos **curtos e
  objetivos**. `verificação: ✓`.
- **B18** — Semanal emite `**negrito**` + lista numerada; Alertas e Mensal
  emitem bullets `-`; o `MarkdownLite` (jest ✓) renderiza esse markdown.
  Confirmado que a IA **emite** markdown em runtime. `verificação: ✓`.

Bônus (Track C): `answer_question` (chat "Pergunte à IA") respondeu corretamente
com a IA real — a chamada de IA do chat funciona; a **persistência** WEB em
`AIConversation` (C.2) depende do stack com Postgres e já está coberta pelos
testes de integração (avaliação C.2 APROVADO 9.5).

Estes 3 saíram de `⚠` para `✓` na tabela acima.

## Backlog de specs — bugs bloqueados (features / mudança quebradora)
Cada item abaixo saiu do loop de bugfix por exigir design/escopo maior. Pegar
para `/create-spec`:

- **B8 — Editar/remover hidratação.** Hoje o módulo só soma. Precisa: endpoints
  `DELETE /hydration/{id}` e/ou `PUT`; expor os **logs individuais** do dia (a
  API retorna só o resumo agregado `HydrationDaySummary`); UI de lista com
  remover/editar (ou "desfazer último"). Ref: `api/v1/hydration.py`,
  `HydrationService` (`log_service.py:54`), `hidratacao/page.tsx`.
- **B11 — Data de nascimento em vez de Idade fixa.** **Mudança de schema
  quebradora**: trocar `user_profiles.age` por `birth_date` (migração + migração
  de dados), derivar idade no cálculo de TDEE/TMB, ajustar formulário. Decidir
  compatibilidade com dados existentes. Ref: `perfil/page.tsx`, `models/profile.py`,
  `services/nutrition/tdee.py`.
- **B12 — Exibir TMB/TDEE + explicação do cálculo.** Feature de transparência.
  **Causa-raiz do `tdee_calculated` null já achada:** `profile.current_weight`
  **nunca é populado** (o form envia só height/age/sex/activity), então o `if`
  em `ProfileService.update_profile` não calcula TDEE. Decidir de onde vem
  `current_weight` (último `weight_log`? campo no form?) e então exibir TMB/TDEE
  + fórmula (Mifflin-St Jeor). Relacionado a B11.
- **B15 — Recuperação de senha.** Feature grande: provedor de e-mail/SMTP +
  endpoints `forgot-password`/`reset-password` com token expirável + telas.
  Backend hoje só tem register/login/refresh/logout/me. Sem config SMTP.
  (Obs. de marketing relacionada: a copy do login cita "Gemini 2.5 Flash", mas o
  projeto usa Groq/Llama — texto desatualizado, corrigir junto.)
- **B16 — Persistir/histórico de Insights.** Tudo vive em `useState`/`mutation.data`
  e some ao navegar. Usar React Query com queryKey estável + staleTime, e/ou
  histórico no backend. Ref: `insights/page.tsx`. Relacionado a B20.
- **B20 — Histórico do chat "Pergunte à IA".** O modelo `AIConversation` existe
  mas não é aproveitado; faltam endpoints de salvar/listar conversas + UI de
  histórico. Relacionado a B16.

## Observações / bugs incidentais encontrados (fora da lista original)
Achados durante a execução — **não** estavam no `.txt`, registrados para triagem:

1. **`manifest.webmanifest` com erro de sintaxe** — o console do navegador
   acusa `Manifest: Line: 1, column: 1, Syntax error` em **todas** as páginas.
   O manifest do PWA não está sendo servido como JSON válido. Baixo impacto
   (PWA/instalação), mas real. Ref: `frontend/app/manifest.ts`.
2. **Testes de frontend pré-existentes quebrados** — `MacroCards.test.tsx` e
   `MacroPieChart.test.tsx` (3 testes) já falhavam **antes** deste lote (não
   tocados por mim). O `make check`/CI não está verde por causa deles.
3. **Backend mapeia falha de auth do Groq para HTTP 500** — `POST /ai/analyze-meal`
   com chave inválida devolve **500** (genérico) em vez de **503** (IA
   indisponível). O fix de B5 no front já trata ambos, mas o ideal seria o
   backend retornar 503 para "IA fora" de forma consistente. Ref: `api/v1/ai.py`.
