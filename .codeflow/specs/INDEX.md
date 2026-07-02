---
versão: 1.0
status: estável
atualizado: 2026-07-02
proximo_numero: 002
---

# Registro de specs (ordem cronológica)

Enumeração canônica das specs do projeto. **Cada spec recebe um número sequencial
de 3 dígitos (`NNN`)** que reflete a ordem cronológica de criação. O número é o
prefixo da pasta e do slug, e também o campo `id` no frontmatter da spec.

| # | slug (pasta) | título | domínio | status | criada |
|---|--------------|--------|---------|--------|--------|
| 001 | [001-backlog-features-qa-v1](001-backlog-features-qa-v1/SPEC_001_BACKLOG_FEATURES_QA_V1.md) | Backlog de features do QA (lote bugs-teste-v1): hidratação CRUD, perfil/TDEE, persistência de IA, recuperação de senha | fullstack | draft | 2026-07-02 |

## Convenção de enumeração (LER ANTES DE CRIAR UMA SPEC)

Ao criar uma nova spec (via `/create-spec` ou manual):

1. **Pegar o próximo número** em `proximo_numero` (frontmatter deste arquivo) —
   aqui, `002`. Formatar com 3 dígitos.
2. **Nomear a pasta e o slug com o prefixo:** `.codeflow/specs/NNN-<slug-kebab>/`
   (ex.: `002-integracao-whatsapp/`). O `slug` no frontmatter da spec é
   `NNN-<slug-kebab>`; o `id` é `NNN`.
3. **Nomear o arquivo** `SPEC_NNN_<NOME>.md` dentro da pasta.
4. **Registrar a nova linha** na tabela acima (na ordem numérica) e **incrementar
   `proximo_numero`** para o próximo valor.

O número **nunca é reusado nem reordenado** — mesmo que uma spec seja cancelada,
seu número fica queimado (marcar a linha como `cancelada`), preservando a leitura
cronológica. Isso mantém estáveis os nomes de artefato de fase
(`FASE-<id>-<slug>-…`), que não dependem do número da spec mas do `id`/`slug` da
fase.
