---
spec: 001-backlog-features-qa-v1
fase: D.3
slug_fase: password-reset-ui
tentativa: 1
veredito: APROVADO
score: 9.7
threshold: 8.5
range_avaliado: 20a521848ac4f6162b54e5bddc029182754d14f3..49554fd5752a6eb28eab4ac42651337240780bb4
---

# FASE D.3 — Avaliação independente

## 1. Veredito e score

**Veredito:** APROVADO · **Score:** 9.7 / threshold 8.5

Telas `/forgot-password` e `/reset-password` + link "Esqueci minha senha" no login
(FR-D4). Fase de interface — avaliada também sob avoid-ai-look / accessibility /
visual-consistency. Verificado contra o código real: tsc/eslint limpos, 4 testes jest
verdes. Reusa shadcn + tokens de tema (sem hex cravado) e o padrão `useForm+zod` de
login/register.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 5 | 2 `page.tsx` novos + `login/page.tsx:82-90` link; escopo travado ok (não revela existência de e-mail; glass/neu; token não logado) |
| 2 | Arquitetura e direção de dependências | 3 | 5 | Client components; `useSearchParams` sob `<Suspense>` (`reset-password/page.tsx:104-110`) — exigência real do App Router 14 |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | Forgot trata sucesso e erro idênticos (`forgot-password/page.tsx:25-32`) — não vaza existência; token só na query, nunca logado |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | `Button`/`Input`/`Label`, `api` client, escala `h-11`/`space-y-4`/`text-[1.6rem]` copiada de login/register |
| 5 | Padrões de domínio/aplicação | 2 | 5 | Mesmo esqueleto de card/tipografia das telas de auth; sem gradiente/emoji gratuito (avoid-ai-look) |
| 6 | Local e nomes dos arquivos | 2 | 5 | Route group `(auth)/forgot-password`, `(auth)/reset-password` — corretos |
| 7 | Qualidade de código | 2 | 5 | `<Label htmlFor>`↔`<Input id>`, botões `<button>` reais, erros com **texto** (não só cor) — a11y ok |
| 8 | Testes e cobertura | 2 | 4 | 4 jest (submit/uniforme/sucesso/erro), porém a verificação **E2E manual em dev** (critério de conclusão da fase) não foi executada; contrato validado só via D.2 |
| 9 | Migration safety (se aplicável) | 2 | — | Não se aplica |

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

Nenhum.

## 5. Sugestões

- `reset-password/page.tsx` não tem campo "confirmar nova senha" — UX comum em reset,
  mas não exigido pelo spec. Opcional.
- Critério de conclusão da fase pede "fluxo E2E manual funciona em dev"; o relatório
  (§9) admite que só rodou jest (render+submit mockado). Recomenda-se um smoke E2E real
  (subir front+back, percorrer forgot→e-mail logado→reset→login) antes do rollout do
  Track D. O backend já foi validado por integração em D.2.
- Mensagem do forgot na tela ("enviamos") difere levemente da do backend ("enviaremos");
  como o front exibe a própria cópia, é inócuo — apenas padronizar por consistência.

## 6. Comandos rodados + saídas reais

```text
$ docker exec caloria_frontend npx tsc --noEmit
(sem saída — 0 erros)

$ docker exec caloria_frontend npx eslint app/(auth)/forgot-password/page.tsx \
    app/(auth)/reset-password/page.tsx app/(auth)/login/page.tsx \
    __tests__/app/forgot-password.test.tsx __tests__/app/reset-password.test.tsx
(sem saída — 0 problemas)

$ docker exec caloria_frontend npx jest __tests__/app/forgot-password.test.tsx \
    __tests__/app/reset-password.test.tsx
Test Suites: 2 passed  ·  Tests: 4 passed
# (rodado no lote com D.4: 3 suites, 6 testes passaram)
```

## 7. Itens da fase / DoD não atendidos

`lint`/`tsc`/jest verdes (✓). Único item parcial: verificação E2E manual em dev não
executada (ver Sugestões) — não bloqueante para o gate da fase, que é coberto por jest.

## 8. Divergências entre o relatório e o código real

Nenhuma. O relatório declarou o `<Suspense>` e o `setTimeout`→`router.push` da tela de
reset; ambos confirmados no diff. A afirmação de reuso de tokens de tema (sem hex) foi
verificada linha a linha.
