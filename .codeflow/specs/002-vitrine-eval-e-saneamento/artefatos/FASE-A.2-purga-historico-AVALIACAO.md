---
spec: 002-vitrine-eval-e-saneamento
fase: A.2
slug_fase: purga-historico
tentativa: 1
veredito: RESSALVAS
score: 9.2
threshold: 8.5
range_avaliado: 240d708..c69fbfb (reconstruído — ver §8)
---

# FASE A.2 — Avaliação independente

## 1. Veredito e score

**Veredito:** RESSALVAS · **Score:** 9.2 / threshold 8.5

Zero BLOQUEANTES: a purga funcionou e eu a verifiquei de forma independente, sem
depender das saídas do relatório. As ressalvas são de **rastreabilidade**, não de
segurança — duas decisões que alteraram materialmente o escopo e os passos da fase
vivem apenas no relatório de execução, quando a DoD global da spec exige que
estejam na §8 ou numa decision do framework.

Registro o que mais me impressionou, porque conta para a nota: o relatório encontrou
e denunciou que o **AC-2, como escrito na spec, era um gate falso** — `gitleaks` com
regras default retornava `no leaks found` sobre um histórico contaminado. Achar que
o próprio critério de aceite não media nada é exatamente o que um executor cético
deveria fazer, e é raro.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 4 | AC-2 ✓ nas duas partes (§6); escopo travado respeitado — `filter-repo` e force-push **não** executados pelo agente, nenhum achado apagado, nenhuma migration ou código de produção tocado (`git diff --stat` da fase: só `.md`/`.txt`). Desconto: escopo estendido de 2 → 10 arquivos sem atualizar a §5 da spec (§4.1) |
| 2 | Arquitetura e direção de dependências | 3 | 5 | Fase documental. O plano da §5.4 é bem construído: backup espelho antes, clone fresco, `replacements.txt` fora de qualquer repo e destruído depois |
| 3 | Segurança / LGPD / multi-tenant | 3 | 4 | Purga verificada por mim: 0 ocorrências em `dev`/`main`/`test` e em `--all` (§6). Descontos: ticket ao GitHub Support omitido (§4.2) e `07-seguranca.md:210` ainda revela comprimento e classe de caracteres da senha (§5) |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | `--replace-text` em vez de `--path --invert-paths` — decisão certa e justificada: preserva os arquivos no histórico, remove só o valor (`EXECUCAO.md:80-84`) |
| 5 | Padrões de domínio/aplicação | 2 | 5 | Redação por placeholder consistente (`<e-mail pessoal do mantenedor>`, `[REDIGIDO]`) em todos os 10 arquivos |
| 6 | Local e nomes dos arquivos | 2 | 5 | Todos os arquivos tocados são de `docs/auditoria/` + `docs/legacy/analise.md`; nada fora de `docs/` |
| 7 | Qualidade de código | 2 | 5 | Diff cirúrgico: `git diff --numstat` → 7/7 e 3/3 nos dois arquivos originais; nenhuma seção apagada; AUD-038 íntegro com os três vetores de risco |
| 8 | Testes e cobertura | 2 | 4 | Não há teste aplicável a markdown; a verificação é por `git log -S` + `gitleaks`, e ambas foram reproduzidas por mim. Desconto: a suíte não foi re-rodada após a reescrita, como os "Testes" da §5 pediam |
| 9 | Migration safety | 2 | [—] | Nenhuma migration tocada (NFR-7) |

Score = (3·4 + 3·5 + 3·4 + 3·5 + 2·5 + 2·5 + 2·5 + 2·4) / 20 · 2 = **9.2**

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

### 4.1 — Extensão de escopo de 2 para 10 arquivos nunca chegou à spec nem a uma decision

**Onde:** `FASE-A.2-purga-historico-EXECUCAO.md:45-68` (§3.1) vs. spec §5, Fase A.2
("**Arquivos alterados:** `docs/auditoria/achados.md`, `docs/auditoria/log.md`") e
spec §9, item global "Toda decisão de escopo tomada durante a execução está
registrada aqui em §8 ou numa decision do framework".

**O que aconteceu.** A credencial vivia em mais 8 arquivos, dois deles publicando o
comando de extração. O executor **parou e reportou antes de agir**, como a
constitution manda, e o owner autorizou. O processo foi correto. O que faltou é o
registro no lugar que a spec designa:

```text
$ git log --oneline 461ee38..HEAD -- .codeflow/specs/.../SPEC_002_*.md
9dfeef9 docs(specs): registra execucao das fases a.1, a.2 e b.1 da spec 002
$ git show 9dfeef9 -- .../SPEC_002_*.md | grep -c '^[+-].*achados.md'
0            # o commit só trocou `status: draft`→`active` e `updated_at`
$ ls .codeflow/decisions/
2026-07-02-lote-bugs-teste-v1.md   2026-07-03-baseline-lint-mypy.md
2026-07-07-lote-bugs-incidentais-v1.md   2026-07-26-limiares-lookup-nutricional.md
             # nenhuma decision sobre esta spec
```

