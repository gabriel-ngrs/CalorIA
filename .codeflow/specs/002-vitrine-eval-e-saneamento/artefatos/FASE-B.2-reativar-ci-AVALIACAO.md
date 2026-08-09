---
spec: 002-vitrine-eval-e-saneamento
fase: B.2
slug_fase: reativar-ci
tentativa: 2
veredito: APROVADO
score: 9.5
threshold: 8.5
range_avaliado: 9b3ff80e069c8ea0d093f582cf9aa47415eacf4e..721f0f0892b3298964b04b917e3f1b0cb5a1cc69
---

# FASE B.2 — Avaliação independente

## 1. Veredito e score

**Veredito:** APROVADO · **Score:** 9.5 / threshold 8.5

Os dois IMPORTANTES da tentativa 1 eram de registro e estão fechados:

- **4.1** (`backend/tests/smoke_test.py` alterado fora do escopo declarado): o
  arquivo entrou na lista de "Arquivos alterados" da Fase B.2 na §5 da spec, com
  nota ligando ao risco R3; a §8 ganhou a **OQ9**; e existe
  `decisions/2026-08-02-smoke-test-como-sonda-de-ambiente.md`. A decision é a melhor
  do lote: argumenta a distinção "sonda de ambiente × teste automatizado", enumera
  quatro alternativas descartadas com o motivo de cada uma, e declara dois riscos
  residuais próprios.
- **4.2** (`range` não reconstruível): remapeado para `9b3ff80..721f0f0`, ambos
  ancestrais de HEAD — verificado.

