---
spec: 001-backlog-features-qa-v1
fase: B.3
slug_fase: hydration-ui-list
tentativa: 1
veredito: APROVADO
score: 9.5
threshold: 8.5
range_avaliado: 5287aa44f0cc826fcfa624c4dab54d90975cacc3..fa902e5549d9a1018c4c08df527cc438261505a2
---

# FASE B.3 — Avaliação independente

## 1. Veredito e score

**Veredito:** APROVADO · **Score:** 9.5 / threshold 8.5

O card "Registros de hoje" lista os `entries` do dia (já vindos de `useHydrationToday`,
sem nova query) com remover e edição inline de `amount_ml`; os hooks
`useDeleteHydration`/`useUpdateHydration` são cópia fiel do padrão `useLogHydration`
(mutation + `invalidateQueries(["hydration"])` + `["dashboard"]` + toast). A correção de
tipo `entries_count` → `entries` alinha o front ao contrato real do backend e é segura
(grep confirma **zero** referências remanescentes a `entries_count`). `tsc`, `lint` e o
jest da fase passam; as 2 suítes vermelhas (`MacroCards`/`MacroPieChart`) são pré-quebradas,
intocadas por B.3 e explicitamente fora de escopo — verifiquei que a falha é de
text-matching de macros, sem relação com hidratação. Sem BLOQUEANTES nem IMPORTANTES;
duas sugestões para robustecer o teste.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 4.5 | `hidratacao/page.tsx:206-306` card lista `entries` com remover/editar; AC-B4 coberto a nível de hook (spec permite "hook OU render"). Escopo travado: gráfico de histórico intocado, sem foto, glass/neu mantido. −0.5: a atualização do total (parte do AC-B4) não é **asserida** no teste, só garantida pela invalidação literal em `onSuccess`. |
| 2 | Arquitetura e direção de dependências | 3 | 5.0 | Hooks em `useLogs.ts:72-108` espelham `useLogHydration`; página consome query existente; tipo alinhado ao backend. Sem lógica de dados na página além de estado local de edição. |
| 3 | Segurança / multi-tenant | 3 | 5.0 | Sem segredo/PII no diff. Posse garantida no servidor (B.2). A UI valida `ml > 0` antes do PUT (`page.tsx:66-71`), então **não** dispara o caminho `null`→500 achado em B.2. |
| 4 | Reusar/espelhar, não duplicar | 3 | 5.0 | `invalidateQueries`+`toast` idênticos a `useLogHydration`; reusa `Card`/`Button`/`Input` do DS e ícones `lucide-react`; nenhuma query nova (consome `entries`). |
| 5 | Padrões de domínio/aplicação | 2 | 5.0 | React Query mutation por domínio, invalidação de chaves estáveis, toast pt-BR — padrão do arquivo. |
| 6 | Local e nomes dos arquivos | 2 | 5.0 | Exatamente `useLogs.ts`, `hidratacao/page.tsx`, `types/index.ts`, `__tests__/lib/hooks/useLogs.test.ts` (§5). |
| 7 | Qualidade de código | 2 | 5.0 | `tsc --noEmit` exit 0; `npm run lint` só o warning pré-existente em `Plasma.tsx`. Edição inline clara (`editingId`/`editValue`), botões desabilitados em `isPending`. |
| 8 | Testes e cobertura | 2 | 3.5 | 2 testes de hook: DELETE (URL correta + toast) e PUT (corpo **sem** `id` + toast). Lacunas: nenhum teste do ramo de **erro** (`onError`) e nenhuma asserção de que `invalidateQueries` disparou — que é o cerne comportamental do AC-B4. Ver Sugestões. |
| 9 | Migration safety (se aplicável) | 2 | [—] | Fase é só frontend — sem schema. |

Média ponderada (excluída a dim. 9): (3·4.5 + 3·5 + 3·5 + 3·5 + 2·5 + 2·5 + 2·5 + 2·3.5) / 20 = 95.5/100 → **9.5/10**.

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

Nenhum. (A cobertura de AC-B4 é de hook — permitido pela spec — e a atualização de
lista/total é entregue por invalidação literal e padrão, idêntica ao `useLogHydration` já
em produção. É gap de robustez de teste, não defeito de comportamento; fica como sugestão.)

## 5. Sugestões

- **Asserir a invalidação (fecha o AC-B4 de fato).** Em `useLogs.test.ts`, espionar
  `queryClient.invalidateQueries` e afirmar que `["hydration"]` e `["dashboard"]` são
  invalidadas no `onSuccess` de delete/update — é isso que prova "a lista e o total
  atualizam sem reload", hoje garantido só por inspeção de código.
