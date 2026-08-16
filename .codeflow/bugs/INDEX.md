---
versão: 1.0
status: estável
atualizado: 2026-08-08
proximo_numero: 006
---

# Registro de bugs (ordem cronológica)

Registro de **entrada** dos bugs reportados pelo owner, antes de virarem lote de
correção. Cada bug recebe um número sequencial de 3 dígitos (`NNN`), usado como
prefixo do arquivo e como campo `id` no frontmatter.

| # | arquivo | título | severidade | área | status | criado |
|---|---------|--------|------------|------|--------|--------|
| 001 | [001-fluxo-cadastro-refeicao.md](001-fluxo-cadastro-refeicao.md) | Cadastro de refeição não-determinístico e impreciso; banco nutricional subutilizado | alto | backend/ai | corrigido | 2026-07-09 |
| 002 | [002-varredura-saneamento.md](002-varredura-saneamento.md) | Varredura de saneamento: 81 achados de QA manual + auditoria de código | alto | transversal | em-lote | 2026-07-26 |
| 003 | [003-http-413-no-estrato-de-foto.md](003-http-413-no-estrato-de-foto.md) | Análise por foto quebrada em produção: HTTP 413 por `max_tokens` reservado | alto | backend/ai + frontend | aberto | 2026-08-08 |
| 004 | [004-servicos-expostos-no-host-em-producao.md](004-servicos-expostos-no-host-em-producao.md) | Compose de produção publica backend e frontend no host, contornando o Caddy | alto | infra/deploy | corrigido | 2026-08-15 |
| 005 | [005-seed-demo-nao-roda-em-producao.md](005-seed-demo-nao-roda-em-producao.md) | Seed da conta de demonstração não roda na imagem de produção (psycopg2 só no extra `dev`) | alto | backend/scripts + infra | aberto | 2026-08-16 |

## Convenção de enumeração (LER ANTES DE REGISTRAR UM BUG)

1. **Pegar o próximo número** em `proximo_numero` (frontmatter deste arquivo).
   Formatar com 3 dígitos.
2. **Nomear o arquivo** `.codeflow/bugs/NNN-<slug-kebab>.md`.
3. **Registrar a linha** na tabela acima e **incrementar `proximo_numero`**.
4. O número **nunca é reusado nem reordenado**. Bug descartado fica com status
   `não-reproduz` e o número queimado.

Vocabulário de `status`: `aberto`, `em-lote`, `corrigido`, `não-reproduz`,
`convertido-em-melhoria`.

## Relação com `bug-batches/`

Esta pasta é o **registro de entrada**; `.codeflow/bug-batches/` é o **ledger de
execução** consumido por `/batch-bugfix` e `/double-check`.

Quando um bug (ou um conjunto deles) entra em correção:

1. Criar/atualizar `.codeflow/bug-batches/<slug>.{txt,md}` conforme o schema do
   `/batch-bugfix`.
2. Cada linha do ledger referencia o bug de origem por `NNN`.
3. Marcar o bug aqui como `em-lote` e, ao fim do `/double-check`, como
   `corrigido`.

Um bug que, após investigação, se revela pedido de feature migra para
`.codeflow/melhorias/` e fica aqui como `convertido-em-melhoria`, com link.