Além disso a fase colheu um ganho que ela mesma tinha declarado fora de escopo: o
rework da A.3 alinhou a `rev` do `ruff` no `.pre-commit-config.yaml` (v0.8.0 →
v0.15.2), fechando o achado nº 2 da §9 deste relatório ("deriva de versão entre
pre-commit e CI"). Hook e CI agora concordam — verifiquei rodando os dois.

O AC-6 continua demonstrado com evidência mais forte que a pedida, e agora com um
dado novo: a run `#30757473846` sobre o HEAD atual está **verde**, cobrindo os
commits do rework (higiene + regex + docs).

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 5 | AC-6 ✓ com execução automática real e verde no HEAD (§6). Nenhum `continue-on-error` novo (`ci.yml:92`, pré-existente, só no upload de cobertura), nenhum gate de lint/typecheck/teste relaxado. O desconto da tentativa 1 some: `smoke_test.py` agora declarado na §5, com OQ9 e decision |
| 2 | Arquitetura e direção de dependências | 3 | 5 | Jobs `backend` e `frontend` preservados integralmente; `ci.yml:3-7` restaura literalmente os gatilhos que estavam comentados — nada inventado |
| 3 | Segurança / LGPD / multi-tenant | 3 | 4 | Manter o CD em `workflow_dispatch` é a decisão segura, e o comentário de `cd.yml:3-8` atribui a reativação à Fase E.4 sem ambiguidade. Desconto: a condição `GROQ_API_KEY.startswith("gsk_")` faz a sonda voltar a rodar contra a Groq real **e** contra `localhost:5432/caloria_db` se uma chave verdadeira chegar ao CI — cenário previsto para a Fase C.7. A decision registra dois riscos residuais, mas não este (§5) |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | Gatilhos restaurados são os já comentados; `README.md` não alterado porque o badge já apontava para `ci.yml` — o passo 4 pedia "confirmar", e confirmar sem diff é a leitura certa |
| 5 | Padrões de domínio/aplicação | 2 | 5 | O comentário de `cd.yml` troca "temporariamente desabilitado" por atribuição explícita de responsabilidade — elimina a ambiguidade que a fase existia para eliminar |
| 6 | Local e nomes dos arquivos | 2 | 5 | `ci.yml`, `cd.yml`, `Makefile`, `README.md` e `backend/tests/smoke_test.py` — todos agora declarados na §5 |
| 7 | Qualidade de código | 2 | 4 | Comentários registram o *porquê*. Desconto mantido: `Makefile:291-296` ainda diz cobrir "pytest completo", mas a cadeia roda `tests/unit/` + `tests/integration/` enquanto o CI roda `pytest` sobre `testpaths = ["tests"]`, que inclui `tests/smoke_test.py`. A promessa de equivalência falsa era o defeito que o passo 3 existia para remover |
| 8 | Testes e cobertura | 2 | 5 | AC-6 provado por observação de falhas reais em dois gates distintos antes do verde, e não por violação sintética |
| 9 | Migration safety | 2 | [—] | Nenhuma migration tocada (NFR-7) |

Score = (3·5 + 3·5 + 3·4 + 3·5 + 2·5 + 2·5 + 2·4 + 2·5) / 20 · 2 = **9.5**

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

Nenhum.

## 5. Sugestões

- **O `skipif` do smoke test tem um efeito colateral que a decision não cobre.**
  A decision registra dois riscos residuais (prefixo do provedor mudar; teste novo
  herdar o `pytestmark`), mas não o que a avaliação anterior apontou: se uma chave
  real da Groq entrar no CI — cenário explicitamente previsto para a camada completa
  do eval da Fase C.7 —, os quatro testes voltam a rodar automaticamente contra a
  API real **e** contra `postgresql://…@localhost:5432/caloria_db`, queimando cota do
  free tier a cada push. Vale acrescentar o parágrafo à decision, ou antecipar o
  débito já registrado (mover a sonda para `backend/scripts/`), que elimina os três
  riscos de uma vez.
- **A mensagem do alvo `check` ainda promete um pouco mais do que entrega.**
  Trocar "pytest completo" por "`pytest tests/unit/` + `tests/integration/`" resolve,
  e é uma linha.
- **`make check` ficou mais caro** — agora exige a stack dev no ar para
  `test-integration`. Depois da B.1 seria possível rodar `tests/unit/` no host sem
  Docker. Corretamente fora do escopo desta fase; candidato a uma fase de higiene.
- **O `range` resolve mas não isola.** `9b3ff80..721f0f0` cobre as cinco fases do
  lote, e os commits desta fase (`b9cb561` e `7bb06aa`) não são contíguos — os três
  da A.3 estão entre eles. É o que o schema manda (§2.9.3), mas vale nomear os dois
  SHAs no corpo do relatório.

## 6. Comandos rodados + saídas reais

```text
# --- branch e ancestralidade (Passo 2) — o achado 4.2 ---
$ git rev-parse --short HEAD
da08121
$ git merge-base --is-ancestor 9b3ff80e069c8ea0d093f582cf9aa47415eacf4e HEAD  → ANCESTRAL
$ git merge-base --is-ancestor 721f0f0892b3298964b04b917e3f1b0cb5a1cc69 HEAD  → ANCESTRAL
$ git log --format='%h %s' -1 9b3ff80
9b3ff80 test(backend): cria schema em fixture e libera testes unit de infra    ✓

# --- AC-6, parte 1: gatilhos lidos do arquivo, não do relatório ---
$ sed -n '1,7p' .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [dev]
  pull_request:
    branches: [main]                                                          ✓
$ sed -n '1,10p' .github/workflows/cd.yml
name: CD — Deploy em Produção
# Deploy manual por decisão explícita, não por pendência de conserto: a topologia de
# produção ainda não foi decidida (spec 002, Fase E.2). A reativação do gatilho
# automático abaixo é responsabilidade da Fase E.4 …
#   push:
#     branches: [main]
on:
  workflow_dispatch:                          ← mantido por decisão (passo 2)   ✓

# --- AC-6, parte 2: execução automática real, verificada na fonte ---
$ gh run list --limit 5 --json databaseId,headSha,conclusion,workflowName
{"conclusion":"success","databaseId":30757473846,"headSha":"da081216…","workflowName":"CI"}
{"conclusion":"success","databaseId":30751992281,"headSha":"7bb06aab…","workflowName":"CI"}
{"conclusion":"failure","databaseId":30751605926,"headSha":"b58e8eec…","workflowName":"CI"}
{"conclusion":"failure","databaseId":30751122901,"headSha":"b226f39d…","workflowName":"CI"}
{"conclusion":"failure","databaseId":30751122897,"headSha":"5322eb52…","workflowName":"CI"}
   # duas falhas reais em gates distintos antes do primeiro verde, e agora um segundo
   # verde sobre o HEAD do rework — AC-6 demonstrado por observação                ✓

# --- nenhum gate relaxado ---
$ grep -n "continue-on-error" .github/workflows/ci.yml
92:        continue-on-error: true        ← só no upload de cobertura, PRÉ-EXISTENTE

# --- registro do escopo (IMPORTANTE 4.1) ---
$ grep -n "smoke_test.py" .codeflow/specs/002-*/SPEC_002_*.md | head -3
649:  `Makefile`, `README.md`, `backend/tests/smoke_test.py`.
652:  > em `backend/tests/smoke_test.py`. O arquivo é uma **sonda de ambiente** morando
1466:- **OQ9 — `backend/tests/smoke_test.py` falhando ao reativar o CI.**
$ ls .codeflow/decisions/2026-08-02-smoke-test-como-sonda-de-ambiente.md
.codeflow/decisions/2026-08-02-smoke-test-como-sonda-de-ambiente.md            ✓

# --- o ganho colateral: hook e CI concordam agora ---
$ sed -n '8,15p' .pre-commit-config.yaml
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.2                              ← era v0.8.0
$ pre-commit run --all-files
ruff (legacy alias)......................................................Passed
ruff format..............................................................Passed
Detect hardcoded secrets.................................................Passed
… (todos os 9 hooks Passed)
>>> EXIT=0
$ git status --porcelain | wc -l
0                                             ← os hooks não tocaram a árvore

# --- os mesmos gates que o CI roda, verificados localmente ---
$ backend/.venv/bin/python -m ruff check .          → All checks passed!
$ backend/.venv/bin/python -m ruff format --check . → 119 files already formatted
$ backend/.venv/bin/python -m mypy app/             → Success: no issues found in 72 source files
$ backend/.venv/bin/python -m pytest tests/unit/ -q → 199 passed in 2.73s
$ cd frontend && npm test                           → 17 suites, 100 passed
$ cd frontend && npm run lint                       → 1 Warning pré-existente; exit 0
$ cd frontend && npx tsc --noEmit                   → exit 0

# --- badge do README (passo 4 = confirmar, sem alterar) ---
$ grep -n "badge.svg" README.md
5:[![CI](https://github.com/gabriel-ngrs/CalorIA/actions/workflows/ci.yml/badge.svg)](…) ✓

# --- make test-integration: [—] NÃO RODADO ---
$ docker ps
The command 'docker' could not be found in this WSL 2 distro.

# --- árvore limpa ao final ---
$ git status --porcelain | wc -l
0
```

## 7. Itens da fase / DoD não atendidos

| Item (§5 / §9 da spec) | Estado |
|---|---|
| Passo 1 — restaurar gatilhos de `ci.yml`, remover `workflow_dispatch` e o comentário | Atendido |
| Passo 2 — `cd.yml` manual, com a responsabilidade da E.4 declarada | Atendido (`cd.yml:2-8`) |
| Passo 3 — corrigir o alvo `check` do Makefile | Atendido; ver ressalva de redação em §5 |
| Passo 4 — confirmar o badge do README | Atendido, sem diff |
| Testes (AC-6) — push dispara; jobs verdes; violação de gate derruba a build | Atendido, com evidência mais forte que a pedida |
| Gate — execução verde visível no GitHub Actions | Atendido (run `#30757473846`, sobre o HEAD atual) |
| Escopo travado — nenhum gate relaxado, nenhum `continue-on-error` novo | Atendido |
| DoD global — decisão de escopo registrada em §8 ou decision | **Atendido nesta tentativa** (OQ9 + decision) |

## 8. Divergências entre o relatório e o código real

1. **Nenhuma divergência.** Todas as afirmações verificáveis conferem: gatilhos,
   `cd.yml` mantido manual, badge, `continue-on-error` restrito ao upload de
   cobertura, e as runs do GitHub Actions com os SHAs e conclusões exatos.

2. **`range` corrigido e resolvendo** — fecha o IMPORTANTE 4.2. Permanece a ressalva
   de que um intervalo único não descreve honestamente uma fase cujos dois commits
   não são contíguos.

3. **Registro herdado, ainda válido:** o commit `7bb06aa` também trocou
   `isinstance(data, (dict, list))` por `isinstance(data, dict | list)` em
   `smoke_test.py` — correção da regra `UP038` do `ruff`, coerente com o achado de
   deriva de versão, mas não listada como mudança em lugar nenhum. Inócua; com a
   `rev` do hook agora alinhada, a causa dessa classe de surpresa sumiu.
