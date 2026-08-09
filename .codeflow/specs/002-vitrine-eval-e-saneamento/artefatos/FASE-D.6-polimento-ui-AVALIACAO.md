---
spec: 002-vitrine-eval-e-saneamento
fase: D.6
slug_fase: polimento-ui
tentativa: 2
veredito: APROVADO
score: 9.7
threshold: 8.5
range_avaliado: 40e2941..2e6cd1d1d2a7c060d34fda9137c7aa0b25e52a6f
---

# FASE D.6 — Avaliação independente

## 1. Veredito e score

**Veredito:** APROVADO · **Score:** 9.7 / threshold 8.5

**O D6-IMP-1 está fechado, pela opção mais barata das duas, e com uma peça a mais.** O
teste é sobre o **hook**, com `sonner` mockado e sem montar a página — exatamente a
saída que eu havia sugerido. E a afirmação mudou de natureza: os testes que já existiam
verificavam o **conteúdo** da mensagem e passariam com dois toasts; os novos verificam a
**contagem** (`toHaveBeenCalledTimes(1)`), que é o que o defeito violava.

Quatro testes novos, e o quarto é o que eu não tinha pedido:

| teste | o que trava |
|---|---|
| `useLogMood emite exatamente um toast de sucesso` | o par página/hook do defeito original |
| `useLogWeight emite exatamente um toast de sucesso` | mesmo padrão em peso |
| `useLogHydration emite exatamente um toast de sucesso` | mesmo padrão em hidratação |
| `a falha emite só o toast de erro, e nenhum de sucesso` | o caso negativo |

Os três primeiros cobrem a sugestão da §5 da avaliação anterior — verificar se o mesmo
par página/hook existe em outros lugares. E `humor/page.tsx:106` ganhou um comentário
dizendo por que o toast **não** está ali, que é o que impede a reintrodução silenciosa
pelo próximo editor.

Revalidei os seis passos da fase no código, não no relatório, e os três itens do AC-23.
Todos conferem. Detalhe em §6.

**Nota de escopo desta avaliação:** a fase toca interface, e o protocolo prevê carregar
as skills de auditoria visual nesse caso. O delta da tentativa 2 é um arquivo de teste;
a substância visual foi avaliada na tentativa 1 e não mudou. Fiz a verificação
funcional dos seis passos e a leitura de acessibilidade dos pontos que a fase alterou
(§5), sem repetir a auditoria de design — declaro isso em vez de fingir cobertura que
não exerci.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 5 | Os seis passos verificados no código (§6). AC-23 nas três partes: sem flash claro (script inline blocante, `layout.tsx:15,73`), console limpo em produção (zero `console.` em `lib/api.ts` e `app/providers.tsx`), data correta (`peso/page.tsx:270` com `+ "T12:00"`). Os quatro testes declarados agora existem. Escopo travado respeitado: páginas não refatoradas, `getLocalToday`/`fileToBase64`/`MEAL_LABELS` seguem duplicados como manda o escopo, e a biblioteca de toast é a mesma |
| 2 | Arquitetura e direção de dependências | 3 | 5 | Teste no hook e não na página — a afirmação fica onde o comportamento mora, e não depende de montar React Query + página. O `ThemeProvider` foi ajustado para **não** reaplicar o tema no `useEffect` (`theme-provider.tsx:20-28`), só alinhar o estado ao DOM: reaplicar reintroduziria o flash que o script eliminou, e o comentário registra isso |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | Remover os logs de request/navegação/query do build de produção fecha um vazamento real: eram uma linha por request no console, com endpoint e atividade do usuário. O script inline tem `try/catch` para navegador com `localStorage` bloqueado, onde só **ler** já lança |
| 4 | Reusar/espelhar, não duplicar | 3 | 4 | O teste reusa o `createWrapper` e os mocks já presentes no arquivo, sem fixture nova. Desconto: o passo 2 apontava `providers.tsx:77` (`NODE_ENV === "development"`) como precedente a espelhar, e a implementação **removeu** os logs em vez de guardá-los — resultado mais forte para o AC, mas não é o padrão nomeado (§8) |
| 5 | Padrões de domínio/aplicação | 2 | 5 | `initialMode` com default `"text"` e `useState(initialMode)` + `if (open) setInputMode(initialMode)` (`QuickAddModals.tsx:134,149,173`) — o modal reabre no modo pedido, não fica preso ao primeiro |
| 6 | Local e nomes dos arquivos | 2 | 5 | Arquivos declarados na §5 mais o teste novo, no diretório que já abriga os testes de hook |
| 7 | Qualidade de código | 2 | 5 | Os comentários registram *por que*, nunca *o quê*: por que o `try` no script (`layout.tsx:14`), por que o `ThemeProvider` não reaplica (`:20-22`), por que o toast não está na página (`humor/page.tsx:106`). O último é o que fecha o buraco que o teste também fecha |
| 8 | Testes e cobertura | 2 | 5 | `useLogs.test.ts` → 17 passed (§6); suíte inteira 118/118, contra 114 antes. O caso negativo ("a falha emite só o toast de erro") cobre o modo pelo qual um `onError` mal escrito vazaria sucesso |
| 9 | Migration safety | 2 | [—] | Nenhuma migration tocada |

