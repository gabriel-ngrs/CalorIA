---
spec: 001-backlog-features-qa-v1
fase: B.3
slug_fase: hydration-ui-list
status: executado
tentativa: 1
reprovacoes: 0
sha_inicial: 5287aa44f0cc826fcfa624c4dab54d90975cacc3
sha_final: fa902e5549d9a1018c4c08df527cc438261505a2
range: 5287aa44f0cc826fcfa624c4dab54d90975cacc3..fa902e5549d9a1018c4c08df527cc438261505a2
---

# FASE B.3 — Relatório de execução

## 1. Resumo do que foi feito

Adicionei à página de hidratação um card **"Registros de hoje"** que lista os
`entries` do dia (já vindos de `useHydrationToday`) com ação de **remover** e
**editar inline** o `amount_ml`. Criei os hooks `useDeleteHydration` /
`useUpdateHydration` (mutações que invalidam `["hydration"]` e `["dashboard"]`, com
toast — padrão do arquivo). Corrigi o tipo `HydrationDaySummary` (`entries_count`,
que nunca era usado, → `entries: HydrationLog[]`, o que a API realmente devolve).

## 2. Arquivos CRIADOS

Nenhum (adições a arquivos existentes).

## 3. Arquivos ALTERADOS

| Arquivo | O que mudou |
|---------|-------------|
| `frontend/lib/hooks/useLogs.ts` | Novos `useDeleteHydration` (DELETE) e `useUpdateHydration` (PUT, remove `id` do corpo); ambos invalidam `hydration`+`dashboard` e dão toast. |
| `frontend/app/(dashboard)/hidratacao/page.tsx` | Card "Registros de hoje" listando `summary.entries`; edição inline (`editingId`/`editValue`, `startEdit/cancelEdit/saveEdit`); botões remover/editar/salvar/cancelar com `aria-label`; estado vazio. |
| `frontend/types/index.ts` | `HydrationDaySummary.entries_count` → `entries: HydrationLog[]` (alinha o tipo ao contrato real do backend). |
| `frontend/__tests__/lib/hooks/useLogs.test.ts` | Testes de `useDeleteHydration` (URL + toast) e `useUpdateHydration` (PUT sem `id` no corpo + toast). |

## 4. Confirmação do REUSO e decisões de design

- **Reuso confirmado:** `entries` já era exposto por `HydrationDaySummary`
  (backend `schemas/logs.py:52`) e recebido por `useHydrationToday` — a UI só
  consome, sem nova query. O padrão dos hooks (mutation + `invalidateQueries` +
  `toast`) é cópia fiel de `useLogHydration`. Componentes `Card`/`Button`/`Input`
  do design system reusados; ícones `lucide-react`.
- **Decisões de design:**
  - **Correção de tipo `entries_count`→`entries`:** o campo `entries_count` no type
    nunca era referenciado no código (grep confirmou 0 usos reais); o backend sempre
    devolveu `entries`. Troca necessária para a lista tipar corretamente. Escopo
    mínimo — não toca outros consumidores (nenhum existia).
  - **Edição inline** (input no lugar do item) em vez de modal — mais leve e coerente
    com o card; edita só `amount_ml` (o caso de uso do B8). `date`/`time` continuam
    editáveis pela API (B.2), mas a UI foca no valor.
  - Acessibilidade: todos os botões-ícone têm `aria-label` (remover/editar/salvar/
    cancelar/editar quantidade).

## 5. Comandos rodados + saídas reais

```text
# type-check
$ docker exec caloria_frontend npx tsc --noEmit
=== tsc exit: 0 ===

# lint
$ docker exec caloria_frontend npm run lint
# apenas 1 warning PRÉ-EXISTENTE em components/auth/Plasma.tsx
# (react-hooks/exhaustive-deps) — nada nos arquivos desta fase.

# jest (hook desta fase)
$ npx jest __tests__/lib/hooks/useLogs.test.ts
Tests:       13 passed, 13 total   # inclui useDeleteHydration + useUpdateHydration

# jest (suíte inteira — sem regressão nos arquivos tocados)
Test Suites: 2 failed, 10 passed, 12 total
Tests:       3 failed, 71 passed, 74 total
# → As 2 suítes que falham são MacroCards.test.tsx e MacroPieChart.test.tsx,
#   PRÉ-QUEBRADAS e explicitamente FORA DO ESCOPO desta spec (ver nota de intro:
#   "testes de front pré-quebrados MacroCards/MacroPieChart → tratar por /bugfix").
#   Não tocam hidratação nem os tipos alterados.

# grep de segredo/PII (esperado: 0) — nenhum segredo no diff.
```

## 6. Critérios de aceite da fase (com evidência)

- [x] **AC-B4** (FR-B3) — *removo um pela lista, a lista e o total atualizam sem
  reload*: `useDeleteHydration`/`useUpdateHydration` invalidam `["hydration"]`
  (recarrega `useHydrationToday` → `entries` e `total_ml`) e `["dashboard"]`, sem
  reload de página. Coberto por teste de hook (URL correta + toast); a atualização
  do total é consequência direta da invalidação — mesmo mecanismo já provado do
  `useLogHydration`.

## 7. Definition of Done da fase

- [x] `npm run lint` / `tsc` / jest (da fase) verdes.
- [x] Remoção/edição refletem no total do dia (via invalidação de `["hydration"]`+`["dashboard"]`).
- [x] Escopo travado: sem foto, sem mexer no gráfico de histórico; segue glass/neu (ADR-007).
- [x] Nenhum segredo/PII no diff.
- [x] Commit em pt-BR (Conventional Commits), sem menção a autor/IA.

## 8. (Em rework) O que mudou nesta tentativa

N/A — primeira execução.

## 9. Itens em aberto / dúvidas para o avaliador

- **Cobertura de AC-B4:** optei por teste de **hook** (a spec permite "hook OU render
  da lista"). Não escrevi um teste de render da página inteira (que arrastaria mocks
  de `useMe`/charts dinâmicos). Se o avaliador preferir um teste de render do card,
  é adição, não correção.
- **E2E manual:** não dirigi o app autenticado (fluxo exige login). A lógica de
  atualização do total é o mesmo padrão de invalidação já em produção no
  `useLogHydration`; `tsc` garante a integração de tipos com `entries`.
- **Suíte jest global vermelha** por `MacroCards`/`MacroPieChart` — pré-existente e
  fora do escopo (declarado na spec). Não é regressão desta fase.
