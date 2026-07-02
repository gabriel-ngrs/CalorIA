---
spec: 001-backlog-features-qa-v1
fase: A.4
slug_fase: profile-tdee-ui
status: executado
tentativa: 1
reprovacoes: 0
sha_inicial: f5d32fd14f52961d6c98d89e9150f8f9b20c5eb8
sha_final: a72cd1cf56e7ba5952230e8ef0930b42113be384
range: f5d32fd14f52961d6c98d89e9150f8f9b20c5eb8..a72cd1cf56e7ba5952230e8ef0930b42113be384
---

# FASE A.4 — Relatório de execução

## 1. Resumo do que foi feito

A página de perfil trocou o campo de idade por um **seletor de data de
nascimento** (`<Input type="date">`), passa a enviar `birth_date` no update e
exibe um **card TMB/TDEE** com o valor da TMB (`bmr`), o TDEE e a fórmula
(`Mifflin-St Jeor`), com **estado vazio** quando o TDEE ainda não pôde ser
calculado. O label da fórmula foi corrigido de "Harris-Benedict" para
"Mifflin-St Jeor". O onboarding (consumidor do mesmo tipo) migrou seu passo 1 de
idade para data de nascimento. Teste jest cobre AC-A4 (3 casos).

## 2. Arquivos CRIADOS

| Arquivo | Propósito |
|---------|-----------|
| `frontend/__tests__/app/perfil.test.tsx` | AC-A4: date picker presente (sem campo idade); card TMB/TDEE com fórmula; estado sem TDEE. |

## 3. Arquivos ALTERADOS

| Arquivo | O que mudou |
|---------|-------------|
| `frontend/app/(dashboard)/perfil/page.tsx` | State `age`→`birthDate`; input `type="date"` (max=hoje) com label "Data de nascimento"; card exibe TMB (`bmr`) + TDEE + fórmula (`profile.formula`); caption corrigida (Mifflin); card de estado vazio quando `tdee_calculated` é null. |
| `frontend/app/onboarding/page.tsx` | `Step1Fields.age`→`birthDate`; input do passo 1 vira `type="date"`; envia `birth_date` (era `age`); pré-preenche de `profile.birth_date`. |

## 4. Confirmação do REUSO e decisões de design

- **Reuso confirmado (§4 / ADR-007):** estendi o card e o banner **já existentes**
  (glass/neu), reusando o componente `Input`, `Card`, `Label` e os tokens de cor/
  espaçamento vigentes — sem introduzir dependência nem novo padrão visual. O card
  TMB/TDEE é a evolução do "TDEE banner" que já existia.
- **Date picker = `<Input type="date">`:** decisão deliberada em vez do
  `calendar.tsx`+`popover` (também disponíveis). Razão: é um seletor de data
  **nativo, acessível por teclado, sem armadilha de foco** e consistente com os
  demais inputs desta tela (que já usam o componente `Input`); atende "seletor de
  data de nascimento" com **diff mínimo**. `max` = hoje impede data futura.
- **Não recalcular no front (escopo travado):** o card lê `bmr`/`tdee_calculated`/
  `formula` do backend (A.3); nada é calculado no cliente.
- **Correção de copy (Harris→Mifflin):** o banner exibia "Harris-Benedict"
  hard-coded; agora usa `profile.formula` (vindo do backend) e o texto explica
  "TDEE = TMB × nível de atividade" (transparência — o objetivo de B12).
- **Extensão de escopo declarada — `onboarding/page.tsx`:** não está na lista de
  arquivos de A.4 na spec, mas consome `UserProfile` (alterado em A.3) via
  `profile.age` — deixaria o `tsc` vermelho (herdado de A.3). Migrado com diff
  mínimo (mesmo padrão de date input). **Nota:** o onboarding envia
  `current_weight_kg` (nome divergente do backend `current_weight`) — **pré-existente
  e fora do escopo desta spec**, não toquei.

### Self-review das skills de UI (fase toca interface)
- **avoid-ai-look:** contexto = usuário pessoal de diário alimentar, tom
  saudável/direto, referência = a própria página de perfil. Mantive o design system
  estabelecido (ADR-007) em vez de decorar; nenhum gradiente/efeito novo empilhado;
  o chip de ícone é o padrão já vigente na tela (consistência, não "cara de IA").