Score = (3·5 + 3·5 + 3·5 + 3·4 + 2·5 + 2·5 + 2·5 + 2·5) / 20 · 2 = 97/20 · 2 = **9.7**

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

Nenhum.

**D6-IMP-1 da tentativa 1 está fechado.** O achado era *"o teste de toast único, pedido
nominalmente pela fase, não foi escrito"*, com duas correções sugeridas. Foi adotada a
opção 1 (teste sobre o hook), estendida aos três pares página/hook e ao caso negativo:

```text
$ npx jest __tests__/lib/hooks/useLogs.test.ts
✓ useLogMood emite exatamente um toast de sucesso
✓ useLogWeight emite exatamente um toast de sucesso
✓ useLogHydration emite exatamente um toast de sucesso
✓ a falha emite só o toast de erro, e nenhum de sucesso
Tests: 17 passed, 17 total
```

## 5. Sugestões

- **O script anti-FOUC não consulta `prefers-color-scheme`.** Ele lê
  `caloria-theme` e aplica `dark` só se estiver salvo; visitante de primeira viagem com
  SO em modo escuro recebe a interface clara. Não é defeito contra o AC-23, que fala de
  "usuário com tema escuro **salvo**", e o default do produto é claro
  (`theme-provider.tsx:13,18`) — mas é a diferença entre "sem flash" e "no tema que a
  pessoa espera". Uma linha a mais no script (`||(!t&&matchMedia("(prefers-color-scheme:dark)").matches)`)
  resolveria, e é decisão de produto, não de engenharia.
- **`next-themes` continua no `package.json` sem uso.** O passo 1 o citava como
  alternativa e o caminho escolhido foi outro, melhor para o caso. Concordo com o
  relatório que remover é poda e tem fase própria (D.4) — registro para que a D.4 não o
  perca.
- **Leitura de acessibilidade dos pontos que a fase mexeu:** o `onError` acrescentado em
  `useProfile.ts` (2 ocorrências) e `useReminders.ts` (4) é ganho real — falha silenciosa
  é o pior caso para quem usa leitor de tela, porque não há nem pista visual a inferir.
  E o toast duplicado não era só ruído visual: dois anúncios do mesmo evento em região
  `aria-live` são lidos duas vezes. A correção melhora as duas coisas, mesmo sem ter
  sido motivada por acessibilidade.

## 6. Comandos rodados + saídas reais

> Gates compartilhados rodados uma vez sobre o HEAD atual (`ef17694`), descendente do
> `sha_final` desta fase.

