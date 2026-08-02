---
spec: 002-vitrine-eval-e-saneamento
fase: A.3
slug_fase: gitleaks
tentativa: 1
veredito: REPROVADO
score: 8.3
threshold: 8.5
range_avaliado: c69fbfb..b58e8ee (reconstruído — ver §8)
---

# FASE A.3 — Avaliação independente

## 1. Veredito e score

**Veredito:** REPROVADO · **Score:** 8.3 / threshold 8.5

Reprovado por dois caminhos: há **1 BLOQUEANTE** e o score ficou abaixo do
threshold. O BLOQUEANTE não é sobre o `gitleaks` — é um gate explícito da própria
fase (`pre-commit run --all-files` verde), declarado no Critério de conclusão da §5
e na DoD §9, que **não está satisfeito** e que o relatório deixa aberto de propósito
sem convertê-lo em decision.

Dito isso, o miolo desta fase é o melhor trabalho do Track A. O executor descobriu
que o gate que a spec mandava construir **não teria detectado o incidente que criou
o Track A**, reportou, obteve autorização e escreveu três regras próprias — e a
diferença é mensurável (`no leaks found` → 30 achados sobre o mesmo histórico).
Verifiquei as três regras com sondas sintéticas próprias e todas disparam.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 2 | AC-3 ✓ nas duas pontas (§6); escopo travado ✓ (segredo sintético, nenhuma allowlist ampla). Descontos pesados: gate `pre-commit run --all-files` verde **não atendido** (§3.1) e `.gitleaks.toml` criado fora dos arquivos declarados sem atualizar a §5 (§4.1) |
| 2 | Arquitetura e direção de dependências | 3 | 5 | Binário direto em vez da action de marketplace (`ci.yml:51-61`) — o comando do CI é byte a byte o rodado localmente; `fetch-depth: 0` e `--redact` são decisões corretas e justificadas |
| 3 | Segurança / LGPD / multi-tenant | 3 | 3 | O gate funciona e é bloqueante. Descontos: `caloria-senha-hardcoded` não pega senha que contenha `$ { } < > [ ]` (§4.3, verificado) e o binário é baixado sem verificação de checksum (§5) |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | `.pre-commit-config.yaml` e `SECURITY.md` estendidos, não substituídos; o step entrou no job `backend` que já existia — exatamente o mapa NOVO/REUSADO da §4 da spec |
| 5 | Padrões de domínio/aplicação | 2 | 5 | Allowlists por valor literal dentro de `[rules.allowlist]` da regra específica; nenhuma por repositório ou regra inteira (`.gitleaks.toml:33-44,54-70,80-99`) |
| 6 | Local e nomes dos arquivos | 2 | 5 | `.gitleaks.toml` na raiz é o caminho canônico de auto-detecção da ferramenta |
| 7 | Qualidade de código | 2 | 5 | `.gitleaks.toml:1-16` registra o *porquê* de cada bloco; `SECURITY.md` declara também **o que o gate não cobre** — honestidade rara em documento de segurança |
| 8 | Testes e cobertura | 2 | 4 | AC-3 provado com exit codes reais nas duas pontas. Desconto: as três regras próprias não têm teste automatizado — uma regressão no regex passaria silenciosa |
| 9 | Migration safety | 2 | [—] | Nenhuma migration tocada (NFR-7) |

Score = (3·2 + 3·5 + 3·3 + 3·5 + 2·5 + 2·5 + 2·5 + 2·4) / 20 · 2 = **8.3**

## 3. Achados BLOQUEANTES

### 3.1 — O gate `pre-commit run --all-files` verde, declarado na §5 e na DoD §9, não está satisfeito

**Onde:** spec §5, Fase A.3, "Critério de conclusão (gate): AC-3 satisfeito;
`pre-commit run --all-files` verde; CI verde" e spec §9, "**A.3** — AC-3;
`pre-commit run --all-files` verde; CI verde". O relatório marca o item como
`[ ]` não satisfeito (`FASE-A.3-gitleaks-EXECUCAO.md:299-314`).

**Verificado por mim, na ponta da branch:**

```text
$ RUFF_CACHE_DIR=<tmp> pre-commit run --all-files
...
fix end of files.........................................................Failed
- hook id: end-of-file-fixer
- exit code: 1
- files were modified by this hook
>>> EXIT=1

$ git status --short | wc -l
19          # 19 arquivos modificados pelos hooks de whitespace/EOF
```

(Árvore revertida em seguida com `git checkout -- .`; `git status --porcelain` → 0.)