- **Cobrir o ramo de erro.** A spec pedia "remoção … /erro"; o `onError:
  toast.error(...)` (`useLogs.ts:83,106`) não tem teste. Um caso com `api.delete`
  rejeitando fecharia a lacuna.
- **UX (menor):** `saveEdit` (`page.tsx:66-71`) faz `return` silencioso para valor ≤ 0
  ou vazio, sem feedback; e o input de edição não espelha o teto `le=5000` do backend
  (um valor grande retorna 422 → toast de erro genérico). Nenhum bloqueia; melhora o
  polimento. Remover não pede confirmação — aceitável para o domínio (log trivial de
  re-adicionar), mas um `confirm`/undo seria mais seguro.

## 6. Comandos rodados + saídas reais

Rodados por mim na ponta de `dev` (HEAD `4114201`; `fa902e5` confirmado ancestral),
no container `caloria_frontend`.

```text
$ git merge-base --is-ancestor fa902e5 HEAD ; echo $?
0

# Type-check
$ docker exec caloria_frontend npx tsc --noEmit   → exit 0

# Lint
$ docker exec caloria_frontend npm run lint
  → só Warning pré-existente em components/auth/Plasma.tsx (react-hooks/exhaustive-deps);
    nada nos arquivos de B.3.

# Jest da fase
$ npx jest __tests__/lib/hooks/useLogs.test.ts
  Test Suites: 1 passed, 1 total
  Tests:       13 passed, 13 total  (inclui useDeleteHydration + useUpdateHydration)

# Correção de tipo — nenhuma referência órfã a entries_count
$ grep -rn "entries_count" frontend --include=*.ts --include=*.tsx   → (nenhuma)

# Suítes vermelhas: pré-quebradas e fora de escopo (não regressão de B.3)
$ npx jest __tests__/components/dashboard/MacroCards.test.tsx MacroPieChart.test.tsx
  ● MacroPieChart › Unable to find text "Sem dados hoje"
  ● MacroCards › Unable to find text "/2000 kcal/"   (x2)
$ git diff 5287aa4..fa902e5 --stat -- '*Macro*'   → (vazio: B.3 não tocou esses arquivos)

$ git status --porcelain   → (vazio)
```

**Revisão de UI (estática, a partir do diff — o fluxo autenticado não foi dirigido aqui;
mesma limitação que o executor declarou no item 9):**
- **Acessibilidade:** todo botão-ícone tem nome acessível (`aria-label`: Remover/Editar
  registro, Salvar, Cancelar, Editar quantidade em ml); usa `<button>`/`<ul>/<li>`/`<Input>`
  reais; estados por texto+`disabled` (não só cor); erro via toast textual. Sem armadilha
  de foco (edição inline, não modal). Nenhuma violação bloqueante.
- **Consistência visual:** espaçamentos/tamanhos na escala Tailwind (`py-2.5`, `gap-1/2`,
  `h-8 w-8`); cores por token semântico (`text-muted-foreground`, `divide-border`,
  acento `blue-500` da hidratação; `green/red-500` como affordance de salvar/remover);
  card espelha o hover glass/neu dos cards irmãos da página. Sem hex solto.
- **avoid-ai-look:** reusa o idioma visual já existente da página (não é template
  genérico); o "ícone em quadradinho arredondado" (`rounded-lg bg-blue-500/10` no Droplets)
  é o mesmo padrão já usado na página — escolha coerente com o contexto, não default solto.

Árvore de trabalho intacta ao final; nenhuma alteração de código feita pelo avaliador.

## 7. Itens da fase / DoD não atendidos

Nenhum bloqueante. O critério de conclusão de B.3 (§5: "`npm run lint`/`tsc`/jest verdes;
remoção/edição refletem no total do dia") está cumprido: as verdes são reais e a reflexão
no total é entregue pela invalidação de `["hydration"]`+`["dashboard"]`. As sugestões da §5
apenas robustecem a evidência de teste do AC-B4; não são pendências de comportamento.

## 8. Divergências entre o relatório e o código real

Nenhuma divergência material — o relatório descreve fielmente o card, os hooks, a correção
de tipo e as limitações (cobertura de hook, sem E2E autenticado, sem teste de render). Dois
pontos de transparência confirmados por mim: (a) `entries_count` era de fato órfão (grep = 0
usos), então a troca por `entries` não quebra consumidor algum; (b) as suítes vermelhas
`MacroCards`/`MacroPieChart` são pré-existentes e não tocadas por B.3, como declarado.
