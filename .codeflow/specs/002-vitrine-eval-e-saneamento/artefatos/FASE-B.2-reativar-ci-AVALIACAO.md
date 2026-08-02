---
spec: 002-vitrine-eval-e-saneamento
fase: B.2
slug_fase: reativar-ci
tentativa: 1
veredito: RESSALVAS
score: 8.9
threshold: 8.5
range_avaliado: 9dfeef9..b9cb561 + 7bb06aa (reconstruído — ver §8)
---

# FASE B.2 — Avaliação independente

## 1. Veredito e score

**Veredito:** RESSALVAS · **Score:** 8.9 / threshold 8.5

O objetivo da fase foi cumprido e eu confirmei na fonte: os gatilhos automáticos
estão restaurados, o CI dispara em `push` para `dev`, e a execução verde existe. O
AC-6 foi demonstrado da melhor forma possível — não com uma violação sintética de
`ruff`, mas com **duas falhas reais consecutivas em gates diferentes** antes da
execução verde. Isso prova o mecanismo com mais força do que o teste que a spec pedia.

As ressalvas são duas, e ambas de registro/limite: a fase alterou
`backend/tests/smoke_test.py`, que não está entre os arquivos que ela declara, e a
alteração é justamente um `skipif` que transforma um step vermelho em verde — o
raciocínio é bom, mas essa é a fronteira exata do escopo travado da fase e merecia
uma decision, não um parágrafo de relatório.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 3 | AC-6 ✓ com execução real (§6). Nenhum `continue-on-error` novo, nenhum gate de lint/typecheck relaxado. Desconto: `backend/tests/smoke_test.py` alterado fora dos 4 arquivos declarados, e a alteração é um `skip` que destrava o CI (§4.1) |
| 2 | Arquitetura e direção de dependências | 3 | 5 | Jobs `backend` e `frontend` preservados integralmente — nenhum step, service, env ou versão de action tocado; `ci.yml:3-7` restaura literalmente os gatilhos que estavam comentados |
| 3 | Segurança / LGPD / multi-tenant | 3 | 4 | Manter o CD em `workflow_dispatch` é a decisão segura: reativar dispararia deploy para topologia não auditada, com o `sleep 10` ainda no lugar. Desconto: a condição do `skipif` (`GROQ_API_KEY.startswith("gsk_")`) faz o smoke test **rodar contra a Groq real** se alguma chave verdadeira chegar ao CI (§5) |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | Gatilhos restaurados são os já comentados em `:5-8`; nada inventado. `README.md` não alterado porque o badge já apontava para `ci.yml` — o passo 4 pedia "confirmar", e confirmar sem diff é a leitura certa |
| 5 | Padrões de domínio/aplicação | 2 | 5 | O comentário de `cd.yml:3-6` troca "temporariamente desabilitado" por atribuição explícita de responsabilidade (Fase E.4) — elimina a ambiguidade que a fase existia para eliminar |
| 6 | Local e nomes dos arquivos | 2 | 5 | `ci.yml`, `cd.yml`, `Makefile` — todos declarados na §5 |
| 7 | Qualidade de código | 2 | 4 | Comentários registram o *porquê*. Desconto: a mensagem nova do `check` afirma cobrir "pytest completo", o que ainda não é exato (§5) |
| 8 | Testes e cobertura | 2 | 5 | AC-6 provado por observação de falhas reais em dois gates distintos, e não por teste sintético — evidência mais forte que a pedida |
| 9 | Migration safety | 2 | [—] | Nenhuma migration tocada (NFR-7) |

Score = (3·3 + 3·5 + 3·4 + 3·5 + 2·5 + 2·5 + 2·4 + 2·5) / 20 · 2 = **8.9**

## 3. Achados BLOQUEANTES

Nenhum.