**Por que é BLOQUEANTE.** É um gate nominal da fase, não uma sugestão. A causa é
dívida pré-existente (whitespace/EOF em dumps de `docs/auditoria/artefatos/`, CSVs de
`data/`, uma migration, 4 testes e uma página do frontend) e a análise do executor
está certa: corrigir esses 19 arquivos está fora dos três declarados. Mas a
constitution universal é explícita — *"Gates duros não admitem override conversacional
… Override genuíno exige uma decision arquitetural registrada **antes** da próxima
invocação do workflow, não uma autorização falada no meio da execução"*. Deixar o
gate `[ ]` aberto no relatório, com a nota "sugiro resolver na D.4", é precisamente
o override conversacional que a regra proíbe. Não há decision em
`.codeflow/decisions/` nem item na §8 da spec.

**Correção sugerida — qualquer uma das três fecha:**
1. Registrar uma decision no framework (ou item na §8 da spec) que **difira
   explicitamente** o gate `pre-commit run --all-files` para a Fase D.4, nomeando os
   19 arquivos e a razão. É o caminho mais barato e o que o executor já argumentou.
2. Rodar os dois hooks de higiene num commit `style:` isolado, com autorização do
   owner — foi o que se fez para o `.gitleaks.toml`, então o precedente existe.
3. Restringir os hooks `trailing-whitespace`/`end-of-file-fixer` por `exclude:` aos
   diretórios de dado bruto e artefato, o que também remove a armadilha para quem
   rodar `make hooks` no futuro.

Observação de ambiente que **não** entra no gate: o `backend/.ruff_cache/` com
subpastas de `root` citado em `EXECUCAO.md:307-311` não reproduziu aqui — contornei
com `RUFF_CACHE_DIR` e os hooks de `ruff` passaram. A causa da falha é só a dívida
de whitespace/EOF.

## 4. Achados IMPORTANTES

### 4.1 — `.gitleaks.toml` foi criado fora do escopo declarado e a §5 da spec nunca foi atualizada

