---
spec: 001-backlog-features-qa-v1
fase: C.1
slug_fase: insights-usequery-cache
status: executado
tentativa: 1
reprovacoes: 0
sha_inicial: 9ba0366f9770756f6ba64279a267d266fc1dfd52
sha_final: 32517df3111f69983879eadccc775b58f485d72f
range: 9ba0366f9770756f6ba64279a267d266fc1dfd52..32517df3111f69983879eadccc775b58f485d72f
---

# FASE C.1 — Relatório de execução

## 1. Resumo do que foi feito

Os 6 hooks de insights (`useDailyInsight`, `useWeeklyInsight`, `useEatingPatterns`,
`useNutritionalAlerts`, `useGoalAdjustment`, `useMonthlyReport`) foram migrados de
`useMutation` para `useQuery` com `queryKey` estável, de modo que o resultado
**persiste ao navegar** e voltar dentro da sessão (B16). O controle de custo Groq
foi preservado integralmente: cada query nasce `enabled: false` e só dispara via
`refetch()` no clique — nada roda no mount, foco de janela, reconexão ou
remontagem. A página de insights passou a ler de `query.data`/`isFetching` e a
disparar via `refetch()`.

## 2. Arquivos CRIADOS

| Arquivo | Propósito |
|---------|-----------|
| — | Nenhum arquivo novo (apenas alterações). |

## 3. Arquivos ALTERADOS

| Arquivo | O que mudou |
|---------|-------------|
| `frontend/lib/hooks/useAI.ts` | 6 hooks de insight migrados `useMutation`→`useQuery`; constante `INSIGHT_QUERY_OPTIONS` centraliza a config de custo (`enabled:false`, `staleTime:Infinity`, `gcTime:30min`, `refetchOnWindowFocus/Reconnect/Mount:false`). `useMonthlyReport(month, year)` passou a receber params por argumento (queryKey). `useAskQuestion`/`useMealSuggestion` mantidos como mutation (fora do escopo). |
| `frontend/app/(dashboard)/insights/page.tsx` | Botões dos 6 insights: `x.mutate(...)`→`x.refetch()`; loading/disabled/label `x.isPending`→`x.isFetching` (semântica correta para query disabled); `useMonthlyReport(reportMonth, reportYear)`. Cards de `mealSuggestion`/`askQuestion` inalterados. |
| `frontend/__tests__/lib/hooks/useAI.test.ts` | Testes dos 6 hooks reescritos para o comportamento de query: (a) **não dispara no mount** (controle de custo), (b) `refetch()` busca e retorna o dado, (c) **cache sobrevive à remontagem** (AC-C1). Testes de `useAskQuestion`/`useMealSuggestion` preservados. |

## 4. Confirmação do REUSO e decisões de design

- **Reuso confirmado:** seguiu o padrão `useQuery` já usado em `useProfile.ts`
  (`queryKey` + `staleTime`), conforme §4 da spec. `api` client reusado sem
  alteração de contrato dos endpoints de IA.
- **Decisão — `isPending` → `isFetching`:** para uma query com `enabled:false`, o
  `status` fica `pending` (sem dado) mesmo sem estar buscando, logo `isPending` é
  `true` no mount e mostraria o skeleton indevidamente. `isFetching` reflete
  "buscando agora" (o equivalente ao antigo `isPending` da mutation). Sem esse
  ajuste, o loading apareceria sozinho ao abrir a página.
- **Decisão — assert no retorno de `refetch()`:** no ambiente de teste
  (`renderHook` + query disabled), o `result.current` do **mesmo** observer não
  re-renderiza após `refetch()` (verificado empiricamente: `refetch()` retorna
  `status:success` + `data` corretos, mas `result.current.data` fica `undefined`).
  Os testes de busca assertam o valor de retorno de `refetch()`; o teste de
  persistência (AC-C1) monta um **novo** observer no mesmo `QueryClient`, que serve
  o dado do cache normalmente. Runtime real não é afetado (a página re-renderiza).
