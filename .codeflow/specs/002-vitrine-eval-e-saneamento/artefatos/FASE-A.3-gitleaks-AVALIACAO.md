---
spec: 002-vitrine-eval-e-saneamento
fase: A.3
slug_fase: gitleaks
tentativa: 2
veredito: APROVADO
score: 9.5
threshold: 8.5
range_avaliado: b9cb561e6c4dd3f0c63fd1f171dfe15496d3d88d..721f0f0892b3298964b04b917e3f1b0cb5a1cc69
---

# FASE A.3 — Avaliação independente

## 1. Veredito e score

**Veredito:** APROVADO · **Score:** 9.5 / threshold 8.5

O BLOQUEANTE e os quatro IMPORTANTES da tentativa 1 estão fechados, e verifiquei os
cinco eu mesmo, na ponta da branch:

- **3.1 (BLOQUEANTE)** — `pre-commit run --all-files` retorna **EXIT=0** e não toca a
  árvore. Rodei duas vezes, com e sem `RUFF_CACHE_DIR` sobreposto; passa nos dois
  casos, então a observação de ambiente sobre `.ruff_cache` não reproduz aqui.
  O executor escolheu o caminho que **resolve** (commit `style:` de higiene +
  alinhamento da `rev` do `ruff`) em vez do que adia.
- **4.1** — §5 da spec ganhou `Arquivos novos: .gitleaks.toml`; §8 ganhou a **OQ8**;
  existe `decisions/2026-08-02-regras-proprias-gitleaks.md`.
- **4.2** — o AC-2 foi reescrito e agora exige duas verificações conjuntas, uma
  delas independente de heurística.
- **4.3** — a lacuna do regex está fechada na parte que importava. Montei sonda
  própria fora do repositório: `Pa$$w0rd123ABC`, `Xy{zab}cd12`, `qq[ww]ee12` e
  `aa<bb>cc12` **são detectados agora**; `${DB_PASS}`, `<senha-aqui>`, `{{SENHA}}`,
  `[REDIGIDO]` e `%(pass)s` continuam corretamente ignorados.
- **4.4** — `range` remapeado, ambos os SHAs ancestrais de HEAD.

O commit `style:` de higiene é o ponto que mais poderia ter dado errado, e não deu:
confirmei que é **puramente mecânico** — `git diff --ignore-all-space
--ignore-blank-lines --stat 7497e63^ 7497e63` retorna vazio. Nenhuma linha de lógica
mudou em 15 arquivos.

Resta uma sub-classe menor do regex ainda aberta (senha cujo **primeiro** caractere
é `$ < { [ %`) — registrada na §5, não como IMPORTANTE: nenhum critério declarado da
fase a exige, e a lacuna anterior era uma ordem de grandeza maior.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 5 | Os três itens do Critério de conclusão agora fecham: AC-3 ✓, `pre-commit run --all-files` **EXIT=0** com árvore intocada (§6), CI verde na run `#30757473846` sobre o HEAD atual. Escopo travado ✓: segredo sintético, nenhuma allowlist ampla; o `.gitleaks.toml` e o commit `style:` estão declarados na §5 da spec |
| 2 | Arquitetura e direção de dependências | 3 | 5 | Binário direto em vez de action de marketplace (`ci.yml:51-61`): o comando do CI é byte a byte o que rodo localmente. Alinhar a `rev` do `ruff` ao que o projeto resolve (`.pre-commit-config.yaml:9`) elimina a divergência hook↔CI |
| 3 | Segurança / LGPD / multi-tenant | 3 | 4 | O gate funciona, é bloqueante nas duas pontas, e a correção do regex fecha a sub-classe grande — verificado por sonda própria (§6). Descontos: valor iniciado por `$ < { [ %` ainda escapa (§5) e o binário do gitleaks continua baixado sem conferência de checksum (`ci.yml:54-55`) |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | `.pre-commit-config.yaml` e `SECURITY.md` estendidos, não substituídos; o step entrou no job `backend` que já existia |
| 5 | Padrões de domínio/aplicação | 2 | 5 | Allowlists por valor literal dentro de `[rules.allowlist]` da regra específica (`.gitleaks.toml:40-51,62-78,88-107`); nenhuma por repositório ou regra inteira |
| 6 | Local e nomes dos arquivos | 2 | 5 | `.gitleaks.toml` na raiz é o caminho canônico de auto-detecção da ferramenta |
| 7 | Qualidade de código | 2 | 5 | `.gitleaks.toml:28-36` registra o *porquê* da correção, inclusive a restrição do RE2 (sem lookahead) que moldou a solução; `.pre-commit-config.yaml:2-7` idem para a `rev` |
| 8 | Testes e cobertura | 2 | 4 | AC-3 provado com exit codes reais nas duas pontas. Desconto mantido: as três regras próprias seguem sem teste automatizado — e esta tentativa provou o ponto, porque a lacuna do 4.3 só apareceu por sonda manual e a que resta também |
| 9 | Migration safety | 2 | [—] | Nenhuma migration tocada (NFR-7) |

