---
spec: 001-backlog-features-qa-v1
fase: A.4
slug_fase: profile-tdee-ui
tentativa: 1
veredito: APROVADO
score: 9.7
threshold: 8.5
range_avaliado: f5d32fd14f52961d6c98d89e9150f8f9b20c5eb8..a72cd1cf56e7ba5952230e8ef0930b42113be384
---

# FASE A.4 — Avaliação independente

## 1. Veredito e score

**Veredito:** APROVADO · **Score:** 9.7 / threshold 8.5

Campo de idade substituído por seletor de data de nascimento (`<Input type="date">`,
`max`=hoje), envio de `birth_date`, card TMB/TDEE com fórmula do backend e estado vazio
por texto. AC-A4 coberto (3 casos jest). `tsc` limpo na ponta da branch. Nenhum
BLOQUEANTE, nenhum IMPORTANTE.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 4 | AC-A4: `__tests__/app/perfil.test.tsx` (date picker sem campo idade; card TMB/TDEE+fórmula; estado vazio). Não reintroduz idade; não recalcula no front. Dedução: `onboarding/page.tsx` fora da lista literal (consumidor do tipo — fecha `tsc`); `useProfile.ts`, listado na spec, **não** foi tocado (desnecessário — `Partial<UserProfile>` já aceita `birth_date` após A.3) |
| 2 | Arquitetura e direção de dependências | 3 | 5 | card lê `bmr`/`tdee_calculated`/`formula` do backend; nenhum cálculo no cliente |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | só UI; nenhum segredo/PII; `GROQ_API_KEY` não tocada |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | reusa `Card`/`Input`/`Label` e tokens glass/neu existentes; card é evolução do "TDEE banner" já presente (não novo padrão) |
| 5 | Padrões de domínio/aplicação | 2 | 5 | segue App Router + hooks React Query; `type="date"` nativo consistente com os demais inputs da tela |
| 6 | Local e nomes dos arquivos | 2 | 5 | `perfil/page.tsx`, `onboarding/page.tsx`, teste em `__tests__/app/` — corretos |
| 7 | Qualidade de código | 2 | 5 | diff mínimo; label associado (`htmlFor="birth_date"`); copy corrigida (Harris→`profile.formula`) |
| 8 | Testes e cobertura | 2 | 5 | 3 casos AC-A4 reexecutados (3/3); suíte sem regressão (as 3 falhas são MacroCards/MacroPieChart, intocados por A.4) |
| 9 | Migration safety | 2 | — | não se aplica (fase de UI) |

Score = (4·3+5·3+5·3+5·3+5·2+5·2+5·2+5·2) / (5·20) · 10 = 97/100 · 10 = **9.7**.

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

Nenhum.

## Revisão de UI (fase toca interface)

- **avoid-ai-look:** sem gradiente/efeito novo empilhado; reusa o design system vigente
  (ADR-007) e o padrão de chip de ícone já presente — consistência, não decoração.
- **accessibility-audit:** `<Label htmlFor="birth_date">` associado ao input; picker de
  data **nativo** (teclado + leitor de tela, sem focus-trap); estado vazio comunica por
  **texto** ("TMB/TDEE ainda indisponível" + instrução), não só por cor. Correto.
- **visual-consistency:** só tokens existentes (`text-muted-foreground`,
  `bg-orange-500/15`, `border-dashed`); nenhum hex solto; hierarquia preservada (TDEE é o
  número primário). Sem regressão visual no diff.

## 5. Sugestões

- **`onboarding/page.tsx` envia `current_weight_kg` (não persiste):** o backend
  `ProfileUpdate` espera `current_weight`, então o peso do onboarding é descartado
  silenciosamente. É **pré-existente** e fora do escopo desta spec (declarado). Efeito
  colateral: usuário recém-onboarded sem `WeightLog` fica com TDEE null — porém A.4 trata
  isso com o card de estado vazio. Sugiro endereçar por `/bugfix` à parte.
- **3 testes front pré-quebrados** (`MacroCards`/`MacroPieChart`): confirmadamente fora do
  escopo desta spec e não são regressão de A.4 — não tocam nenhum arquivo de Track A.

## 6. Comandos rodados + saídas reais

```text
$ npx tsc --noEmit
# (sem saída — 0 erros; fecha os 3 transitórios herdados de A.3)

$ npx eslint --no-cache "app/(dashboard)/perfil/page.tsx" "app/onboarding/page.tsx" \
    "types/index.ts" "__tests__/app/perfil.test.tsx"
# (sem saída — 0 erros/warnings nos arquivos da fase)
# nota: `npm run lint` (next lint) falha por permissão em .next/cache (owner root, artefato
# de docker) — ambiente, não código; rodei eslint direto nos arquivos tocados.

$ npx jest __tests__/app/perfil.test.tsx
Tests: 3 passed, 3 total

$ npx jest
Test Suites: 2 failed, 11 passed, 13 total
Tests: 3 failed, 74 passed, 77 total
# as 3 falhas = MacroCards.test.tsx / MacroPieChart (pré-quebradas, fora de escopo, não tocadas por A.4)
```

## 7. Itens da fase / DoD não atendidos

Nenhum. Gate ("`lint`/`tsc`/jest verdes; salva `birth_date`; card exibe TMB/TDEE")
atendido — `tsc` = 0, jest da fase 3/3, `birth_date` enviado em `handleSubmit`.

## 8. Divergências entre o relatório e o código real

Nenhuma. Date picker nativo, card com `profile.formula`, estado vazio e migração do
onboarding conferem com o diff `f5d32fd1..a72cd1cf`. A não-alteração de `useProfile.ts`
(listado na spec) é desnecessidade real, não omissão — o tipo já aceitava `birth_date`.
