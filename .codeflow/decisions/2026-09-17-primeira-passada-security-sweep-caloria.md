---
data: 2026-09-17
título: Primeira passada do /security-sweep no CalorIA — risco está em dependência, não em código
status: ativa
tags: [seguranca, security-sweep, dependencias, gitleaks, semgrep, osv-scanner, idor, codeflow]
---

# Primeira passada do /security-sweep no CalorIA

## Contexto

Teste de ponta a ponta do workflow universal `/security-sweep` (recém-criado no codeflow) contra o
CalorIA, profundidade estática (código em disco + histórico git; nenhum alvo vivo). Objetivo duplo:
exercitar o workflow pela primeira vez e levantar a superfície de risco do repo.

## Decisão

Registrar que, na cobertura desta passada, **o risco de segurança do CalorIA está em higiene de
dependência, não em código próprio**. A camada de código amostrada (auth, IDOR em refeições, logging)
saiu limpa; o que exige ação é atualizar dependências com advisory conhecido — prioridade crítica em
`next` e `next-auth`. Os achados confirmados foram encaminhados como lote em
`.codeflow/bug-batches/security-sweep-2026-09-17.md` para `/batch-bugfix` → `/double-check`.

## Números (calibração das ferramentas)

- **gitleaks:** 246 brutos → **0** confirmados. Histórico git limpo; hits são gitignored ou regra
  custom de e-mail. FP-em-contexto ~100% no modo `dir` — usar `gitleaks git` (histórico) como sinal.
- **semgrep:** 1 bruto → **0** (falso-positivo: loga exceção, não token).
- **osv-scanner:** 252 entradas de advisory → candidatos de dependência; contagem inflada por advisory
  acumulado, exige triagem por range/alcance. Crítico: next, next-auth. Alto: axios + deps Python de
  request (starlette, python-multipart).

## Alternativas descartadas

- Tratar os 246 do gitleaks ou os 252 do osv como "vulnerabilidades" — descartado: sem triagem, número
  bruto é ruído (rule `adversarial-testing`).
- Corrigir aqui — descartado: `/security-sweep` só descobre e valida; o fix é `/batch-bugfix`.

## Consequências

- Próximo passo: `/batch-bugfix` sobre o ledger (começar por next/next-auth), depois `/double-check`.
- O workflow `/security-sweep` completou de ponta a ponta na primeira execução — conta como o 1º dos
  dois projetos de exercício exigidos pela `EVOLUTION.md` antes de tirar o status `experimental`.
