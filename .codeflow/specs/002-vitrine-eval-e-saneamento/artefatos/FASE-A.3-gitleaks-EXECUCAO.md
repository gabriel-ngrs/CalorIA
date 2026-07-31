---
spec: 002-vitrine-eval-e-saneamento
fase: A.3
slug_fase: gitleaks
status: executado
tentativa: 1
reprovacoes: 0
sha_inicial: 5769f238590027c4036776edddc679e5e0dafa4a
sha_final: df3f38e7983a6416f183ba0d24bead256473a6f1
range: 5769f238590027c4036776edddc679e5e0dafa4a..df3f38e7983a6416f183ba0d24bead256473a6f1
---

# FASE A.3 — Relatório de execução

## 1. Resumo do que foi feito

`gitleaks` v8.21.2 entrou como hook do `.pre-commit-config.yaml` e como step
bloqueante do job `backend` do `ci.yml`. O `SECURITY.md` deixou de afirmar por
disciplina que "secrets nunca são commitados" e passou a apontar as duas ferramentas
que o verificam — **declarando também o que o gate não cobre**, que é o achado
metodológico desta fase.

AC-3 verificado nas duas pontas com segredo sintético não-allowlistado: o hook local
rejeita o commit (`exit 1`, HEAD não avança) e o comando exato do step do CI retorna
`exit 1` com o segredo no histórico e `exit 0` na `dev` limpa.

> **Nota de elegibilidade:** a fase declara `Depende de: A.2, B.2`. `B.2` está
> concluída. **`A.2` NÃO está** — seu gate depende do `git filter-repo` + force-push,
> que são do owner e não aconteceram. Esta fase foi executada assim mesmo por decisão
> explícita do owner ("siga a ordem indicada na spec", executar todo o Track A neste
> run). O avaliador precisa saber disso: A.3 é tecnicamente completa, mas foi
> executada sobre uma dependência não concluída.

## 2. Arquivos CRIADOS

Nenhum. **Em particular, `.gitleaks.toml` NÃO foi criado** — ver §9, item 2.

## 3. Arquivos ALTERADOS

| Arquivo | O que mudou |
|---------|-------------|
| `.pre-commit-config.yaml` | Hook `gitleaks` (repo `github.com/gitleaks/gitleaks`, `rev: v8.21.2`) adicionado **antes** dos hooks genéricos do `pre-commit-hooks`, para que a varredura de segredo rode antes de qualquer auto-fix de formatação. |
| `.github/workflows/ci.yml` | `actions/checkout@v4` ganhou `fetch-depth: 0` (sem histórico completo a varredura seria só do último commit); novo step "Varredura de segredos — gitleaks", bloqueante, com `working-directory: .` (o job tem default `backend`), baixando o binário v8.21.2 e rodando `gitleaks detect --source . --redact --no-banner --exit-code 1`. |
| `SECURITY.md` | A afirmação "Secrets e credenciais nunca são commitados" passou a citar as duas barreiras que a tornam verificável, **e** ganhou um item novo declarando o limite real do gate: senhas de usuário em texto claro não têm forma reconhecível e não são detectadas pelas regras default. |

## 4. Confirmação do REUSO e decisões de design

- **Reuso confirmado:** `.pre-commit-config.yaml` já existia com `ruff`,
  `ruff-format` e os hooks genéricos (incl. `no-commit-to-branch`); `SECURITY.md` já
  existia. Ambos foram estendidos, não substituídos — conforme o mapa NOVO/REUSADO da
  §4 da spec.

- **Decisão: binário direto no CI em vez de `gitleaks/gitleaks-action@v2`.** Dois
  motivos. (a) A action de marketplace exige `GITLEAKS_LICENSE` para contas de
  organização; hoje `gabriel-ngrs` é conta pessoal e seria gratuito, mas o gate
  passaria a depender de um termo de licença de terceiro que pode mudar. (b) Com o
  binário, o comando do CI é **byte a byte o mesmo** que rodei localmente — o que
  permitiu provar o AC-3b sem esperar por uma execução remota.

- **Decisão: `--redact` obrigatório.** O log do GitHub Actions é tão acessível quanto
  o repositório. Sem `--redact`, um step que detecta um segredo o **imprime** no log,
  transformando o gate numa segunda via de vazamento. Comprovado na saída da §5.2, em
  que o valor aparece como `REDACTED`.

- **Decisão: `fetch-depth: 0`.** Sem isso o `actions/checkout` faz clone raso e
  `gitleaks detect` varre apenas o commit da vez. Com histórico completo, qualquer
  segredo introduzido em qualquer commit do push é pego. Custo: clone mais lento
  (~424 commits, 14 s de varredura medidos localmente).