**Cenário de falha concreto.** Um avaliador (ou um rework) que leia a §5 da spec e o
diff da fase encontra 8 arquivos alterados fora da lista declarada e, sem o relatório
em mãos, lê isso como violação de escopo BLOQUEANTE. O próprio executor previu
exatamente isso (`EXECUCAO.md:464-465`: *"Sugiro atualizar a §5 da spec … senão o
avaliador vai ler o diff como violação de escopo"*) — e a sugestão não foi aplicada.

**Correção sugerida:** atualizar a lista "Arquivos alterados" da Fase A.2 na §5 da
spec para os 10 arquivos reais, e registrar a extensão como item da §8. Alternativa
equivalente: uma decision em `.codeflow/decisions/`.

### 4.2 — O passo 3 da fase (ticket ao GitHub Support) foi omitido por decisão verbal

**Onde:** spec §5, Fase A.2, passo 3 ("*solicitar ao GitHub Support a invalidação do
cache de commits órfãos*") vs. `FASE-A.2-purga-historico-EXECUCAO.md:433-450` (§9,
item 1).

**O defeito.** A fundamentação do owner é sólida e eu a verifiquei
(`forkCount: 0`, `visibility: PRIVATE`, senha rotacionada nos serviços de reuso), e
o passo não consta do "Critério de conclusão" da fase — por isso é IMPORTANTE e não
BLOQUEANTE. Mas continua sendo um passo declarado da §5 que não aconteceu, e o
risco residual **é reconhecido no próprio relatório**: na Fase D.2 o repositório
volta a ser público, e objetos órfãos podem voltar a ser alcançáveis por SHA se o GC
do GitHub não tiver rodado. A mitigação combinada ("deixar passar alguns dias") é um
acordo verbal, sem prazo verificável nem gate na D.2.

**Correção sugerida:** registrar a omissão e a mitigação como item da §8 da spec, com
uma pré-condição explícita na Fase D.2 — por exemplo, verificar que os SHAs
pré-purga listados em `EXECUCAO.md:257` retornam 404 **antes** de tornar o
repositório público.

### 4.3 — O `range` do frontmatter não é reconstruível

**Onde:** `FASE-A.2-purga-historico-EXECUCAO.md:8-10`.

```text
$ git merge-base --is-ancestor cb2e4ca7bd7323123ab4196d5f5906ff06dda7be HEAD
   → NÃO-ancestral   (sha pré-purga)
```

E o `sha_final` `7bb06aab`, atualizado no commit `95c6c8c`, é o commit da **Fase
B.2**, não desta fase. Os commits reais da A.2 são `fd923d6` (redação dos dois
documentos) e `c69fbfb` (extensão aos outros 8). O Passo 2 do protocolo de avaliação
manda PARAR quando o range não é ancestral de HEAD; segui apenas porque a causa é
conhecida e documentada — a própria fase reescreveu o histórico.

**Correção sugerida:** `range: 240d708..c69fbfb`.

## 5. Sugestões

- **`docs/auditoria/07-seguranca.md:210` ainda descreve a senha.** O texto
  preservado diz que `[REDIGIDO]` tem "8 chars + especiais". O valor saiu, mas o
  comprimento e a classe de caracteres ficaram — é metadado de senha rotacionada,
  risco hoje nulo, mas o padrão de redação da fase seria mais consistente sem isso.
- **`docs/auditoria/artefatos/G1-creds.txt`** continua sendo um dump cujo propósito
  era listar segredos, agora redigido. Concordo com o executor: podar na Fase D.4 é
  melhor que mantê-lo redigido para sempre. Efeito colateral bônus: some junto com
  a dívida de whitespace que hoje trava o gate da A.3 (ver a avaliação daquela fase).
- **Placeholder aninhado em `G1-creds.txt:9-14`** produz `Author: Gabriel
  <<e-mail pessoal do mantenedor>>` (chevron duplo). Cosmético; some com a poda.
- **`--replace-text` não toca metadados de commit.** O e-mail do owner segue como
  `author.email` de todos os commits — confirmado por mim (`git log --all
  --format='%ae' | sort -u` → 1 endereço). É decisão consciente do owner, registrada
  em `EXECUCAO.md:472-480`, e e-mail de autor é público por padrão no GitHub. Sem
  ação recomendada, só registro para que ninguém "descubra" isso depois como surpresa.

## 6. Comandos rodados + saídas reais

```text
# --- AC-2, parte 1: varredura de segredos sobre o histórico, comando exato do CI ---
$ gitleaks detect --source . --config .gitleaks.toml --redact --no-banner --exit-code 1
INF 416 commits scanned.
INF scan completed in 17.3s
INF no leaks found
>>> EXIT=0                                                                 ✓

# --- verificação direta, que não depende de heurística (valores redigidos) ---
$ git log dev main test --oneline -S'<e-mail-do-owner>' | wc -l
0                                            # era 12 antes da purga         ✓
$ git log --all --oneline -S'<e-mail-do-owner>' | wc -l
0                                                                            ✓
$ grep -rIl '<e-mail-do-owner>' --exclude-dir=.git --exclude-dir=node_modules \
    --exclude-dir=.next --exclude-dir=.venv . | wc -l
0                                                                            ✓

# --- AC-2, parte 2: achados.md sem PII e sem comando de extração ---
$ git diff 461ee38..HEAD -- docs/auditoria/achados.md | grep -c '^+.*git log -p'
0
# e o achado sobrevive: AUD-038 íntegro com severidade, arquivo:linha, commit de
# origem `4737257`, os três vetores de risco e o plano de remediação em 4 etapas.

# --- diff cirúrgico, nenhuma seção apagada ---
$ git diff --stat 461ee38..HEAD -- docs/
 docs/auditoria/07-seguranca.md          | 12 +++---
 docs/auditoria/08-testes.md             |  2 +-
 docs/auditoria/achados.md               | 14 +++----
 docs/auditoria/artefatos/G1-creds.txt   | 24 +++++++-------
 docs/auditoria/log.md                   |  6 ++---
 docs/auditoria/plano-correcao.md        |  4 +--
 docs/auditoria/plano.md                 |  2 +-
 docs/auditoria/relatorio-preliminar.md  |  2 +-
 docs/auditoria/runbook.md               | 14 +++----
 docs/legacy/analise.md                  |  8 ++---
              # 10 arquivos — os 2 declarados + os 8 da extensão da §3.1

# --- escopo travado: nada de código, nada de migration ---
$ git diff --name-only 240d708..c69fbfb -- backend/app backend/alembic frontend/ | wc -l
0                                                                            ✓

# --- Dependabot: branches órfãs removidas ---
$ git ls-remote --heads origin | awk '{print $2}'
refs/heads/dev
refs/heads/main
refs/heads/test                              # nenhuma dependabot/*          ✓

# --- fundamentação da omissão do ticket ao Support, reverificada ---
$ gh repo view gabriel-ngrs/CalorIA --json visibility,isPrivate,forkCount
{"forkCount":0,"isPrivate":true,"visibility":"PRIVATE"}

# --- gates do projeto na ponta da branch (a fase é documental; [—] justificado,
#     rodados mesmo assim para provar que a reescrita não quebrou nada) ---
$ backend/.venv/bin/python -m ruff check .          → All checks passed!
$ backend/.venv/bin/python -m ruff format --check . → 119 files already formatted
$ backend/.venv/bin/python -m mypy app/             → Success: no issues found in 72 source files
$ backend/.venv/bin/python -m pytest tests/unit/ -q → 199 passed in 3.03s
$ cd frontend && npm test                           → 17 suites, 100 passed

# --- árvore limpa ao final ---
$ git status --porcelain | wc -l
0
```

## 7. Itens da fase / DoD não atendidos

| Item (§5 / §9 da spec) | Estado |
|---|---|
| Passo 1 — reescrever `achados.md` e `log.md` | Atendido |
| Passo 2 — preparar e documentar o comando de `filter-repo` + plano de force-push + plano do Dependabot | Atendido (§5.4 e §5.5 do EXECUCAO) |
| Passo 3 — owner executa `filter-repo` + force-push | Atendido (§5.7) |
| Passo 3 — solicitar invalidação de cache ao GitHub Support | **NÃO ATENDIDO** — omissão deliberada (§4.2) |
| Passo 4 — varredura sobre todo o histórico sem achados | Atendido, verificado por mim |
| Testes — "suíte completa verde após a reescrita" | **PARCIAL** — não consta do relatório; rodei por conta própria e está verde (§6) |
| Gate — documentos reescritos, PRs do Dependabot tratados | Atendido (9 PRs fechados, 9 branches removidas) |
| DoD global — decisão de escopo registrada em §8 ou decision | **NÃO ATENDIDO** (§4.1, §4.2) |

## 8. Divergências entre o relatório e o código real

1. **Nenhuma divergência substantiva.** Reproduzi as três medições centrais do
   relatório (gitleaks sobre o histórico, `git log -S` nas três refs, grep do working
   tree) e todas batem. O relatório é conservador: declara `[—]` onde não rodou gate
   e marca como "linha de base, não aprovação" a verificação feita antes do passo do
   owner.

2. **`range` inconsistente** (§4.3) — `sha_inicial` pré-purga inalcançável e
   `sha_final` apontando para o commit da Fase B.2.

3. **Um 11º arquivo foi redigido, mas não pela fase.** §5.7 registra que o
   `filter-repo` alcançou uma ocorrência da senha em `docs/auditoria/09-qualidade.md`
   que as duas rodadas manuais de redação não tinham pego. Confirmei que esse arquivo
   **não** aparece no diff dos commits da fase (`git diff --stat 240d708..c69fbfb --
   docs/` não o lista): a redação veio da reescrita de histórico, não de um commit da
   A.2. Registrado com honestidade no relatório; anoto aqui só para que a lista de
   "10 arquivos" da §3.1 não seja lida como cobertura completa da redação manual.