```text
# --- Passo 2: ancestralidade e árvore limpa ---
$ git status --porcelain | wc -l
0
$ git merge-base --is-ancestor 40e2941 HEAD                                  → ANCESTRAL
$ git merge-base --is-ancestor 2e6cd1d1d2a7c060d34fda9137c7aa0b25e52a6f HEAD → ANCESTRAL
$ git show 2d940ed --stat
 frontend/__tests__/lib/hooks/useLogs.test.ts | 85 ++++++++++++++  (1 arquivo, aditivo)

# --- D6-IMP-1 fechado ---
$ cd frontend && npx jest __tests__/lib/hooks/useLogs.test.ts
Tests: 17 passed, 17 total  (4 novos no bloco "toast único por registro")      ✓
$ grep -n "toast" "app/(dashboard)/humor/page.tsx"
106:    // O toast de sucesso é emitido pelo hook (useLogs.ts) — emitir de novo …
   → nenhuma emissão na página, e o comentário explica a ausência              ✓
$ grep -n "toast.success" lib/hooks/useLogs.ts | wc -l
5      → o hook segue sendo a única fonte                                      ✓

# --- os seis passos da fase, relidos no código ---
# 1) FOUC: script inline blocante, com try/catch
$ sed -n '14,15p' app/layout.tsx
// Roda antes do primeiro paint, síncrono e sem depender de React. O `try` cobre
const THEME_NO_FLASH_SCRIPT = `try{var t=localStorage.getItem("caloria-theme");
                                if(t==="dark"){document.documentElement.classList.add("dark")}}catch(e){}`;
$ grep -n "dangerouslySetInnerHTML" app/layout.tsx        → 73                 ✓
$ sed -n '20,28p' components/theme-provider.tsx
// O script inline de `layout.tsx` já aplicou a classe antes do paint. Aqui
// o estado só se alinha ao que está no DOM — nada é reaplicado …             ✓

# 2) logs fora do build de produção
$ grep -n "console\." lib/api.ts app/providers.tsx
(vazio)                                                                        ✓
$ grep -n "NODE_ENV" app/providers.tsx
78:  {process.env.NODE_ENV === "development" && <ReactQueryDevtools …>}   (pré-existente)

# 3) data com o sufixo T12:00
$ grep -n 'T12:00' "app/(dashboard)/peso/page.tsx"
51: // O sufixo "T12:00" evita que a string date-only seja lida como meia-noite
57:  date: new Date(d.date + "T12:00").toLocaleDateString("pt-BR", …)
270: {new Date(l.date + "T12:00").toLocaleDateString("pt-BR", …)}              ✓

# 5) initialMode chegando ao modal
$ grep -n "initialMode" "app/(dashboard)/dashboard/page.tsx" components/dashboard/QuickAddModals.tsx
dashboard/page.tsx:110  <QuickMealModal … initialMode={quickMealMode} />
dashboard/page.tsx:370  <QuickMealModal … initialMode={quickMealMode} />
QuickAddModals.tsx:134  initialMode = "text",
QuickAddModals.tsx:149  const [inputMode, setInputMode] = useState<InputMode>(initialMode);
QuickAddModals.tsx:173  if (open) setInputMode(initialMode);                    ✓

# 6) onError nos hooks silenciosos
$ grep -c "onError" lib/hooks/useProfile.ts lib/hooks/useReminders.ts
useProfile.ts:2   useReminders.ts:4                                            ✓

# --- gate da fase ---
$ cd frontend && npm test         → Test Suites: 20 passed · Tests: 118 passed  ✓
$ cd frontend && npm run lint     → exit 0 (1 Warning pré-existente, Plasma.tsx:156)  ✓
$ cd frontend && npx tsc --noEmit → exit 0                                     ✓

# --- gates de backend, sobre o HEAD atual (a fase não toca backend) ---
$ docker exec caloria_backend pytest -q --cov=app --cov=evals
620 passed, 1 skipped — Required test coverage of 72.0% reached. Total coverage: 74.28%
$ docker exec caloria_backend ruff check . / ruff format --check . / mypy app/ evals/
All checks passed! / 147 files already formatted / Success: no issues found in 81 source files

$ git status --porcelain | wc -l
0
```

## 7. Itens da fase / DoD não atendidos

| Item (§5 / §9 da spec) | Estado |
|---|---|
| Passo 1 — FOUC do tema eliminado | Atendido (script inline blocante, com `try/catch`) |
| Passo 2 — logs fora do build de produção | Atendido (removidos; ver §8) |
| Passo 3 — data do histórico de peso | Atendido (`peso/page.tsx:270`) |
| Passo 4 — toast duplicado removido | Atendido, agora com teste e comentário |
| Passo 5 — `initialMode` nos três atalhos | Atendido |
| Passo 6 — `onError` em `useProfile` e `useReminders` | Atendido (2 e 4 ocorrências) |
| Teste — data renderizada confere | Atendido |
| **Teste — um único toast é emitido** | **Atendido nesta tentativa** (4 testes, incl. caso negativo) |
| Teste — modal abre no modo solicitado | Atendido |
| Teste — build de produção sem os logs | Atendido |
| AC-23 (três partes) | Atendido |
| Gate — `make test-frontend`, `npm run lint`, `npx tsc --noEmit` | Atendido, rodados por mim |

Nada em aberto.

## 8. Divergências entre o relatório e o código real

1. **Nenhuma divergência.** Os quatro testes existem com os nomes declarados, e os seis
   passos conferem no código.

2. **Divergência de letra, não de substância, herdada da tentativa 1:** o passo 2 pede
   *"guardar atrás de `NODE_ENV`"* os logs e aponta `providers.tsx:77` como o padrão a
   espelhar; a implementação **removeu** os `console.*`. O resultado é mais forte para o
   AC-23 ("em build de produção o console não recebe log"), e foi aceito na avaliação da
   tentativa 1 — não o reabro. Registro porque o efeito colateral é real: some também o
   log de desenvolvimento, que era o motivo de a instrução dizer "guardar" em vez de
   "remover". Se fizer falta em depuração, o padrão de `providers.tsx:77` continua ali
   para reintroduzi-los guardados.

3. **O relatório declara ter coberto a sugestão da §5 da avaliação anterior** (verificar
   o mesmo par página/hook em outros lugares). Confirmei: peso e hidratação também
   ganharam teste de contagem. É entrega acima do pedido.