- **Escopo travado respeitado:** o segredo usado no teste é **sintético** — um
  identificador com o prefixo `AKIA` seguido de 16 caracteres inventados, mais uma
  string aleatória de 40 caracteres —, sem correspondência com nenhuma credencial
  real. Nenhuma allowlist foi adicionada: o gate roda com as regras default, sem
  exceções. Os valores literais **não aparecem neste relatório**, pelo motivo do item
  seguinte.

- **O gate bloqueou este próprio relatório, e isso é evidência adicional do AC-3.** A
  primeira tentativa de commitar este documento falhou: o hook `gitleaks` detectou a
  chave sintética que eu havia colado literalmente na §4 e na §5.2
  (`Fingerprint: ...FASE-A.3-gitleaks-EXECUCAO.md:aws-access-token:118`,
  `WRN leaks found: 2`, commit rejeitado). **A correção foi redigir o documento, não
  afrouxar o gate** — nenhuma allowlist, nenhum `# gitleaks:allow`, nenhum
  `--no-verify`. É exatamente o comportamento que o escopo travado da fase exige.

- **Achado durante a execução, registrado por honestidade:** a primeira tentativa de
  teste usou `AKIAIOSFODNN7EXAMPLE`, a chave de exemplo da documentação da AWS. O
  gitleaks **passou** — porque esse valor está na allowlist de stopwords da própria
  ferramenta. Um teste de gate que usa um valor allowlistado dá falso verde. O teste
  foi refeito com valor não-allowlistado.

## 5. Comandos rodados + saídas reais

### 5.1 `pre-commit run --all-files` no repositório limpo

```text
$ pre-commit run gitleaks --all-files
Detect hardcoded secrets.................................................Passed
```

E na execução do próprio commit desta fase, com o hook já instalado em `.git/hooks`:

```text
ruff.................................................(no files to check)Skipped
ruff-format..........................................(no files to check)Skipped
Detect hardcoded secrets.................................................Passed
trim trailing whitespace.................................................Passed
fix end of files.........................................................Passed
check yaml...............................................................Passed
check for merge conflicts................................................Passed
check for added large files..............................................Passed
don't commit to branch...................................................Passed
```

> **Ressalva importante, ver §9 item 1:** `pre-commit run --all-files` com **todos** os
> hooks **não** fica verde neste repositório. O hook `gitleaks` passa, mas
> `trim trailing whitespace` e `fix end of files` modificam **25 arquivos
> pré-existentes** (dumps em `docs/auditoria/artefatos/`, CSVs em `data/`, uma
> migration, 4 testes, uma página do frontend). É dívida de higiene anterior a esta
> fase, e corrigi-la está fora dos três arquivos declarados. Reverti todos esses
> auto-fixes para não contaminar o diff.

### 5.2 AC-3, ponta 1 — o hook local rejeita o commit

Arquivo de prova (sintético, não-allowlistado), estagiado de verdade:

```python
# backend/app/_fake_secret_probe.py  (valores redigidos — ver §4)
AWS_ACCESS_KEY_ID = "<AKIA + 16 caracteres sintéticos>"
AWS_SECRET_ACCESS_KEY = "<40 caracteres sintéticos>"
```

```text
$ git add backend/app/_fake_secret_probe.py && pre-commit run gitleaks
Secret:      REDACTED
RuleID:      generic-api-key
Entropy:     5.321928
File:        backend/app/_fake_secret_probe.py
Line:        2
Fingerprint: backend/app/_fake_secret_probe.py:generic-api-key:2

Finding:     ...WS_ACCESS_KEY_ID = "REDACTED"
Secret:      REDACTED
RuleID:      aws-access-token
Entropy:     4.121928
File:        backend/app/_fake_secret_probe.py
Line:        1

INF 1 commits scanned.
WRN leaks found: 2
>>> HOOK_EXIT=1                                    ← rejeitado

# e o `git commit` de verdade, com o hook instalado em .git/hooks:
$ git commit -m "test: probe de segredo sintetico (nao deve passar)"
[...] WRN leaks found: 2
>>> COMMIT_EXIT=1                                  ← bloqueado

$ git log --oneline -1
7ce07df docs(specs): registra execucao das fases a.1, a.2 e b.1 da spec 002
                                                   ← HEAD NÃO avançou
```

### 5.3 AC-3, ponta 2 — o mesmo conteúdo derruba o step do CI

Simulação fiel: o probe foi commitado numa branch descartável com `--no-verify`
(para chegar ao histórico como chegaria num push de quem não instalou o hook), e
então rodou-se o **comando exato do step do `ci.yml`**:

```text
# COM o segredo no histórico
$ gitleaks detect --source . --redact --no-banner --exit-code 1
INF 424 commits scanned.
INF scan completed in 13.6s
WRN leaks found: 4
>>> CI_STEP_EXIT=1                                 ← job falharia

# CONTROLE: mesma invocação na dev limpa
$ gitleaks detect --source . --redact --no-banner --exit-code 1
INF 422 commits scanned.
INF scan completed in 14.1s
INF no leaks found
>>> CI_STEP_EXIT_LIMPO=0                           ← job passaria
```