Score = (3·5 + 3·5 + 3·4 + 3·5 + 2·5 + 2·5 + 2·5 + 2·4) / 20 · 2 = **9.5**

## 3. Achados BLOQUEANTES

Nenhum. O BLOQUEANTE 3.1 da tentativa 1 está fechado — evidência na §6.

## 4. Achados IMPORTANTES

Nenhum.

## 5. Sugestões

- **Sobrou uma sub-classe do regex: senha cujo *primeiro* caractere é `$ < { [ %`.**
  A classe negada `[^"'\s$<{\[%]` agora vale só para a primeira posição — que é a
  correção certa e fecha o caso reportado —, mas ela é absoluta ali. Verificado por
  mim, fora do repositório (`.gitleaks.toml:37`):

  ```text
  # sondas fora do repositório; valores redigidos aqui pelo mesmo motivo que o
  # relatório da fase redige os dele — o hook varre este documento
  atribuição de senha cujo valor começa por `$`   → NÃO detectado
  atribuição de senha cujo valor começa por `%`   → NÃO detectado
  atribuição de senha com espaços no valor        → detectado (falso positivo novo:
                                                    o regex antigo excluía `\s` no
                                                    valor inteiro; o novo, só na 1ª
                                                    posição)
  ```

  Fechamento completo é o caminho que a avaliação anterior sugeriu e que não foi
  tomado: aceitar `[^"'\s]{8,}` no regex e mover a proteção contra placeholder para
  uma `[rules.allowlist]` com `regexTarget = "match"` e padrões `^\$\{`, `^\{\{`,
  `^<`, `^\[`, `^%\(`. Sem lookahead no RE2, é a forma correta de expressar
  "descarte placeholder" sem furar o valor real.
- **As três regras continuam sem teste automatizado.** Um `pytest` que rode
  `gitleaks detect --no-git` sobre um diretório de sondas sintéticas (o que fiz à
  mão em §6) travaria a regressão. Esta é a segunda avaliação seguida em que uma
  lacuna de regex é achada por sonda manual — é o sinal clássico de teste faltando.
- **O binário do `gitleaks` é baixado sem verificação de integridade**
  (`ci.yml:54-55`: `curl … | tar -xz`). A versão está pinada, mas tag de release é
  mutável. Para um step cuja função é segurança, conferir o `sha256` publicado são
  três linhas.
- **`make hooks` precisa virar passo obrigatório do setup.** `pre-commit install`
  altera `.git/hooks/`, que não é versionado; sem ele a ponta local do AC-3 é
  opcional na prática. O alvo já existe (`Makefile:299`); falta o README e o
  `docs/setup.md` mandarem rodá-lo.

## 6. Comandos rodados + saídas reais