- **visual-consistency:** só tokens/escala existentes (`text-muted-foreground`,
  `bg-orange-500/15`, `pt-5 pb-5`, `mt-1/1.5`); nenhum hex solto novo; sem quarto
  tom de cinza. Hierarquia preservada (TDEE é o número primário do card).
- **accessibility-audit:** input de data com `<Label htmlFor="birth_date">`
  associado (teclado + leitor de tela; picker nativo, sem focus-trap); estado vazio
  comunica por **texto** (título "TMB/TDEE ainda indisponível" + explicação), não só
  por cor; comparação de meta usa cor **e** texto ("X kcal abaixo do TDEE").

## 5. Comandos rodados + saídas reais

```text
# type-check frontend (tsc) — agora LIMPO (fecha os 3 erros transitórios de A.3)
$ npx tsc --noEmit
# (sem saída — 0 erros)

# lint frontend (next lint --no-cache, como o Makefile lint-check)
$ npm run lint -- --no-cache
# Só 1 warning PRÉ-EXISTENTE em components/auth/Plasma.tsx
# (react-hooks/exhaustive-deps), não tocado por esta fase.

# jest — teste da fase (AC-A4)
$ npx jest __tests__/app/perfil.test.tsx
PASS __tests__/app/perfil.test.tsx
  ✓ exibe seletor de data de nascimento, não campo de idade
  ✓ exibe o card com TMB, TDEE e a fórmula
  ✓ mostra aviso quando o TDEE ainda não pôde ser calculado
Tests: 3 passed, 3 total

# jest — suíte completa (regressão)
$ npm test
Test Suites: 2 failed, 11 passed, 13 total
Tests: 3 failed, 74 passed, 77 total
#   → os 3 fails são MacroCards/MacroPieChart, PRÉ-QUEBRADOS e explicitamente
#     FORA DE ESCOPO desta spec (nota de planning, "testes de front pré-quebrados
#     MacroCards/MacroPieChart"). Verifiquei com `git stash` das mudanças de
#     frontend: falham igual SEM A.4 (3 failed, 6 passed) → não são regressão.

# grep de segredo/PII (esperado: 0)
# nenhum segredo; só UI.
```

## 6. Critérios de aceite da fase (com evidência)

- [x] **AC-A4** — `perfil.test.tsx`:
  (1) `getByLabelText(/Data de nascimento/)` é um `input[type=date]` e **não** há
  campo "Idade" (`queryByLabelText(/^Idade/)` → null);
  (2) o card exibe TDEE (`2554`), TMB (`1648 kcal/dia`) e a fórmula
  (`Mifflin-St Jeor`);
  (3) sem TDEE, aparece "TMB/TDEE ainda indisponível".

## 7. Definition of Done da fase

- [x] `tsc` do front **limpo** (0 erros — fecha os transitórios herdados de A.3)
- [x] `npm run lint` sem novos erros (1 warning pré-existente em `Plasma.tsx`)
- [x] jest da fase verde (3/3); suíte sem regressão (as 3 falhas são pré-quebradas
  e fora de escopo — comprovado por `git stash`)
- [x] Formulário salva `birth_date`; card exibe TMB/TDEE + fórmula
- [x] Escopo travado: não reintroduz idade; segue glass/neu; não recalcula TDEE no
  front
- [x] Nenhum segredo/PII
- [x] Commit em pt-BR (Conventional Commits), sem menção a autor/IA

## 8. (Em rework) O que mudou nesta tentativa

N/A — primeira execução.

## 9. Itens em aberto / dúvidas para o avaliador

- **`onboarding/page.tsx` fora da lista de A.4:** incluído por ser consumidor do
  tipo `UserProfile` (senão `tsc` ficaria vermelho). Diff mínimo.
- **`current_weight_kg` no onboarding:** divergência de nome com o backend
  (`current_weight`) é **pré-existente** e fora do escopo — sinalizo mas não corrigi.
- **3 testes front pré-quebrados** (`MacroCards`/`MacroPieChart`): fora de escopo por
  decisão da spec; a serem tratados por `/bugfix`. Não são regressão de A.4.
- **Track A completo:** A.1→A.4 executados em sequência nesta run; migração
  `birth_date` aplicada à mão no PG de dev (CI/CD desabilitado, §7).
