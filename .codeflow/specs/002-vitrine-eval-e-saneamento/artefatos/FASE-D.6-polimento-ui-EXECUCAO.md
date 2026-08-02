---
spec: 002-vitrine-eval-e-saneamento
fase: D.6
slug_fase: polimento-ui
status: executado
tentativa: 1
reprovacoes: 0
sha_inicial: 40e2941
sha_final: 7f9f59a
range: 40e2941..7f9f59a
---

# FASE D.6 — Relatório de execução

> **Nota de commit.** D.5 e D.6 compartilham o commit `7f9f59a` — ver a nota no
> relatório da D.5.

## 1. Resumo do que foi feito

Os seis passos da fase, todos entregues.

## 2. Arquivos CRIADOS

| Arquivo | Propósito |
|---------|-----------|
| `frontend/lib/dev-log.ts` | `devLog`/`devError`, ativos só em desenvolvimento. |
| `frontend/__tests__/lib/devLog.test.ts` | 5 testes. |
| `frontend/__tests__/app/data-local.test.ts` | 4 testes da data `date-only`. |
| `frontend/__tests__/components/dashboard/QuickMealModal.test.tsx` | 5 testes do modo inicial do modal. |

## 3. Arquivos ALTERADOS

| Arquivo | O que mudou |
|---------|-------------|
| `frontend/app/layout.tsx` | Script inline blocante que aplica o tema salvo antes do primeiro paint. |
| `frontend/components/theme-provider.tsx` | O `useEffect` passa a **alinhar** o estado ao DOM, em vez de reaplicar o tema. |
| `frontend/lib/api.ts` | 4 `console.log`/`console.error` → `devLog`/`devError`. |
| `frontend/app/providers.tsx` | 3 idem (NavTimer e QueryCache). |
| `frontend/app/(dashboard)/peso/page.tsx` | Data do histórico ganha o sufixo `"T12:00"`. |
| `frontend/app/(dashboard)/humor/page.tsx` | Toast duplicado removido (o hook já emite); import de `toast` removido. |
| `frontend/app/(dashboard)/dashboard/page.tsx` | Estado `quickMealMode`; os três atalhos passam o modo. |
| `frontend/components/dashboard/QuickAddModals.tsx` | `initialMode` na prop; efeito que sincroniza a cada abertura. |
| `frontend/lib/hooks/useProfile.ts` | `onError` em 2 mutations. |
| `frontend/lib/hooks/useReminders.ts` | `onError` em 4 mutations. |

## 4. Confirmação do REUSO e decisões de design

**REUSADO:** o padrão de guardar por `NODE_ENV` já existia em
`providers.tsx:77` (ReactQueryDevtools) — virou uma função. O sufixo `"T12:00"`
já era usado em `humor/page.tsx`, `relatorios/page.tsx` e no próprio
`peso/page.tsx:57`; o histórico era o único ponto que não usava.
`next-themes` **não** foi adotado.

**Decisões de design:**
- **Script inline, não `next-themes`.** A spec oferecia as duas rotas. O script
  inline resolve o FOUC sem trocar a API `useTheme()` que os componentes já
  consomem — trocar de biblioteca seria refatoração maior do que o defeito.
  O `try/catch` cobre navegador com `localStorage` bloqueado, onde ler já lança.
- **`ThemeProvider` deixou de reaplicar o tema no `useEffect`.** Se continuasse
  aplicando depois da hidratação, reintroduziria o flash que o script eliminou;
  agora ele só alinha o estado React ao que o DOM já tem.
- **`initialMode` sincronizado por efeito na abertura.** O modal permanece
  montado entre aberturas, então o valor inicial de `useState` só valeria para o
  primeiro atalho clicado. Há teste que reabre com outro modo.
- **`devLog`/`devError` eliminados no build de produção**, porque `NODE_ENV` é
  substituído por literal e o `if` vira código morto para o bundler.

**Escopo travado respeitado:** nenhuma página foi refatorada; as duplicações
conhecidas (`getLocalToday`, `fileToBase64`, `MEAL_LABELS`) continuam onde
estavam; a biblioteca de toast não mudou.

## 5. Comandos rodados + saídas reais

```text
$ npm run lint
(apenas o warning pré-existente de components/auth/Plasma.tsx:156)

$ npx tsc --noEmit
EXIT=0

$ npm test
Test Suites: 20 passed, 20 total
Tests:       114 passed, 114 total  (era 100 antes da fase)

$ npm test -- __tests__/components/dashboard/QuickMealModal.test.tsx
  ✓ initialMode=text abre em Texto
  ✓ initialMode=photo abre em Foto
  ✓ initialMode=audio abre em Áudio
  ✓ sem initialMode o padrão continua sendo texto
  ✓ reabrir com outro modo troca o modo exibido
```

## 6. Checklist dos ACs / critério de conclusão

- [x] **AC-23, tema escuro sem flash** — script blocante em `<head>`. Coberto por
      inspeção de código, não por teste automatizado: o FOUC é um evento de
      pintura anterior à hidratação, que jsdom não observa. Um teste de verdade
      exigiria Playwright com captura de frame — fora do escopo desta fase.
- [x] **AC-23, build de produção sem os logs** — `TestDevLog` prova os dois
      ramos: em `production` nada é escrito, em `development` sim.
- [x] **AC-23, a data do histórico de peso confere com a data registrada** —
      `data-local.test.ts` prova a correção **e** reproduz o defeito anterior
      (sem o sufixo, `2026-08-02` renderizava `01/08/2026` em `America/Sao_Paulo`).
- [x] **Modal abre no modo solicitado** — 5 testes, incluindo a reabertura.
- [x] **`make test-frontend`, `npm run lint` e `npx tsc --noEmit` verdes.**
- [~] **Um único toast é emitido** — o toast duplicado foi removido e o import de
      `toast` saiu do arquivo (o lint quebraria se sobrasse não usado), mas
      **não há teste automatizado** para isso: exigiria montar a página de humor
      inteira com React Query e sonar. Verificado por leitura do diff.
- [x] **`onError` nos hooks de perfil e lembretes** — 6 mutations cobertas.

## 7. Dúvidas para o avaliador

1. Dois itens do AC-23 (ausência de FOUC e toast único) estão cobertos por
   inspeção de código, não por teste automatizado — os dois exigiriam
   infraestrutura de teste que a fase não prevê (Playwright para o frame,
   render completo de página para o toast). Aceitável, ou vale abrir uma fase
   de testes E2E?
2. O `theme-provider` foi mantido em vez de migrar para `next-themes`, que
   segue instalado e não usado. Remover a dependência órfã numa fase futura?
