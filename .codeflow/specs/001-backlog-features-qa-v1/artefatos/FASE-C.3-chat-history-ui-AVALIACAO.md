---
spec: 001-backlog-features-qa-v1
fase: C.3
slug_fase: chat-history-ui
tentativa: 1
veredito: APROVADO
score: 9.7
threshold: 8.5
range_avaliado: 5ce117f92eedef206260ba8a42ab5596c339ea36..7a2e60d517871bca9d49c088786626e9d931cdd0
---

# FASE C.3 — Avaliação independente

## 1. Veredito e score

**Veredito:** APROVADO · **Score:** 9.7 / threshold 8.5

`useChatHistory` (`useQuery` em `GET /ai/conversations`, carrega no mount por ser
só leitura) + UI renderizando o histórico persistido por `role` + invalidação de
`["ai","conversations"]` no `onSuccess` de `useAskQuestion`. Remove o estado local
`chatHistory` que era a causa do "some ao navegar" (B20 frontend). AC-C3/FR-C4
cobertos por teste; `tsc`/lint/jest verdes. Zero bloqueantes/importantes.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 5 | `useAI.ts:48-57` `useChatHistory` carrega no mount; `page.tsx:373-385` renderiza `messages` por `role` (user à direita, model com `MarkdownLite`); `useAskQuestion` invalida o histórico (`useAI.ts:71-73`). AC-C3 verde. Sem tocar backend. |
| 2 | Arquitetura e direção de dependências | 3 | 5 | Remove `useState chatHistory` e passa a ler a verdade do servidor (`page.tsx:80-88`); invalidação em vez de estado otimista — elimina a duplicação de estado. |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | Só consome `GET /ai/conversations` (autenticado no backend); não expõe chave de IA; nada sensível no diff. |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | Reusa `MarkdownLite`, o padrão `useQuery` e o layout glass/neu das bolhas de chat; `ChatMessage`/`ConversationResponse` (types) espelham o schema do backend (C.2). |
| 5 | Padrões de domínio/aplicação | 2 | 5 | `queryKey ["ai","conversations"]` consistente com a invalidação; `staleTime:60s` adequado p/ leitura barata. |
| 6 | Local e nomes dos arquivos | 2 | 5 | `useAI.ts`, `insights/page.tsx`, `types/index.ts` — os arquivos declarados na fase. |
| 7 | Qualidade de código | 2 | 5 | `handleAsk` simplificado (só dispara a mutação); render condicional por `role` legível. `tsc`/lint limpos. |
| 8 | Testes e cobertura | 2 | 5 | `useChatHistory carrega no mount (AC-C3)` + `useAskQuestion invalida ['ai','conversations']`; suíte `useAI.test.ts` 12/12 (rodada por mim). |
| 9 | Migration safety (se aplicável) | 2 | — | Não se aplica (fase só frontend). |

Média ponderada (dims 1–8, peso total 20) = 100/20 = 5.0 → **9.7/10** (desconto
simbólico pela sugestão de UX abaixo).

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

Nenhum.

## 5. Sugestões

1. **Janela sem feedback entre mutação e refetch** (`page.tsx`): ao enviar, a
   pergunta recém-feita só aparece depois que `invalidateQueries` recarrega
   `["ai","conversations"]`. O bloco `askQuestion.isPending` cobre a mutação, mas não
   o intervalo do refetch subsequente — pode haver um pequeno hiato até a mensagem
   surgir. Aceitável; um estado otimista opcional suavizaria.
2. **`key={i}` por índice** no `messages.map`: as mensagens são append-only e não
   reordenam, então o índice é estável na prática — sem defeito. Registrado apenas.
3. **Ordem do pipeline:** C.3 foi executada encadeada após C.2 no mesmo chat (o
   protocolo prevê 1 fase por vez, avaliada em chat zerado antes da seguinte). Não é
   defeito de código de C.3; a correção é de processo. C.2 foi avaliada APROVADA em
   separado, então a dependência está satisfeita.

## 6. Comandos rodados + saídas reais

```text
$ cd frontend && npx tsc --noEmit
TSC_EXIT=0   (limpo)

$ npx next lint --no-cache
./components/auth/Plasma.tsx 156:26 Warning react-hooks/exhaustive-deps
  (PRÉ-EXISTENTE, não tocado nesta fase)
LINT_EXIT=0   (0 erros)

$ npx jest __tests__/lib/hooks/useAI.test.ts
Test Suites: 1 passed, 1 total
Tests:       12 passed, 12 total
#  ✓ useChatHistory carrega o histórico ... no mount (AC-C3)
#  ✓ useAskQuestion invalida ['ai','conversations'] ao concluir

$ npx jest    (suíte completa — regressão)
Test Suites: 2 failed, 11 passed, 13 total
Tests:       3 failed, 81 passed, 84 total
# 3 falhas = MacroCards/MacroPieChart, PRÉ-QUEBRADAS e FORA DE ESCOPO. Não tocam
# arquivos de C.3.
```

## 7. Itens da fase / DoD não atendidos

Nenhum específico de C.3. Critério de conclusão (reabrir o chat mostra as
mensagens; `lint`/`tsc`/jest verdes) atendido. Nota transversal: `make check`
global segue vermelho por causa do Track A (`test_celery_tasks.py`), independente de
C — fora do escopo desta fase.

## 8. Divergências entre o relatório e o código real

Nenhuma. O EXECUCAO confere com `git diff 5ce117f..7a2e60d`: `useChatHistory`,
invalidação no `onSuccess`, remoção do `useState chatHistory`, render por `role`,
tipos espelhados. E2E manual logado não foi executado (o executor sinalizou) — a
cobertura combina o teste de hook (mount) com o teste de integração de C.2
(persistência real).
