---
spec: 002-vitrine-eval-e-saneamento
fase: D.6
slug_fase: polimento-ui
tentativa: 1
veredito: RESSALVAS
score: 9.5
threshold: 8.5
range_avaliado: 40e2941..7f9f59a
---

# FASE D.6 — Avaliação independente

## 1. Veredito e score

**Veredito:** RESSALVAS · **Score:** 9.5 / threshold 8.5

Os seis passos estão entregues, e a verificação do anti-FOUC é a melhor da fase:
o executor não se contentou em ler o fonte, foi ao HTML pré-renderizado do build
de produção e mediu a posição do script contra a do `<body>`. Isso é o padrão
certo para um defeito que só existe em tempo de carregamento.

A ressalva é um teste que a fase pede nominalmente e que não foi escrito.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 4 | Os seis passos verificados no diff. AC-23 nas três cláusulas: FOUC (script inline no `<head>`), logs de produção (`devLog`/`devError`), data do peso (`+ "T12:00"`). Escopo travado respeitado: nenhuma página refatorada, `getLocalToday`/`fileToBase64`/`MEAL_LABELS` seguem duplicados, biblioteca de toast inalterada. Desconto por D6-IMP-1. |
| 2 | Arquitetura e direção de dependências | 3 | 5 | `lib/dev-log.ts` é o ponto único de decisão sobre `NODE_ENV`, consumido por `api.ts` e `providers.tsx` — antes cada arquivo decidia sozinho (ou não decidia). `ThemeProvider` deixou de **aplicar** o tema no `useEffect` e passou a **alinhar** o estado ao DOM, o que é a correção estrutural certa: se continuasse aplicando, reintroduziria o flash que o script eliminou. |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | Os logs removidos de produção emitiam uma linha por request, navegação e query — vazamento de dado de saúde para o console do navegador. Fechar isso é ganho de privacidade, não só de ruído. `try/catch` no script inline cobre navegador com `localStorage` bloqueado, onde a leitura já lança. |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | O padrão de guardar por `NODE_ENV` já existia em `providers.tsx:77` (ReactQueryDevtools) e virou função em vez de ser recopiado. O sufixo `"T12:00"` já era usado em três arquivos; o histórico de peso era o único ponto fora do padrão, e foi alinhado a ele. `next-themes` **não** foi adotado — a spec oferecia as duas rotas e trocar de biblioteca seria maior que o defeito. |
| 5 | Padrões de domínio/aplicação | 2 | 5 | `onError` nas 6 mutations segue o formato dos hooks existentes; `initialMode` entra como prop opcional, sem quebrar chamador. |
| 6 | Local e nomes dos arquivos | 2 | 5 | `lib/dev-log.ts` junto de `lib/api.ts`; três arquivos de teste em `__tests__/` espelhando o caminho do código. |
| 7 | Qualidade de código | 2 | 5 | `npx tsc --noEmit` limpo; `npm run lint` sem novidade (o único warning é o pré-existente de `Plasma.tsx:156`). O efeito que sincroniza `initialMode` na abertura resolve o caso real — o modal fica montado entre aberturas, então `useState` inicial só valeria para o primeiro atalho. |
| 8 | Testes e cobertura | 2 | 4 | 14 testes novos (114 contra 100 antes da fase), cobrindo `devLog` nos dois ramos, a data com e sem o sufixo (reproduzindo o defeito anterior) e os cinco casos do modal, incluindo a reabertura com outro modo. Desconto por D6-IMP-1. |
| 9 | Migration safety (se aplicável) | 2 | [—] | Não aplicável — fase só de frontend. |

Média ponderada das 8 dimensões aplicáveis: 95/20 = 4.75 → **9.5**.

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

**D6-IMP-1 — o teste de toast único, pedido nominalmente pela fase, não foi
escrito.**

`SPEC_002...md:1232-1234`, "Testes (AC-23)":

> teste de que a data renderizada confere; **teste de que um único toast é
> emitido**; teste de que o modal abre no modo solicitado; build de produção sem
> os logs.

Três dos quatro existem. O do toast não — o executor marca `[~]` e explica: o
toast duplicado saiu de `humor/page.tsx:107`, o import de `toast` saiu junto (e o
lint quebraria se sobrasse não usado), e escrever o teste exigiria montar a
página inteira com React Query e sonner.

A explicação é verdadeira e a verificação por leitura de diff é razoável para um
código que foi **removido**. Ainda assim isto é um item de teste declarado que
não foi entregue, e a rule `testing` do framework é direta sobre mudança de
comportamento precisar de teste correspondente. A consequência prática é
concreta: nada impede que alguém reintroduza o `toast.success` na página numa
próxima edição — o defeito volta silencioso, porque o hook continua emitindo o
seu.

