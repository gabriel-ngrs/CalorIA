---
versão: 1.0
id: "002"
slug: 002-varredura-saneamento
título: "Varredura de saneamento: 81 achados de QA manual + auditoria de código"
severidade: alto
área: transversal
status: em-lote
criado: 2026-07-26
atualizado: 2026-07-26
reportado_por: varredura Fase A (não é relato do owner)
lote: bugs-saneamento-v1
---

# BUG 002 — Varredura de saneamento

Este registro **não é um bug único**: é a entrada de enumeração para o inventário
produzido pela Fase A do trabalho de saneamento, cujo detalhe vive no ledger
[`bug-batches/bugs-saneamento-v1.md`](../bug-batches/bugs-saneamento-v1.md).

Abrir 81 arquivos `bugs/NNN-*.md` cumpriria a letra da convenção e destruiria a
utilidade dela — o registro de `bugs/` é o de **entrada de relatos do owner**,
e estes achados vieram de varredura, não de relato. Um número foi consumido para
manter a rastreabilidade; a enumeração fina dos achados é `S01`–`S81` no ledger.

## Como foi produzido

Seis frentes em paralelo, cada achado passando por um verificador independente
instruído a **refutá-lo** (não a confirmá-lo):

| frente | escopo |
|---|---|
| QA autenticação/perfil | cadastro, login, sessão, reset de senha, onboarding, TDEE |
| QA refeições/dashboard | registro por texto e foto, edição, exclusão, gráficos, histórico |
| QA módulos | peso, hidratação, humor, lembretes, notificações, chat de IA |
| auditoria `services/ai/` | leitura integral + prova por execução no container |
| auditoria backend | endpoints, services, core, workers, com curl e psql |
| auditoria infra | compose, Dockerfiles, Makefile, CI/CD, migrations, pyproject |

## Placar

81 achados: 4 críticos, 21 altos, 34 médios, 22 baixos. 6 eram pedido de feature
disfarçado de bug. 7 corrigidos nesta sessão; o restante **aberto**, agrupado por
tema no ledger.

## Baseline de qualidade — corrigido para o estado real

A auditoria de 2026-05 registrava "ruff 14 erros, mypy 6 erros em `ai_client.py`,
cobertura 62%". Reavaliado hoje: **ruff, `ruff format --check` e `mypy app/`
(strict) passam sem nenhum erro**. O baseline estava desatualizado — foi zerado
pela decision `2026-07-03-baseline-lint-mypy.md` e nunca revalidado no manifest.

O que de fato estava vermelho no gate: `npx tsc --noEmit` falhava por dois
motivos de configuração (`playwright.prod.config.ts` fora do `exclude` do
tsconfig e `tsconfig.tsbuildinfo` da raiz pertencendo a root). Ambos corrigidos.

## Rastreabilidade

- Ledger do lote: [`bug-batches/bugs-saneamento-v1.md`](../bug-batches/bugs-saneamento-v1.md)
- Bug de origem do trabalho: [`001-fluxo-cadastro-refeicao.md`](001-fluxo-cadastro-refeicao.md)