```text
# --- branch e ancestralidade (Passo 2) ---
$ git rev-parse --short HEAD
da08121
$ git merge-base --is-ancestor b9cb561e6c4dd3f0c63fd1f171dfe15496d3d88d HEAD  → ANCESTRAL
$ git merge-base --is-ancestor 721f0f0892b3298964b04b917e3f1b0cb5a1cc69 HEAD  → ANCESTRAL

# --- O BLOQUEANTE 3.1: o gate declarado da fase, rodado por mim ---
$ pre-commit run --all-files
ruff (legacy alias)......................................................Passed
ruff format..............................................................Passed
Detect hardcoded secrets.................................................Passed
trim trailing whitespace.................................................Passed
fix end of files.........................................................Passed
check yaml...............................................................Passed
check for merge conflicts................................................Passed
check for added large files..............................................Passed
don't commit to branch...................................................Passed
>>> EXIT=0
$ git status --porcelain | wc -l
0                                        ← nenhum arquivo tocado pelos hooks ✓

# idem com RUFF_CACHE_DIR sobreposto (a "nota de ambiente" do relatório):
$ RUFF_CACHE_DIR=<tmp> pre-commit run --all-files    → todos Passed, EXIT=0
   # o `.ruff_cache` com subpastas de root NÃO reproduz nesta máquina; o gate passa
   # nas duas formas.

# --- o commit `style:` é mesmo puramente mecânico? ---
$ git diff --ignore-all-space --ignore-blank-lines --stat 7497e63^ 7497e63
                                         ← vazio: zero linhas de lógica em 15 arquivos ✓

# --- IMPORTANTE 4.3: a lacuna do regex, sonda própria FORA do repositório ---
#   Valores sintéticos inventados por mim; nenhum arquivo do projeto tocado. Descrevo
#   a FORMA de cada caso em vez de colar o literal — este documento é varrido pelo
#   próprio hook, e colar os literais faria o gate reprovar o commit desta avaliação
#   (aconteceu na primeira tentativa; a saída abaixo é a da sonda, não deste arquivo).
$ gitleaks detect --no-git --source <scratchpad>/probe --config <repo>/.gitleaks.toml \
    --redact --no-banner --report-format json --report-path /dev/stdout
probe.py:1   caloria-senha-hardcoded    ← senha de 14 chars com `$` no MEIO       ✓ (era o furo)
probe.py:2   caloria-senha-hardcoded    ← senha alfanumérica de 10 chars
probe.py:3   caloria-senha-hardcoded    ← senha com `{` e `}` no meio             ✓
probe.py:4   caloria-senha-hardcoded    ← senha com `[` e `]` no meio             ✓
probe.py:5   caloria-senha-hardcoded    ← senha com `<` e `>` no meio             ✓
probe.py:11  caloria-email-pessoal      ← e-mail sintético de provedor de consumo
probe.spec.ts:1 caloria-senha-preenchida-em-teste ← `.fill()` com `$` no meio     ✓
probe.spec.ts:5 caloria-senha-preenchida-em-teste ← `.fill()` com `{ }` no meio   ✓
   # NÃO acusados, corretamente: interpolação `${…}`, placeholder `<…>`, moustache
   #   `{{…}}`, `[REDIGIDO]`, formato `%(…)s`, e os dois valores das allowlists
   #   nominais (a senha errada do teste de rejeição e a do cadastro descartável)
>>> EXIT=1                                       ← o gate bloqueia ✓

# --- e o que ainda escapa (§5) ---
probe2.py:1  senha cujo valor COMEÇA por `$`   → não acusado
probe2.py:2  senha cujo valor COMEÇA por `%`   → não acusado
probe2.py:3  senha com espaços no valor        → acusado (falso positivo novo)

# --- o comando exato do step do CI, sobre o repositório real ---
$ gitleaks detect --source . --config .gitleaks.toml --redact --no-banner --exit-code 1
INF 422 commits scanned.
INF scan completed in 14.3s
INF no leaks found
>>> EXIT=0                                       ← sem regressão no repo real ✓

# --- CI verde no HEAD atual, confirmado na fonte ---
$ gh run list --limit 3 --json databaseId,headSha,conclusion,workflowName
{"conclusion":"success","databaseId":30757473846,"headSha":"da081216…","workflowName":"CI"}
{"conclusion":"success","databaseId":30751992281,"headSha":"7bb06aab…","workflowName":"CI"}
{"conclusion":"failure","databaseId":30751605926,"headSha":"b58e8eec…","workflowName":"CI"}
   # a run mais recente cobre os commits do rework (style + regex + docs)  ✓

# --- registro do escopo (IMPORTANTE 4.1) e do AC-2 (IMPORTANTE 4.2) ---
$ sed -n '585,593p' .codeflow/specs/002-*/SPEC_002_*.md
- **Arquivos novos:** `.gitleaks.toml`.
  > **Escopo corrigido (2026-08-02).** … Sem o arquivo, a A.3 entregaria um
  > scanner que não detectaria o incidente que criou o Track A. Ver
  > `.codeflow/decisions/2026-08-02-regras-proprias-gitleaks.md` e OQ8.
$ grep -n 'config .gitleaks.toml\|-S.<valor da credencial>' .codeflow/specs/002-*/SPEC_002_*.md
313:  (`gitleaks detect --config .gitleaks.toml --log-opts="--all"`) *e* **(b)** a
315:  `git log --all -S'<valor da credencial>' --oneline | wc -l`, *então* **(a)**
324:  > independentes — a varredura com `--config .gitleaks.toml` e a busca literal por
556:- **Testes (AC-2):** `gitleaks detect --config .gitleaks.toml --log-opts="--all"`
557:  com zero achados **e** `git log --all -S'<valor da credencial>' --oneline | wc -l`
   # o AC-2 (§3) e o bullet Testes da A.2 (§5) passaram a exigir as duas
   # verificações conjuntas — fecha o IMPORTANTE 4.2                         ✓

# --- demais gates do projeto ---
$ backend/.venv/bin/python -m ruff check .          → All checks passed!
$ backend/.venv/bin/python -m ruff format --check . → 119 files already formatted
$ backend/.venv/bin/python -m mypy app/             → Success: no issues found in 72 source files
$ backend/.venv/bin/python -m pytest tests/unit/ -q → 199 passed in 2.73s
$ cd frontend && npm test                           → 17 suites, 100 passed
$ cd frontend && npm run lint                       → 1 Warning pré-existente; exit 0
$ cd frontend && npx tsc --noEmit                   → exit 0

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
| Passo 1 — hook `gitleaks` no `.pre-commit-config.yaml` | Atendido (`.pre-commit-config.yaml:17-20`) |
| Passo 2 — step bloqueante no job `backend` do `ci.yml` | Atendido (`ci.yml:51-61`) |
| Passo 3 — `SECURITY.md` atualizado | Atendido, e declara também o que o gate não cobre |
| Testes (AC-3) — hook rejeita; CI falha; `pre-commit run --all-files` verde | **Atendido nas três pontas nesta tentativa** |
| Gate — AC-3 satisfeito | Atendido |
| Gate — `pre-commit run --all-files` verde | **Atendido** (EXIT=0, árvore intocada) |
| Gate — CI verde | Atendido (run `#30757473846`, sobre o HEAD atual) |
| Elegibilidade — "Depende de: A.2, B.2" | Violada na execução original; hoje ponto morto — A.2 e B.2 aprovadas nesta rodada |
| DoD global — decisão de escopo registrada em §8 ou decision | **Atendido nesta tentativa** (OQ8 + decision) |

