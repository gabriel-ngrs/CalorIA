---
spec: 001-backlog-features-qa-v1
fase: C.1
slug_fase: insights-usequery-cache
tentativa: 1
veredito: APROVADO
score: 9.8
threshold: 8.5
range_avaliado: 9ba0366f9770756f6ba64279a267d266fc1dfd52..32517df3111f69983879eadccc775b58f485d72f
---

# FASE C.1 — Avaliação independente

## 1. Veredito e score

**Veredito:** APROVADO · **Score:** 9.8 / threshold 8.5

Migração dos 6 hooks de insight de `useMutation` para `useQuery` com controle de
custo Groq integral (`enabled:false` + `refetch()` no clique). AC-C1 (cache
sobrevive à navegação) coberto por teste real. Escopo travado respeitado (nenhum
endpoint/tabela de backend; contrato de IA inalterado). Zero achados bloqueantes
ou importantes.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 5 | `useAI.ts:12-22` `INSIGHT_QUERY_OPTIONS` = `enabled:false`+`staleTime:Infinity`+`gcTime:30min`+`refetchOnWindowFocus/Reconnect/Mount:false` (FR-C1). Testes "NÃO dispara no mount" verdes p/ os 6 hooks. Nenhum backend tocado (OQ4 respeitado). |
| 2 | Arquitetura e direção de dependências | 3 | 5 | Config centralizada numa constante espalhada nos 6 hooks; `page.tsx` lê `query.data`/`isFetching` e chama `refetch()`. Sem inversão de dependência. |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | `GROQ_API_KEY` não exposta; risco #6 (auto-fetch queimar quota) mitigado — testes provam que nada dispara no mount/foco. |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | Espelha o padrão `useQuery`+`staleTime` de `useProfile.ts` (§4 da spec); `INSIGHT_QUERY_OPTIONS` evita repetir a config 6×. |
| 5 | Padrões de domínio/aplicação | 2 | 5 | `queryKey` estável e parametrizada (`["ai","patterns",days]`, `["ai","monthly-report",month,year]`); convenção React Query do projeto. |
| 6 | Local e nomes dos arquivos | 2 | 5 | Só `useAI.ts`, `insights/page.tsx` e o teste — exatamente os arquivos declarados na fase. |
| 7 | Qualidade de código | 2 | 5 | Comentário registra o "porquê" (custo Groq); `isPending`→`isFetching` justificado e correto p/ query `enabled:false`. `tsc` e `next lint` limpos. |
| 8 | Testes e cobertura | 2 | 5 | 10 testes: mount-não-dispara (×6), refetch busca, e cache sobrevive à remontagem com `api.post` chamado 1× (AC-C1). Suíte da fase 12/12 no HEAD. |
| 9 | Migration safety (se aplicável) | 2 | — | Não se aplica (fase só frontend). |

Média ponderada (dims 1–8, peso total 20) = 100/20 = 5.0 → **9.8/10** (desconto
simbólico pela limitação de teste descrita na Sugestão 1, sem impacto funcional).

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

Nenhum.

## 5. Sugestões

1. **Teste de persistência assevera o retorno de `refetch()`, não `result.current.data`**
   (`useAI.test.ts` — testes "busca via refetch"): documentado no EXECUCAO §4 como
   limitação do `renderHook` com query `enabled:false`. O teste de remontagem
   (AC-C1) compensa assertando o cache num novo observer. Sem ação necessária;
   apenas registrado.
2. **UX ao trocar período/mês** (`insights/page.tsx`): mudar `patternDays`/`alertDays`/
   mês altera a `queryKey` e esvazia o card até novo clique (antes, com mutation, o
   resultado anterior permanecia). É coerente com "o dado exibido casa com o período
   selecionado" e preserva o opt-in; comportamento aceitável.

## 6. Comandos rodados + saídas reais

```text
$ cd frontend && npx tsc --noEmit
TSC_EXIT=0   (limpo)

$ npx next lint --no-cache
./components/auth/Plasma.tsx 156:26 Warning react-hooks/exhaustive-deps
  (PRÉ-EXISTENTE, arquivo não tocado nesta fase)
LINT_EXIT=0   (0 erros)

$ npx jest __tests__/lib/hooks/useAI.test.ts
Test Suites: 1 passed, 1 total
Tests:       12 passed, 12 total   (inclui os 2 hooks de C.3 no HEAD atual)

$ npx jest    (suíte completa — regressão)
Test Suites: 2 failed, 11 passed, 13 total
Tests:       3 failed, 81 passed, 84 total
# As 3 falhas são MacroCards/MacroPieChart — PRÉ-QUEBRADAS e declaradas FORA DE
# ESCOPO na spec (nota de planning). Não tocam arquivos de C.1.
```

## 7. Itens da fase / DoD não atendidos

Nenhum. Critério de conclusão da fase (navegar e voltar mantém o insight;
`lint`/`tsc`/jest verdes) atendido.

## 8. Divergências entre o relatório e o código real

Nenhuma. O EXECUCAO descreve fielmente o diff: 6 hooks migrados, constante de
config, `refetch()` nos botões, `isFetching` no lugar de `isPending`, teste de
cache. Verificado contra `git diff 9ba0366..32517df`.
