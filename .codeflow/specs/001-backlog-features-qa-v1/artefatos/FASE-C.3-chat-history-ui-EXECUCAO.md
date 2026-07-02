---
spec: 001-backlog-features-qa-v1
fase: C.3
slug_fase: chat-history-ui
status: executado
tentativa: 1
reprovacoes: 0
sha_inicial: 5ce117f92eedef206260ba8a42ab5596c339ea36
sha_final: 7a2e60d517871bca9d49c088786626e9d931cdd0
range: 5ce117f92eedef206260ba8a42ab5596c339ea36..7a2e60d517871bca9d49c088786626e9d931cdd0
---

# FASE C.3 — Relatório de execução

## 1. Resumo do que foi feito

O chat "Pergunte à IA" passou a **exibir o histórico persistido** ao abrir a
página, em vez de manter um estado local que sumia ao navegar. Foi criado o hook
`useChatHistory` (`useQuery` em `GET /ai/conversations`, carrega no mount por ser
leitura sem custo de IA) e a UI passou a renderizar as mensagens do backend
(`{role,content}`). `useAskQuestion` invalida `["ai","conversations"]` ao concluir,
recarregando o histórico após cada pergunta (que o backend já persiste — C.2).

## 2. Arquivos CRIADOS

| Arquivo | Propósito |
|---------|-----------|
| — | Nenhum (apenas alterações). |

## 3. Arquivos ALTERADOS

| Arquivo | O que mudou |
|---------|-------------|
| `frontend/types/index.ts` | Novos `ChatMessage {role,content,timestamp}` e `ConversationResponse {channel,messages}` (espelham o schema do backend). |
| `frontend/lib/hooks/useAI.ts` | Novo `useChatHistory` (`useQuery` GET `/ai/conversations`, `staleTime:60s`). `useAskQuestion` ganha `useQueryClient` + `onSuccess` que invalida `["ai","conversations"]`. |
| `frontend/app/(dashboard)/insights/page.tsx` | Remove o estado local `chatHistory`/`setChatHistory`; usa `useChatHistory()`; renderiza as mensagens persistidas por `role` (user à direita, model à esquerda com `MarkdownLite`); `handleAsk` só dispara a mutação (a invalidação recarrega). |

## 4. Confirmação do REUSO e decisões de design

- **Reuso confirmado:** `MarkdownLite` reusado para o texto do modelo; padrão
  `useQuery` do projeto; endpoint `GET /ai/conversations` da C.2. Layout das bolhas
  de chat (glass/neu) reaproveitado do render anterior.
- **Decisão — `useChatHistory` carrega no mount:** ao contrário dos insights (C.1,
  opt-in para não queimar quota Groq), listar o histórico é **só leitura no banco**,
  sem chamar a IA — logo carrega no mount para satisfazer AC-C3 ("reabro e as
  mensagens aparecem"). Sem risco de custo.
- **Decisão — invalidação em vez de estado otimista:** como o backend já persiste o
  par (C.2), invalidar `["ai","conversations"]` no `onSuccess` recarrega a verdade
  do servidor. Remove a duplicação com o estado local (que era a causa do "some ao
  navegar"). Durante o envio, o bloco `askQuestion.isPending` mantém o feedback.
- **Nenhum desvio da spec.**

## 5. Comandos rodados + saídas reais

```text
# type-check
$ npx tsc --noEmit
TSC_EXIT:0   (limpo)

# lint
$ npx next lint --no-cache
./components/auth/Plasma.tsx 156:26 Warning react-hooks/exhaustive-deps
  (PRÉ-EXISTENTE, arquivo não tocado nesta fase) — 0 erros

# testes da fase
$ npx jest __tests__/lib/hooks/useAI.test.ts
Test Suites: 1 passed, 1 total
Tests:       12 passed, 12 total
#  ✓ useChatHistory carrega o histórico no mount (AC-C3)
#  ✓ useAskQuestion invalida ['ai','conversations'] ao concluir

# suíte frontend completa (regressão)
$ npx jest
Test Suites: 2 failed, 11 passed, 13 total
Tests:       3 failed, 81 passed, 84 total
# As 3 falhas são MacroPieChart/MacroCards — PRÉ-QUEBRADAS e FORA DE ESCOPO
# (declaradas na spec). Não são regressão desta fase.

# grep de segredo/PII no diff (esperado: 0)
$ git diff 5ce117f..HEAD | grep -iE "api_key|secret|password|token=" | wc -l
0
```

## 6. Critérios de aceite da fase (com evidência)

- [x] **AC-C3 (FR-C4)** — *histórico existente; reabro a tela do chat; mensagens
  anteriores aparecem.* Evidência: `useChatHistory` faz `GET /ai/conversations` no
  **mount** (teste "carrega o histórico ... no mount (AC-C3)": `isSuccess`, `data`
  com 2 mensagens); a página renderiza `chatHistory.data.messages` por `role`.
  Combinado à C.2 (persistência real, testada em integração), reabrir a página
  recarrega e exibe o histórico.
- [x] **FR-C4 (atualização após enviar)** — evidência: teste "useAskQuestion invalida
  ['ai','conversations']" — `invalidateQueries` chamado com a queryKey do histórico
  no `onSuccess`, disparando o refetch que traz o par recém-persistido.

## 7. Definition of Done da fase

- [x] Testes da fase verdes (12/12 em `useAI.test.ts`, incl. os 2 de C.3).
- [x] `lint`/`tsc`/`jest` limpos nos arquivos tocados (falhas pré-quebradas fora de
      escopo documentadas).
- [x] Escopo travado: não expõe chave de IA (só consome o endpoint do backend);
      segue glass/neu (reusa o layout existente); sem tocar backend.
- [x] Nenhum segredo/PII em log/DTO.
- [x] Commits em pt-BR (Conventional Commits), sem menção a autor/IA.

## 8. (Em rework) O que mudou nesta tentativa

N/A — primeira execução.

## 9. Itens em aberto / dúvidas para o avaliador

- **E2E manual não executado** (o app exige login): a cobertura de AC-C3 é o teste
  de hook (mount + refetch) + o teste de integração de C.2 (persistência real). Um
  smoke E2E logado (perguntar → navegar → voltar → ver histórico) seria a prova
  final de ponta a ponta, se desejado.
- **`timestamp` não é exibido** na UI (só `role`/`content`), coerente com o layout de
  chat anterior; o campo existe no tipo caso se queira exibir depois.
- **Falha pré-existente do Track A** (`test_celery_tasks.py::TestRecalculateTdee`)
  segue vermelha e independe de C — ver §9 do relatório de C.2. Deixa `make check`
  (que roda `test-unit`) vermelho por causa de A, não de C.
