---
versão: 1.0
status: estável
atualizado: 2026-07-07
schema_version: 1.0
---

# INDEX do .codeflow/ do projeto

## Leia sempre primeiro
1. `constitution.md` — regras invariantes, stack, áreas de alto risco deste projeto.
2. `manifest.md` — stack com versões, comandos de validação, padrões detectados.

## Leia se relevante ao contexto
- `discovered.md` — snapshot do onboarding (consultar em dúvida sobre estrutura/estado do projeto).
- `bug-batches/*` — ledgers dos lotes de bugfix (espinha dorsal do `/batch-bugfix`, entrada do `/double-check`). Lotes: `bugs-teste-v1` (QA manual), `bugs-incidentais-v1` (achados incidentais do lote anterior).
- `decisions/INDEX.md` — índice navegável de decisões. Filtrar por tag relevante antes de carregar decisions individuais.
- `specs/INDEX.md` — registro enumerado das specs (ordem cronológica). **Ao criar uma nova spec, é obrigatório enumerá-la** conforme a convenção descrita ali (próximo número em `proximo_numero`, prefixo `NNN-` na pasta/slug).

## Arquivos gerados automaticamente — não editar manualmente
- `checkpoints/*` — estado intermediário de workflows em execução. Efêmero, vai para `.gitignore`.
- `decisions/<data>-<titulo>.md` — decisões individuais. Geradas por workflows; alterações manuais quebram o índice.

## Versão do schema e última atualização
Schema 1.0 | Última atualização: 2026-07-07 | Gerado por: discover