Registro o raciocínio, porque o caso é limítrofe: o escopo travado da fase diz
"não relaxar nenhum gate para fazer o CI passar … uma falha indica regressão real e
deve ser corrigida, não silenciada". A alteração de `smoke_test.py` é literalmente um
`skip` que faz o CI passar. **Não** a classifico como BLOQUEANTE porque a premissa da
regra não se aplica: o escopo travado justifica a proibição com "`ruff` e `mypy` já
passam limpos hoje", isto é, ela mira em regressão real de qualidade. `smoke_test.py`
não era uma regressão — é uma sonda de ambiente com `DB_URL` hardcoded para o banco
de **desenvolvimento** (`smoke_test.py:37`) e chamada à API real da Groq, morando
dentro de `testpaths = ["tests"]` sem nenhum marker. Nunca poderia passar em CI, em
nenhum commit. Declarar a pré-condição não é silenciar defeito; é corrigir uma
declaração errada. E `ruff`, `mypy` e os 294 testes restantes seguem bloqueantes.

## 4. Achados IMPORTANTES

### 4.1 — `backend/tests/smoke_test.py` foi alterado fora do escopo declarado, sem registro em §8 nem decision

**Onde:** spec §5, Fase B.2 ("**Arquivos alterados:** `.github/workflows/ci.yml`,
`.github/workflows/cd.yml`, `Makefile`, `README.md`") vs. o diff real, que inclui
`backend/tests/smoke_test.py` (+34/-6 no commit `7bb06aa`).

O processo foi correto — `EXECUCAO.md:157-174` registra que o executor avaliou o
escopo travado, **reportou ao owner antes de agir** e obteve autorização. O que falta
é o registro no lugar que a spec designa. A §9 exige, como item global: "Toda decisão
de escopo tomada durante a execução está registrada aqui em §8 ou numa decision do
framework". Verificado:

```text
$ git show 9dfeef9 -- .../SPEC_002_*.md    # única alteração da spec no track inteiro
   → trocou apenas `status: draft`→`active` e `updated_at: 2026-07-29`→`2026-07-30`
$ ls .codeflow/decisions/
2026-07-02-lote-bugs-teste-v1.md        2026-07-03-baseline-lint-mypy.md
2026-07-07-lote-bugs-incidentais-v1.md  2026-07-26-limiares-lookup-nutricional.md
   → nenhuma decision referente à spec 002
```

**Cenário de falha concreto.** Numa reavaliação em chat zerado, o avaliador lê a §5
da spec, vê um arquivo de teste alterado fora da lista, vê que a alteração é um
`skip`, cruza com o escopo travado que proíbe exatamente isso, e reprova. É o
terceiro caso idêntico no Track A/B (ver A.2 §4.1 e A.3 §4.1): o executor sempre
parou e reportou, e o registro nunca subiu para a spec.

**Correção sugerida:** acrescentar `backend/tests/smoke_test.py` à lista de arquivos
da Fase B.2 na §5 e registrar na §8 a decisão de declarar as pré-condições do smoke
test. Melhor ainda, e mais barato a longo prazo: mover a sonda para
`backend/scripts/` — fora de `testpaths` —, que resolve a causa em vez do sintoma e
elimina o `skipif` por completo.

### 4.2 — O `range` do frontmatter não é reconstruível

**Onde:** `FASE-B.2-reativar-ci-EXECUCAO.md:8-10`.

```text
$ git merge-base --is-ancestor 425830930d64a876cf1997db54d681a4f44a64fc HEAD
   → NÃO-ancestral   (sha pré-purga, inalcançável desde o filter-repo da A.2)
```

O `sha_final` `7bb06aab` está correto para o segundo commit da fase, mas o
`sha_inicial` desapareceu com a reescrita de histórico. Os commits reais da B.2 são
`b9cb561` (gatilhos + Makefile) e `7bb06aa` (pré-condições do smoke test) — note que
eles **não são contíguos**: os três commits da A.3 (`4b36c5b`, `ca005ed`, `b58e8ee`)
estão entre os dois, porque as fases foram executadas de forma intercalada. Um único
`range` não descreve honestamente esta fase.

**Correção sugerida:** `range: 9dfeef9..b9cb561` para o corpo da fase, com o commit
`7bb06aa` listado à parte no relatório como adendo pós-CI — ou, mais simples, declarar
os dois SHAs explicitamente em vez de um intervalo.

## 5. Sugestões

- **A mensagem do `check` ainda promete um pouco mais do que entrega.**
  `Makefile:291-296` diz cobrir "pytest completo", mas a cadeia roda
  `pytest tests/unit/` + `pytest tests/integration/`, enquanto o CI roda `pytest`
  sobre `testpaths = ["tests"]` — que inclui `tests/smoke_test.py` na raiz. Hoje o
  delta é inócuo (o módulo se declara `skipped` sem chave real), mas a promessa de
  equivalência era exatamente o defeito que o passo 3 da fase existia para remover.
  Trocar por "`pytest tests/unit/` + `tests/integration/`" resolve.
- **O `skipif` do smoke test tem um efeito colateral silencioso.** A condição é
  `GROQ_API_KEY.startswith("gsk_")` (`smoke_test.py:44`). Se um dia uma chave real
  entrar no CI — por exemplo para a camada completa do eval da Fase C.7 —, os quatro
  smoke tests voltam a rodar automaticamente contra a Groq real **e** contra
  `postgresql://…@localhost:5432/caloria_db`, queimando cota do free tier a cada push.
  Mover a sonda para fora de `testpaths` (sugestão de §4.1) elimina o risco.
- **Deriva de versão entre pre-commit e CI, herdada e não resolvida.**
  `.pre-commit-config.yaml:3` fixa `ruff v0.8.0`; o `pyproject.toml` pede `>=0.8.0` e
  o CI resolve 0.15.x. O relatório registra que a regra `UP038` já causou divergência
  real (hook local reprovando código que o CI aprova) e corrigiu a linha ofensora —
  mas o descasamento segue. Alinhar as duas versões é barato e evita a próxima.
- **`make check` ficou mais caro** (agora exige a stack dev no ar para
  `test-integration`). Depois da B.1 seria possível rodar `tests/unit/` no host sem
  Docker; o alvo do Makefile não foi ajustado, e corretamente — está fora do escopo
  desta fase. Candidato a uma fase de higiene.

## 6. Comandos rodados + saídas reais

```text
# --- AC-6, parte 1: os gatilhos estão restaurados (lido do arquivo, não do relatório) ---
$ sed -n '1,8p' .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [dev]
  pull_request:
    branches: [main]
$ python3 -c "import yaml; print(yaml.safe_load(open('.github/workflows/ci.yml'))['on'])"
{'push': {'branches': ['dev']}, 'pull_request': {'branches': ['main']}}      ✓
$ python3 -c "import yaml; print(yaml.safe_load(open('.github/workflows/cd.yml'))['on'])"
{'workflow_dispatch': None}                          ← mantido por decisão (passo 2) ✓

# --- AC-6, parte 2: execução automática real, verificada na fonte ---
$ gh run list --limit 6 --json databaseId,headSha,conclusion,workflowName,displayTitle
#30751992281  7bb06aab  success   "test(backend): declara pre-condicoes do smoke test…"
#30751605926  b58e8eec  failure   "ci(seguranca): isenta valores sinteticos remanescentes…"
#30751122897  5322eb52  failure   "docs(specs): atualiza relatorios de a.2 e a.3…"
   # duas falhas reais em gates distintos antes do verde — AC-6 ("falha a build se um
   # gate falhar") demonstrado por observação, não por violação sintética ✓

# --- nenhum gate relaxado ---
$ grep -n "continue-on-error" .github/workflows/ci.yml
92:        continue-on-error: true        ← só no upload de cobertura, PRÉ-EXISTENTE
   # nenhum em Lint/Type check/Testes; tratamento do upload é da Fase B.4

# --- Makefile: a cadeia agora inclui integração ---
$ make -n check | grep pytest
docker compose -f docker-compose.dev.yml exec backend pytest tests/unit/ -v
docker compose -f docker-compose.dev.yml exec backend pytest tests/integration/ -v   ← NOVO

# --- badge do README (passo 4 = confirmar, sem alterar) ---
$ sed -n '5p' README.md
[![CI](https://github.com/gabriel-ngrs/CalorIA/actions/workflows/ci.yml/badge.svg)](...)
$ git diff 461ee38..HEAD -- README.md | wc -l
0                                                    ← confirmado sem diff ✓

# --- os mesmos gates que o CI roda, verificados localmente ---
$ backend/.venv/bin/python -m ruff check .            → All checks passed!
$ backend/.venv/bin/python -m ruff format --check .   → 119 files already formatted
$ backend/.venv/bin/python -m mypy app/               → Success: no issues found in 72 source files
$ backend/.venv/bin/python -m pytest tests/unit/ -q   → 199 passed in 3.03s
$ cd frontend && npm test                             → 17 suites, 100 passed
$ cd frontend && npm run lint
   → 1 Warning pré-existente (Plasma.tsx, react-hooks/exhaustive-deps); exit 0

# --- make test-integration: [—] NÃO RODADO (Docker indisponível nesta máquina) ---
$ docker ps
The command 'docker' could not be found in this WSL 2 distro.

# --- escopo real do diff da fase ---
$ git show b9cb561 --stat --format=''
 .github/workflows/cd.yml | 6 ++++--
 .github/workflows/ci.yml | 9 +++------
 Makefile                 | 7 +++++--
$ git show 7bb06aa --stat --format=''
 backend/tests/smoke_test.py | 34 +++++++++++++++++++++++++++++++---
   # o 2º commit sai dos 4 arquivos declarados na §5 → achado §4.1

# --- árvore limpa ao final ---
$ git status --porcelain | wc -l
0
```

## 7. Itens da fase / DoD não atendidos

| Item (§5 / §9 da spec) | Estado |
|---|---|
| Passo 1 — restaurar gatilhos de `ci.yml`, remover `workflow_dispatch` e o comentário | Atendido |
| Passo 2 — `cd.yml`: manter manual e registrar sem ambiguidade que a reativação é da E.4 | Atendido (`cd.yml:3-6`) |
| Passo 3 — corrigir o alvo `check` do Makefile | Atendido (fez as duas saídas oferecidas pela spec); ver ressalva de redação em §5 |
| Passo 4 — confirmar o badge do README | Atendido, sem diff |
| Testes (AC-6) — push dispara; jobs verdes; violação de gate derruba a build | Atendido, com evidência mais forte que a pedida |
| Gate — execução verde visível no GitHub Actions | Atendido (run #30751992281, dois jobs `success`) |
| Escopo travado — nenhum gate relaxado, nenhum `continue-on-error` novo | Atendido para lint/typecheck/teste; ver §3 sobre o `skipif` |
| DoD global — decisão de escopo registrada em §8 ou decision | **NÃO ATENDIDO** (§4.1) |

## 8. Divergências entre o relatório e o código real

1. **Nenhuma divergência substantiva.** Todas as afirmações verificáveis conferem:
   gatilhos, YAML, badge, cadeia do `make check`, os três runs do GitHub Actions com
   os SHAs e conclusões exatos, e o `continue-on-error` restrito ao upload de
   cobertura.

2. **A §3 do relatório omite `backend/tests/smoke_test.py` da tabela "Arquivos
   ALTERADOS".** A alteração está descrita com honestidade na §9, item 1, mas não
   aparece onde o leitor procura o escopo do diff. Combinado com a §5 da spec não
   atualizada, o arquivo fica invisível para quem não ler o relatório até o fim.

3. **`range` inconsistente e não contíguo** (§4.2): o `sha_inicial` é pré-purga, e os
   dois commits da fase estão separados pelos três commits da Fase A.3.

4. **Um efeito colateral não mencionado.** O commit `7bb06aa` também troca
   `isinstance(data, (dict, list))` por `isinstance(data, dict | list)` em
   `smoke_test.py:104` — correção da regra `UP038` do `ruff`, coerente com o achado
   de deriva de versão da §9 item 2, mas não listada em lugar nenhum como mudança.
   Inócua; registro por completude.
