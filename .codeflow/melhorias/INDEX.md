---
versão: 1.0
status: estável
atualizado: 2026-07-09
proximo_numero: 005
---

# Registro de melhorias (ordem cronológica)

Registro de **entrada** das melhorias e features propostas pelo owner, antes de
virarem spec. Cada melhoria recebe um número sequencial de 3 dígitos (`NNN`).

| # | arquivo | título | tipo | esforço | prioridade | status | criada |
|---|---------|--------|------|---------|------------|--------|--------|
| 001 | [001-modulo-treino.md](001-modulo-treino.md) | Módulo de registro de treino + gasto energético real | módulo novo | alto | alta | a fatiar | 2026-07-09 |
| 002 | [002-modulo-dieta.md](002-modulo-dieta.md) | Módulo de dieta prescrita via upload (PDF/TXT/imagem) com extração por IA | módulo novo | médio | média | a fatiar | 2026-07-09 |
| 003 | [003-gamificacao.md](003-gamificacao.md) | Gamificação: streak, floresta/avatar e progresso visual | módulo novo | médio | média | a fatiar | 2026-07-09 |
| 004 | [004-contexto-de-refeicao.md](004-contexto-de-refeicao.md) | Contexto da refeição (casa/restaurante/preparo) no pipeline de análise | evolução | médio | alta | a fatiar | 2026-07-09 |

## Convenção de enumeração (LER ANTES DE REGISTRAR UMA MELHORIA)

1. **Pegar o próximo número** em `proximo_numero` (frontmatter deste arquivo).
   Formatar com 3 dígitos.
2. **Nomear o arquivo** `.codeflow/melhorias/NNN-<slug-kebab>.md`.
3. **Registrar a linha** na tabela acima e **incrementar `proximo_numero`**.
4. O número **nunca é reusado nem reordenado**.

Vocabulário de `status`: `a fatiar`, `spec: <slug>` (já virou spec),
`adiada`, `descartada`.

## Relação com `specs/`

Esta pasta é o **registro de entrada**; `.codeflow/specs/` é onde a melhoria vira
plano executável. Quando uma melhoria for fatiada:

1. Rodar `/create-spec` a partir do arquivo `NNN-*.md`.
2. Enumerar a spec conforme `.codeflow/specs/INDEX.md` (`proximo_numero`).
3. Trocar o `status` aqui para `spec: NNN-<slug>` e preencher `linked_spec` no
   frontmatter da melhoria.

Melhoria grande demais para uma spec única pode gerar mais de uma (registrar
todas no campo `linked_spec`).