## 8. Divergências entre o relatório e o código real

1. **A afirmação "sonda de 12 casos, 12/12 corretos" é verdadeira para os 12 casos
   listados, mas não estabelece o que sugere.** Nenhum dos 12 cobre senha cujo
   *primeiro* caractere é um dos excluídos, que é justamente o resíduo da §5. Não é
   afirmação falsa; é cobertura de sonda menor do que a conclusão implícita. Reproduzi
   os 12 e todos conferem.

2. **A "nota de ambiente" sobre `backend/.ruff_cache/` não reproduz aqui.**
   `pre-commit run --all-files` passa com e sem `RUFF_CACHE_DIR`. Não muda nada: a
   nota está corretamente marcada como ambiente, não como código.

3. **O `range` foi corrigido e resolve**, mas cobre as cinco fases do lote. Os
   commits de código desta fase são `4b36c5b`, `ca005ed`, `b58e8ee` e, no rework,
   `7497e63` + `a6f879e`.

4. **Registro herdado, não corrigido:** a §5.1 do relatório continua apresentando
   `pre-commit run gitleaks --all-files` como "verde no repositório limpo". Com o
   índice limpo, `gitleaks protect --staged` não varre nada e passa por construção.
   A evidência que vale é a §5.2, com arquivo estagiado de verdade, e essa é sólida.
   Era sugestão de redação na avaliação anterior e assim permanece.
