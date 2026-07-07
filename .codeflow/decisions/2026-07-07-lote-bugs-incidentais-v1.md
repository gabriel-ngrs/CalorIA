---
data: 2026-07-07
titulo: Correções do lote bugs-incidentais-v1
status: ativa
tags: [frontend, middleware, pwa, auth, ai, tests]
lote: bugs-incidentais-v1
---

# Decisão consolidada — lote bugs-incidentais-v1

Registra as escolhas não-triviais ao corrigir os 4 bugs incidentais achados
durante o lote `bugs-teste-v1`. Uma linha por bug que motivou decisão. Ledger:
`.codeflow/bug-batches/bugs-incidentais-v1.md`.

## Decisões por bug

- **BI1 + BI4 — corrigidos no matcher do middleware, não nos arquivos "ref".**
  Os dois relatos apontavam arquivos diferentes (`manifest.ts` / `middleware.ts`),
  mas têm a **mesma causa-raiz**: o `matcher` do `withAuth` em
  `frontend/middleware.ts:11` não excluía três rotas públicas. O browser busca
  `/manifest.webmanifest` **sem credenciais** → sem cookie → `withAuth` responde
  `307 → /login` (corpo HTML) → o browser tenta parsear HTML como JSON e emite
  `Manifest: Line 1, column 1, Syntax error` (BI1). O mesmo redirect torna
  `/forgot-password` e `/reset-password` inacessíveis ao deslogado (BI4, viola
  FR-D4/AC-D3 da spec 001). **Escolha:** um único fix — adicionar
  `forgot-password|reset-password|manifest\.webmanifest` ao negative lookahead.
  `app/manifest.ts` estava correto e **não** foi alterado (evita "corrigir" o
  arquivo errado). Alternativa descartada: excluir só o manifest via header
  `crossorigin`/rota dedicada — mais complexa e não resolveria BI4.

- **BI2 — component-vs-test decidido por causa-raiz, não uniformemente.**
  Regra: o lado que carrega a **intenção correta** é a fonte da verdade.
  - `MacroCards` (2 testes `/2000 kcal/`): a linha de valor já separa número e
    unidade (`ml-1`), mas a linha de meta renderizava `meta {goal}{unit}` colado.
    Tratado como **drift do componente** → restaurado o espaço em
    `MacroCards.tsx:122` (`meta {goal} {unit}`), satisfazendo o teste como escrito.
  - `MacroPieChart` (1 teste "Sem dados hoje"): o empty-state foi **redesenhado**
    (copy "Nenhuma refeição registrada hoje" + subtítulo + CTA) — mudança
    intencional de UI. Tratado como **teste desatualizado** → atualizada a
    asserção. Reverter o componente para a copy antiga seria regressão de UX.

- **BI3 — `groq.APIError` → 503, escopo mínimo nos endpoints que vazavam 500.**
  `analyze-meal`/`analyze-photo` capturavam apenas `ValueError`, então uma falha
  do provedor (ex.: `AuthenticationError` de `GROQ_API_KEY` inválida) propagava e
  virava **500 genérico**. **Escolha:** capturar a base `groq.APIError` (cobre
  auth, conexão, status, rate-limit) → `503` "IA indisponível". Capturar a base
  (em vez de só `AuthenticationError`) mapeia qualquer "IA fora" de forma
  consistente. Os endpoints de insights/patterns já retornam **502**, que o
  `frontend/lib/aiErrors.ts` trata igual a 503 — não exibiam o 500, então ficaram
  **fora do escopo mínimo** para não expandir o diff. Débito aberto: unificar os
  502 desses endpoints para 503 numa passada futura, se quisermos padronizar o
  status no backend. Teste de regressão `tests/unit/test_ai_endpoint_errors.py`;
  validado em runtime via driver standalone (Postgres indisponível impede a
  coleta pytest nesta máquina — o `conftest` raiz conecta ao DB no import).

## Verificação
Coluna `verificação` do ledger deixada `—`. O `/double-check` deve: (1) abrir o
navegador e confirmar ausência do erro de manifest e o acesso a
`/forgot-password` deslogado; (2) reexecutar `tests/unit/test_ai_endpoint_errors.py`
em ambiente com Postgres; (3) `npx jest` verde.