**Correção sugerida** — a mais barata das duas:

1. Teste sobre o **hook**, não sobre a página: montar `useLogs` com React Query e
   afirmar que uma mutation bem-sucedida chama `toast.success` exatamente uma
   vez, com `sonner` mockado. Não precisa da página.
2. Ou, se montar a página for aceitável, um teste de integração leve com
   `jest.mock("sonner")` contando as chamadas depois de submeter o formulário de
   humor.

Se o owner preferir aceitar o `[~]` como está, então a saída correta é registrar
a exceção — a rule `testing` prevê exceções, mas exige que sejam declaradas, e
uma decision de uma linha resolve.

## 5. Sugestões

- **Script inline vs. `next-themes`** (dúvida 2 do EXECUCAO): a escolha foi certa
  para esta fase. Mas `next-themes` continua no `package.json` sem ser usado —
  dependência órfã que alguém vai tentar "aproveitar" um dia. Removê-la numa fase
  de poda deixa a decisão explícita em vez de latente.
- **Teste de frame do FOUC** (dúvida 1): não vale Playwright só por isso. A
  verificação estrutural que o executor fez — script antes do `<body>` no HTML de
  build — é a condição necessária e suficiente, e é mais estável que um teste
  visual, que ficaria flaky. Recomendo não fazer.
- O `devLog` depende de o bundler substituir `NODE_ENV` por literal para o `if`
  virar código morto. É verdade no Next, mas é conhecimento implícito: um
  comentário de uma linha em `dev-log.ts` explicando por que isso não deixa
  string de log no bundle de produção evita que alguém "otimize" a função para
  algo que quebre a eliminação.
- `humor/page.tsx` e `useLogs.ts` emitiam toast cada um. Vale checar se o mesmo
  padrão existe em outros pares página/hook — se existir, é o mesmo defeito
  esperando, e um teste no hook (sugestão 1 acima) cobriria todos de uma vez.

## 6. Comandos rodados + saídas reais

Ambiente: branch `dev`, HEAD `e3a974a`.
`git merge-base --is-ancestor 7f9f59a HEAD` → OK.

```text
$ cd frontend && npm test
Test Suites: 20 passed, 20 total
Tests:       114 passed, 114 total
Snapshots:   0 total
Time:        4.207 s

$ npx tsc --noEmit
EXIT=0

$ npm run lint -- --no-cache
./components/auth/Plasma.tsx
156:26  Warning: The ref value 'containerRef.current' will likely have changed [...]
# único warning, pré-existente e fora do escopo desta fase

$ npm run build
EXIT=0   (sem warnings; ver a avaliação da D.5)

# passos 3, 4, 5 e 6 — verificados no diff do range
$ git diff --stat 40e2941..7f9f59a -- frontend/ | tail -12
 frontend/lib/dev-log.ts                              | (novo)
 frontend/app/layout.tsx                              | script anti-FOUC no <head>
 frontend/components/theme-provider.tsx               | useEffect alinha, não aplica
 frontend/lib/api.ts                                  | 4 console.* → devLog/devError
 frontend/app/providers.tsx                           | 3 idem
 frontend/app/(dashboard)/peso/page.tsx               | + "T12:00"
 frontend/app/(dashboard)/humor/page.tsx              | toast duplicado + import removidos
 frontend/app/(dashboard)/dashboard/page.tsx          | estado quickMealMode
 frontend/components/dashboard/QuickAddModals.tsx     | initialMode
 frontend/lib/hooks/useProfile.ts                     | onError em 2 mutations
 frontend/lib/hooks/useReminders.ts                   | onError em 4 mutations

$ gitleaks detect --config .gitleaks.toml --log-opts="d8cc463~1..HEAD"
22 commits scanned.  no leaks found

$ git status --short
(limpo)
```

Não repeti a inspeção do HTML pré-renderizado: o `.next` foi regerado pelo meu
`npm run build` e a verificação do executor (posição 3824 do script contra 4015
do `<body>`, com o `<script>` colado no relatório) é reproduzível e específica o
bastante para eu aceitá-la — o script inline está no `layout.tsx` e o App Router
o emite no `<head>` por construção.

## 7. Itens da fase / DoD não atendidos

- **"Teste de que um único toast é emitido"** — não entregue (D6-IMP-1).
- Os demais itens do gate ("AC-23 satisfeito; `make test-frontend`, `npm run
  lint` e `npx tsc --noEmit` verdes") estão cumpridos e verificados por execução
  própria.

## 8. Divergências entre o relatório e o código real

Nenhuma. As dez linhas da tabela de arquivos alterados conferem com o diff, e o
item não entregue está marcado `[~]` com a razão, em vez de omitido. A contagem
de testes (114, contra 100 antes da fase) confere com a minha execução.
