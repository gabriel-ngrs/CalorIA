---
versão: 1.0
lote: bugs-incidentais-v1
origem: bugs-incidentais-v1.txt
criado: 2026-07-07
atualizado: 2026-07-07
---

# Lote de bugs: bugs-incidentais-v1

Bugs **incidentais** achados durante a execução do lote `bugs-teste-v1` (não
estavam no `.txt` original). Migrados para este lote próprio a partir da seção
"Observações / bugs incidentais encontrados" de `bugs-teste-v1.md` (itens #1–#4).

Decisão consolidada: `.codeflow/decisions/2026-07-07-lote-bugs-incidentais-v1.md`.

Legenda da coluna `verificação`: preenchida pelo `/double-check` (`✓` sanado,
`✗` regrediu, `⚠` inconclusivo, `—` não verificado). Este workflow deixa `—`.

## Bugs
| id | título | status | repro/teste | fix (arquivo:linha) | decision | verificação |
|----|--------|--------|-------------|---------------------|----------|-------------|
| BI1 | manifest.webmanifest com erro de sintaxe | corrigido | repro manual: abrir qualquer página → console sem `Manifest: Line 1 col 1 Syntax error`; `GET /manifest.webmanifest` retorna JSON (200), não HTML de /login | frontend/middleware.ts:11 (add `manifest\.webmanifest` ao negative lookahead) | 2026-07-07-lote-bugs-incidentais-v1.md | — |
| BI2 | Testes de frontend pré-existentes quebrados (3 testes) | corrigido | `cd frontend && npx jest __tests__/components/dashboard/` (9/9 ✓; suíte completa 90/90 ✓) | frontend/components/dashboard/MacroCards.tsx:122 + frontend/__tests__/components/dashboard/MacroPieChart.test.tsx:32,37 | 2026-07-07-lote-bugs-incidentais-v1.md | — |
| BI3 | Backend mapeia falha de auth do Groq p/ 500 (esperado 503) | corrigido | tests/unit/test_ai_endpoint_errors.py (não coleta sem Postgres — validado via driver standalone: analyze_meal/analyze_photo → 503) | backend/app/api/v1/ai.py:47,74,95 (except `groq.APIError` → 503) | 2026-07-07-lote-bugs-incidentais-v1.md | — |
| BI4 | Recuperação de senha inacessível p/ deslogado (regressão B15/D.3) | corrigido | repro manual: deslogado → "Esqueci minha senha" → carrega /forgot-password (sem 307 → /login). Regex validado por node (forgot/reset-password = skip auth) | frontend/middleware.ts:11 (add `forgot-password\|reset-password` ao negative lookahead) | 2026-07-07-lote-bugs-incidentais-v1.md | — |

## Notas de correção (2026-07-07)

- **BI1 + BI4 — mesma causa-raiz, mesmo arquivo.** Ambos são o `matcher` do
  `frontend/middleware.ts`. O `withAuth` interceptava `/manifest.webmanifest`
  (buscado sem credenciais pelo browser → sem cookie → 307 para `/login` →
  corpo HTML) e o browser tentava parsear HTML como JSON (BI1); e interceptava
  `/forgot-password` / `/reset-password`, redirecionando o deslogado para
  `/login` (BI4). Fix único: adicionar as três rotas ao negative lookahead.
  `frontend/app/manifest.ts` estava **correto** — não foi tocado.

- **BI2 — component-vs-test conforme causa-raiz real.**
  - `MacroCards` (2 testes `/2000 kcal/`): o componente renderizava
    `meta {goal}{unit}` (sem espaço → "meta 2000kcal"); a linha do valor já
    separa número/unidade com `ml-1`. Restaurado o espaço no **componente**
    (`meta {goal} {unit}`) — o teste codificava a intenção de design.
  - `MacroPieChart` (1 teste "Sem dados hoje"): o empty-state foi **redesenhado**
    para "Nenhuma refeição registrada hoje" + subtítulo + CTA. Copy nova é
    intencional → atualizado o **teste** para a copy atual.

- **BI3 — escopo do 503.** Só `analyze-meal` e `analyze-photo` capturavam apenas
  `ValueError`, deixando `groq.APIError` (ex.: `AuthenticationError` de chave
  inválida) vazar como 500. Capturado `groq.APIError` (base de auth/conexão/
  status) → 503. Os endpoints de insights já retornam 502 (que o front `aiErrors`
  trata igual a 503) — não exibiam o 500, logo ficaram fora do escopo mínimo.

## Validação do lote (2026-07-07)
- **Frontend jest:** suíte completa **90 passando / 16 suites** (antes: 3
  falhando). BI2 sanado.
- **Frontend tsc + eslint:** sem erros nos arquivos tocados (`middleware.ts`,
  `MacroCards.tsx`).
- **BI3 runtime:** driver standalone (venv backend, sem DB) confirma
  `analyze_meal`/`analyze_photo` → **503** com `AuthenticationError` do Groq.
  Teste `tests/unit/test_ai_endpoint_errors.py` adicionado (ruff ✓); não coleta
  nesta máquina porque o `conftest` raiz conecta ao Postgres no import (PG
  indisponível) — reexecutar em ambiente com DB.
- **BI1/BI4 runtime:** regex do matcher validado por node — `/manifest.webmanifest`,
  `/forgot-password`, `/reset-password`, `/login` = liberados; `/dashboard`,
  `/refeicoes` = ainda protegidos. Repro no navegador fica para o `/double-check`.
