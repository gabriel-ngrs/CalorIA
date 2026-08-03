---
spec: 002-vitrine-eval-e-saneamento
fase: D.6
slug_fase: polimento-ui
status: rework
tentativa: 2
reprovacoes: 1
sha_inicial: 40e2941
sha_final: 2e6cd1d1d2a7c060d34fda9137c7aa0b25e52a6f
range: 40e2941..2e6cd1d1d2a7c060d34fda9137c7aa0b25e52a6f
---

# FASE D.6 — Relatório de execução

## Tentativa 2 — o que mudou

Veredito da tentativa 1: **RESSALVAS**, score 9.5. Um achado IMPORTANTE, fechado.

### D6-IMP-1 — o teste de toast único não foi escrito

**Aceito.** A explicação da tentativa 1 era verdadeira (o `toast.success` duplicado
saiu de `humor/page.tsx` junto com o import, e verificar remoção por leitura de diff é
razoável), mas o item de teste estava declarado nominalmente na fase e não foi
entregue. A consequência que a avaliação aponta é concreta: nada impedia reintroduzir
o `toast.success` na página, e o defeito voltaria em silêncio porque o hook continua
emitindo o seu.

Adotada a **opção 1**, que a avaliação chama de mais barata: teste sobre o hook, com
React Query e `sonner` mockado — sem montar a página.

`frontend/__tests__/lib/hooks/useLogs.test.ts`, novo bloco `toast único por registro`:

| teste | o que trava |
|---|---|
| `useLogMood emite exatamente um toast de sucesso` | o par página/hook do defeito original |
| `useLogWeight emite exatamente um toast de sucesso` | mesmo padrão em peso |
| `useLogHydration emite exatamente um toast de sucesso` | mesmo padrão em hidratação |
| `a falha emite só o toast de erro, e nenhum de sucesso` | o `onError` não duplica nem vaza sucesso |

Os três primeiros cobrem a sugestão da §5 da avaliação — verificar se o mesmo padrão
existe em outros pares página/hook. A afirmação passa a ser sobre **contagem**
(`toHaveBeenCalledTimes(1)`), que é o que o defeito violava; os testes que já existiam
afirmavam só o conteúdo da mensagem, e passariam com dois toasts.

### Evidência

```text
$ cd frontend && npm test
Test Suites: 20 passed, 20 total
Tests:       118 passed, 118 total        # eram 114
Time:        4.436 s

$ npx tsc --noEmit    → EXIT=0
$ npm run lint        → só o warning pré-existente de Plasma.tsx:156
```

### Sobre as sugestões da §5

Não implementadas, e de propósito: o teste de frame do FOUC a própria avaliação
recomenda **não** fazer; remover o `next-themes` órfão é poda, que tem fase própria
(D.4); e o comentário em `dev-log.ts` sobre eliminação de código morto pelo bundler é
melhoria de documentação fora do achado. Nenhuma delas é item de gate.


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

- [x] **AC-23, tema escuro sem flash** — verificado no **HTML pré-renderizado**
      do build de produção, não só por leitura do fonte:

      ```text
      $ python -c "..."   # sobre .next/server/app/login.html
      posicao do script anti-FOUC: 3824
      posicao de <body>:           4015
      script roda ANTES do body:   True

      ...<meta name="next-size-adjust"/><script>try{var t=localStorage
      .getItem("caloria-theme");if(t==="dark"){document.documentElement
      .classList.add("dark")}}catch(e){}</script>...
      ```

      O script está no `<head>`, antes de qualquer conteúdo do `<body>`, então
      a classe `dark` é aplicada antes do primeiro paint. Não há teste de
      **frame** (isso exigiria Playwright com captura visual, fora do escopo),
      mas a condição estrutural que causa o FOUC deixou de existir e isso está
      medido no artefato de build.
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

1. **Toast único** continua sem teste automatizado — exigiria montar a página de
   humor inteira com React Query e sonner. O FOUC, esse sim, ficou verificado no
   HTML de build (§6). Aceitável, ou vale abrir uma fase de testes E2E?
2. O `theme-provider` foi mantido em vez de migrar para `next-themes`, que
   segue instalado e não usado. Remover a dependência órfã numa fase futura?