- **Escopo:** `useMealSuggestion` também "some ao navegar" mas **não** está na lista
  de FR-C1 — mantido como mutation, sem ampliar escopo. Nenhum endpoint/tabela de
  backend tocado (histórico persistente é OQ4, fora de escopo).
- **Nenhum outro desvio.**

## 5. Comandos rodados + saídas reais

```text
# type-check (frontend)
$ npx tsc --noEmit
EXIT_TSC:0   (sem saída — limpo)

# lint (frontend) — cache local sem permissão de escrita, rodado com --no-cache
$ npx next lint --no-cache
./components/auth/Plasma.tsx
156:26  Warning: react-hooks/exhaustive-deps (PRÉ-EXISTENTE, não tocado nesta fase)
EXIT:0

# testes da fase
$ npx jest __tests__/lib/hooks/useAI.test.ts
Test Suites: 1 passed, 1 total
Tests:       10 passed, 10 total

# suíte de frontend completa (regressão)
$ npx jest
Test Suites: 2 failed, 11 passed, 13 total
Tests:       3 failed, 79 passed, 82 total
# As 2 suítes que falham são MacroPieChart/MacroCards — PRÉ-QUEBRADAS e
# declaradas FORA DE ESCOPO na spec. Confirmado idêntico no HEAD base
# (git stash das mudanças → mesmas 3 falhas). Não são regressão desta fase.

# grep de segredo/PII (esperado: 0)
$ git diff --cached | grep -iE "api_key|secret|password|token=" | wc -l
0
```

## 6. Critérios de aceite da fase (com evidência)

- [x] **AC-C1 (FR-C1)** — *gero insight semanal, navego e volto, ainda visível
  sem regenerar.* Evidência: teste "mantém o insight ao remontar o hook (navegar e
  voltar — AC-C1)" — após `refetch()`, desmonta e remonta o hook no **mesmo**
  `QueryClient`; `data` continua presente e `api.post` foi chamado **1x só**
  (`toHaveBeenCalledTimes(1)`), provando que não houve regeneração. Config
  `staleTime:Infinity` + `gcTime:30min` + `refetchOnMount:false` garante a
  sobrevivência do cache.
- [x] **FR-C1 (controle de custo)** — *nenhuma query dispara sem clique.*
  Evidência: 6 testes "não dispara no mount" (`api.post/get not.toHaveBeenCalled`
  logo após montar); `enabled:false` + `refetchOnWindowFocus/Reconnect/Mount:false`.

## 7. Definition of Done da fase

- [x] Testes da fase verdes (10/10 em `useAI.test.ts`)
- [x] Comandos de validação limpos nos arquivos tocados (`tsc` 0, `lint` 0; jest da
      fase verde). Falhas pré-quebradas fora de escopo documentadas.
- [x] Escopo travado respeitado: nenhuma tabela/endpoint backend; contrato dos
      endpoints de IA inalterado; só os 6 hooks de FR-C1 migrados.
- [x] Nenhum segredo/PII em log/DTO/exceção.
- [x] Commits em pt-BR (Conventional Commits), sem menção a autor/IA.

## 8. (Em rework) O que mudou nesta tentativa

N/A — primeira execução.

## 9. Itens em aberto / dúvidas para o avaliador

- **`isFetching` vs `isPending`:** a troca é intencional e necessária para queries
  `enabled:false` (ver §4). Vale conferir se o comportamento de loading visual na
  página segue idêntico ao anterior (aparece só durante a busca).
- **Mudança de UX sutil:** ao trocar o período (`patternDays`/`alertDays`) ou
  mês/ano, a `queryKey` muda e o card volta a ficar vazio até novo clique — antes
  (mutation) o resultado anterior permanecia. É coerente com "o dado exibido deve
  casar com o período selecionado" e preserva o opt-in (não refaz a chamada
  sozinho). Sinalizado caso o avaliador prefira outra abordagem.
- **`useMealSuggestion` fora da lista de FR-C1:** mantido como mutation de
  propósito; se desejável migrá-lo também, seria uma extensão de escopo.