**Onde:** spec §5, Fase A.3 ("**Arquivos alterados:** `.pre-commit-config.yaml`,
`.github/workflows/ci.yml`, `SECURITY.md`" — sem "Arquivos novos") vs.
`FASE-A.3-gitleaks-EXECUCAO.md:34-48` (§2 e §2.1).

Mesmo defeito de registro apontado na avaliação da A.2, e com a mesma origem: o
executor parou, reportou, obteve autorização — processo correto — mas o registro
ficou só no relatório. A spec §9 exige, como item global, que "toda decisão de escopo
tomada durante a execução esteja registrada aqui em §8 ou numa decision do framework".

```text
$ git show 9dfeef9 -- .../SPEC_002_*.md   # única alteração da spec no track
   → trocou apenas `status: draft`→`active` e `updated_at`
$ ls .codeflow/decisions/ | grep -c 002
0
```

**Cenário de falha concreto.** Um avaliador que leia só a spec vê um arquivo novo na
raiz do repositório que a fase não autorizava, e classifica como violação BLOQUEANTE
de escopo — que é literalmente o que o executor previu em `EXECUCAO.md:354-355`.

**Correção sugerida:** acrescentar `- **Arquivos novos:** `.gitleaks.toml`` ao bloco
da Fase A.3 na §5 e registrar a extensão na §8.

### 4.2 — O AC-2, reconhecidamente falso, continua escrito assim na spec

**Onde:** spec §3, AC-2 (`gitleaks detect --log-opts="--all"` → zero achados) vs.
`FASE-A.2-*-EXECUCAO.md:123-129` e `FASE-A.3-*-EXECUCAO.md:350-360`.

Duas fases consecutivas documentaram que esse critério era vazio — retornava zero
**antes** de qualquer purga, com a credencial em 11 commits. O `.gitleaks.toml`
resolveu a instância (hoje o comando mede de verdade), mas o texto do AC continua
descrevendo a invocação sem `--config`, que volta a ser vazia se alguém rodar o
comando literal da spec. Um critério de aceite que passa por construção é pior que
nenhum: dá falso verde.

**Correção sugerida:** reescrever o AC-2 para (a) fixar `--config .gitleaks.toml` na
invocação **e** (b) somar a verificação direta `git log --all -S'<valor>' | wc -l == 0`,
que não depende de heurística. É a recomendação que os dois relatórios já fazem.

### 4.3 — `caloria-senha-hardcoded` não detecta senha que contenha `$`, `{`, `}`, `<`, `>`, `[` ou `]`

**Onde:** `.gitleaks.toml:30`.

```toml
regex = '''(?i)(?:password|passwd|pwd|senha)[a-z0-9_]*\s*[:=]\s*["'][^"'\s${}<>\[\]]{8,}["']'''
```

A classe negada exclui `$ { } < > [ ]` — presumivelmente para não casar
`"${DB_PASSWORD}"` e afins. O efeito colateral é que **o valor inteiro** é rejeitado
se contiver qualquer um desses caracteres em qualquer posição, e `$` é comum em
senha forte.

**Cenário de falha concreto — verificado por mim, fora do repositório:**

```text
# arquivo de sonda (valores sintéticos; redigidos aqui pelo mesmo motivo que o
# relatório da fase redige os dele — o hook varre este documento)
linha 1:  DB_PASSWORD = "<15 chars sintéticos, com um `$` no meio>"   ← NÃO detectado
linha 2:  senha       = "<8 chars sintéticos, alfanuméricos>"         ← detectado

$ gitleaks detect --no-git --source . --config <repo>/.gitleaks.toml \
    --redact --no-banner --report-format json --report-path /dev/stdout
achados: 1
caloria-senha-hardcoded 2           # só a linha 2
```

Isto é, a regra escrita para "fechar a classe de problema, não só a instância"
deixa aberta uma sub-classe grande. Uma senha real de gerenciador de senhas passa
direto no hook e no CI.

**Correção sugerida:** ancorar a exclusão no **início** do valor em vez de proibir
o caractere em qualquer posição — por exemplo, aceitar `[^"'\s]{8,}` e mover a
proteção contra interpolação para uma allowlist com `regexTarget = "match"` que
isente valores começando por `${`, `{{` ou `<`. Acrescentar as duas sondas acima
como teste automatizado (§5) trava a regressão.

### 4.4 — O `range` do frontmatter não é reconstruível

**Onde:** `FASE-A.3-gitleaks-EXECUCAO.md:8-10`.

```text
$ git merge-base --is-ancestor 5769f238590027c4036776edddc679e5e0dafa4a HEAD
   → NÃO-ancestral   (sha pré-purga)
```

O `sha_final` `7bb06aab` (atualizado em `95c6c8c`) é o commit da Fase B.2. Os
commits reais da A.3 são `4b36c5b` (hook + step + SECURITY.md), `ca005ed`
(`.gitleaks.toml`) e `b58e8ee` (4 isenções pós-purga).

**Correção sugerida:** `range: c69fbfb..b58e8ee`.

## 5. Sugestões

- **O binário do `gitleaks` é baixado sem verificação de integridade.**
  `ci.yml:54-55` faz `curl … | tar -xz` de uma release do GitHub. A versão está
  pinada (`8.21.2`), mas tag de release é mutável e o pipe executa o que vier. Para
  um step cuja função é segurança, vale acrescentar conferência de `sha256` contra o
  checksum publicado — três linhas.
- **`pre-commit run gitleaks --all-files` é evidência mais fraca do que parece.** O
  hook oficial é `entry: gitleaks protect --verbose --redact --staged` com
  `pass_filenames: false` (verificado no cache do pre-commit). Com o índice limpo ele
  não varre nada e passa por construção — o "Passed" da §5.1 do relatório é vacuidade,
  não aprovação. A evidência que vale é a §5.2, com arquivo estagiado de verdade, e
  essa está correta. Vale ajustar a redação do relatório.
- **Sem teste automatizado das três regras próprias.** Um `pytest` que rode
  `gitleaks detect --no-git` sobre um diretório de sondas sintéticas (o que fiz à
  mão em §6) travaria a regressão de regex — e o executor já registra em
  `EXECUCAO.md:220-223` que a primeira versão da regra de senha **não pegava**
  `SENHA_ADMIN = "..."`. Exatamente a classe de erro que um teste pega.
- **A dependência `A.2` não estava concluída quando a A.3 rodou**
  (`EXECUCAO.md:27-32`). Hoje é ponto morto — a A.2 fechou em 2026-08-02 e o CI ficou
  verde depois disso —, e a sequência produziu o melhor resultado possível: o gate
  falhou por PII real (`run #30751122897`) e forçou a purga. Registro só para que a
  máquina de estados de ARTIFACTS_SPEC §2.11 não seja lida como opcional.
- **`make hooks` precisa virar passo obrigatório do setup.** `pre-commit install`
  altera `.git/hooks/`, que não é versionado; sem ele a ponta local do AC-3 é
  opcional na prática e só o CI protege. O alvo já existe (`Makefile:299`); falta
  o README/`docs/setup.md` mandarem rodá-lo.

## 6. Comandos rodados + saídas reais

```text
# --- o comando exato do step do CI, na ponta da branch ---
$ gitleaks detect --source . --config .gitleaks.toml --redact --no-banner --exit-code 1
INF 416 commits scanned.
INF scan completed in 17.3s
INF no leaks found
>>> EXIT=0                                              ← repositório limpo hoje ✓

# --- AC-3: as três regras próprias disparam (sondas sintéticas, FORA do repo,
#     valores inventados, nenhum arquivo do projeto tocado) ---
$ gitleaks detect --no-git --source <scratchpad>/probe --config <repo>/.gitleaks.toml \
    --redact --no-banner --report-format json --report-path /dev/stdout
caloria-senha-preenchida-em-teste | probe.spec.ts | line 1
caloria-email-pessoal             | probe.py      | line 3
caloria-senha-hardcoded           | probe.py      | line 1
>>> EXIT=1                                              ← o gate bloqueia ✓

# --- a lacuna do §4.3: senha com `$` escapa ---
#   sonda de 2 linhas (valores sintéticos, redigidos — ver §4.3):
#     linha 1: DB_PASSWORD = "<15 chars, com um `$` no meio>"
#     linha 2: senha       = "<8 chars alfanuméricos>"
$ gitleaks detect --no-git --source . --config <repo>/.gitleaks.toml ...
achados: 1
caloria-senha-hardcoded 2                               ← só a linha 2 ✗

# --- o gate declarado da fase: pre-commit com TODOS os hooks ---
$ RUFF_CACHE_DIR=<tmp> pre-commit run --all-files
fix end of files.........................................................Failed
- hook id: end-of-file-fixer
- exit code: 1
- files were modified by this hook
>>> EXIT=1
$ git status --short | wc -l
19                                                      ← BLOQUEANTE §3.1
$ git checkout -- . && git status --porcelain | wc -l
0                                                       ← árvore revertida

# --- hook do gitleaks: o que ele realmente executa ---
$ cat ~/.cache/pre-commit/repo*/.pre-commit-hooks.yaml | head -6
- id: gitleaks
  name: Detect hardcoded secrets
  entry: gitleaks protect --verbose --redact --staged
  language: golang
  pass_filenames: false                                 ← varre o índice, não a árvore

# --- CI verde, confirmado na fonte ---
$ gh run list --limit 6 --json databaseId,headSha,conclusion,workflowName
{"conclusion":"success","databaseId":30751992281,"headSha":"7bb06aab...","workflowName":"CI"}
{"conclusion":"failure","databaseId":30751605926,"headSha":"b58e8eec...","workflowName":"CI"}
{"conclusion":"failure","databaseId":30751122897,"headSha":"5322eb52...","workflowName":"CI"}
   # confere com a narrativa: o step do gitleaks derrubou a build antes da purga

# --- YAML e demais gates ---
$ python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"  → OK
$ backend/.venv/bin/python -m ruff check .   → All checks passed!
$ backend/.venv/bin/python -m mypy app/      → Success: no issues found in 72 source files
$ backend/.venv/bin/python -m pytest tests/unit/ -q → 199 passed in 3.03s
$ cd frontend && npm test                    → 17 suites, 100 passed

# --- árvore limpa ao final ---
$ git status --porcelain | wc -l
0
```

## 7. Itens da fase / DoD não atendidos

| Item (§5 / §9 da spec) | Estado |
|---|---|
| Passo 1 — hook `gitleaks` no `.pre-commit-config.yaml` | Atendido (`.pre-commit-config.yaml:11-15`) |
| Passo 2 — step bloqueante no job `backend` do `ci.yml` | Atendido (`ci.yml:51-61`) |
| Passo 3 — `SECURITY.md` atualizado | Atendido, e melhor que o pedido: declara o que o gate não cobre |
| Testes (AC-3) — hook rejeita; CI falha; `pre-commit run --all-files` verde | **PARCIAL** — as duas primeiras ✓, a terceira **NÃO** (§3.1) |
| Gate — AC-3 satisfeito | Atendido |
| Gate — `pre-commit run --all-files` verde | **NÃO ATENDIDO** (§3.1) |
| Gate — CI verde | Atendido (run #30751992281) |
| Elegibilidade — "Depende de: A.2, B.2" | Violada na execução; hoje ponto morto (A.2 concluída) |
| DoD global — decisão de escopo registrada em §8 ou decision | **NÃO ATENDIDO** (§4.1) |

## 8. Divergências entre o relatório e o código real

1. **Nenhuma divergência substantiva** — e isso é notável, porque o relatório é o
   mais autocrítico dos cinco. Ele registra três bloqueios do próprio hook sobre si
   mesmo, um falso verde com `AKIAIOSFODNN7EXAMPLE`, e uma iteração falha do regex
   de senha. Reproduzi as medições centrais e todas batem.

2. **Uma imprecisão de contagem:** `EXECUCAO.md:302-305` fala em "25 arquivos"
   modificados pelos hooks de higiene; medi **19** hoje. Diferença provavelmente por
   arquivos contados duas vezes (um por hook). Não muda a conclusão.

3. **`range` inconsistente** (§4.4).

4. **A §5.1 apresenta como "verde no repositório limpo" uma varredura que não varre
   nada** (`gitleaks protect --staged` com índice limpo). Não é falso — é vacuidade
   apresentada como evidência. A evidência real do AC-3 é a §5.2, que é sólida.