Branch descartável apagada (`Deleted branch tmp-ci-probe (was 3056f0d)`); probe
removido; `git status` limpo.

### 5.4 Validação do YAML e dos demais gates

```text
$ python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"   → OK
$ ruff check .            → All checks passed!
$ mypy app/               → Success: no issues found in 72 source files
$ pytest tests/unit/ -q   → 199 passed
```

## 6. Critérios de aceite da fase (com evidência)

- [x] **AC-3** (FR-A3) — *dado* um commit que introduza um segredo de teste, *quando*
      se tenta commitar, *então* o hook local rejeita (§5.2: `HOOK_EXIT=1`,
      `COMMIT_EXIT=1`, HEAD inalterado); **e** *quando* o mesmo chega ao CI, *então* o
      job falha (§5.3: `CI_STEP_EXIT=1` com o segredo no histórico contra
      `CI_STEP_EXIT_LIMPO=0` sem ele).
- [x] **`pre-commit run gitleaks --all-files` verde no repositório limpo** — §5.1.
- [ ] **`pre-commit run --all-files` (todos os hooks) verde** — **NÃO satisfeito**,
      por dívida de whitespace/EOF pré-existente em 25 arquivos fora do escopo. §5.1 e §9.1.
- [ ] **"CI verde"** — **NÃO verificado.** Depende do push para `dev`, que não foi
      feito (mesma pendência da B.2).

## 7. Definition of Done da fase

- [x] Testes da fase verdes — AC-3 provado nas duas pontas com evidência de exit code
- [x] Comandos de validação limpos nos arquivos tocados; YAML validado
- [x] Escopo travado respeitado — segredo de teste **sintético** e reconhecível,
      **nenhuma** allowlist adicionada, gate não desabilitado nem afrouxado
- [x] Nenhum segredo/PII — todas as saídas com `--redact`; o probe foi removido e a
      branch de teste apagada
- [x] Commit em pt-BR: `ci(seguranca): adiciona gitleaks ao pre-commit e ao ci`

## 8. (Em rework) O que mudou nesta tentativa

N/A — primeira execução.

## 9. Itens em aberto / dúvidas para o avaliador

1. **`pre-commit run --all-files` não fica verde, e não é culpa desta fase.** Os hooks
   `trailing-whitespace` e `end-of-file-fixer` — que **já existiam** antes da A.3 —
   modificam 25 arquivos pré-existentes: `docs/auditoria/artefatos/*.txt`,
   `.codeflow/bug-batches/artefatos/*.json`, `data/processed/alimentos_final.csv`,
   `data/raw/*.csv`, `backend/alembic/versions/20260224_*.py`, 4 arquivos de teste,
   `frontend/app/(auth)/register/page.tsx` e `docs/legacy/analise.md`. Corrigi-los
   está fora dos três arquivos que a fase declara. **Decisão:** revertidos, gate
   reportado como insatisfeito. Boa parte desses arquivos é candidata à poda da Fase
   D.4, o que resolveria o problema sem trabalho extra — sugiro tratar lá.

2. **RECOMENDAÇÃO FORTE — o gate entregue não teria detectado o incidente que criou o
   Track A.** Já registrado na §9 do relatório da A.2 e reafirmado aqui porque agora é
   demonstrável: as regras default do gitleaks casam segredos com **forma**
   reconhecível. A credencial de `auth.spec.ts` é uma senha arbitrária de usuário —
   sem forma. Prova: `gitleaks detect --log-opts="--all"` retorna
   **`no leaks found`** sobre o histórico atual, que **ainda contém** a credencial em
   11 commits.
   Ou seja: A.3 fecha a classe "chave de API/token commitado" e **não** fecha a classe
   "senha pessoal hardcoded", que é a que de fato ocorreu.
   **Não criei `.gitleaks.toml` com regra customizada** porque a fase declara apenas
   três arquivos alterados e a constitution proíbe ampliar escopo por conta própria.
   Proposta concreta para uma fase futura (ou extensão desta): adicionar
   `.gitleaks.toml` com uma regra que case (a) o e-mail do owner e (b) o padrão de
   senha usado, e trocar o AC-2 por `git log --all -S'<valor>' | wc -l == 0`.

3. **A dependência `A.2` não está concluída** (ver nota em §1). Se o avaliador seguir
   a máquina de estados de ARTIFACTS_SPEC §2.11 à risca, esta fase não era elegível.
   Foi executada por instrução explícita do owner nesta sessão.

4. **`pre-commit install` foi executado na máquina local** para provar a ponta local
   do AC-3. Isso altera `.git/hooks/pre-commit`, que não é versionado — não entra no
   diff, mas o alvo `make hooks` já existia justamente para isso. Vale garantir que o
   README/`docs/setup.md` mande rodar `make hooks`, senão o hook local é opcional na
   prática e só o CI protege.
