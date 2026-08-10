---
spec: 002-vitrine-eval-e-saneamento
fase: D.3
slug_fase: readme-vitrine
tentativa: 2
veredito: APROVADO
score: 9.8
threshold: 8.5
range_avaliado: 5f137f7bc6887de33131daf36586df0c3c316507..049f6e5d1764c7dd6b04af9af16f94e2d1eb873e
---

# FASE D.3 — Avaliação independente

## 1. Veredito e score

**Veredito:** APROVADO · **Score:** 9.8 / threshold 8.5

Os dois achados IMPORTANTES da tentativa 1 estão resolvidos, e eu verifiquei
cada um contra o repositório, não contra o relatório:

- **IMP-1 resolvido.** A cláusula "link da demo" tem agora registro durável e
  destino nomeado. A **OQ24** entrou na §8 no formato de OQ18/OQ20/OQ22, e o
  executor foi além do mínimo: alinhou o AC-20 (com nota de migração), o passo 1
  da D.3, o **AC-27**, a **Fase E.4** (`README.md` nos arquivos alterados, passo 6
  novo, cláusula no teste) e as duas linhas da §9. Depois que a D.4 apagar os
  `FASE-*-EXECUCAO.md`, a decisão continua no repositório e a cláusula tem dono.
- **IMP-2 resolvido.** `README.md:181-182` separa `ruff check` (pre-commit e CI)
  de `ruff format --check` (pre-commit e `make check`). Confere com `ci.yml`, que
  tem um único passo de ruff, e com `Makefile:300`.

Também aplicou as sugestões 2 e 3, e recusou 1 e 4 com a justificativa certa —
eu as havia declarado fora do escopo da D.3 e endereçadas à D.4; ampliar a fase
em rework contrariaria o protocolo. Recusar foi a decisão correta.

Zero BLOQUEANTES, zero IMPORTANTES. Restam quatro sugestões, todas de baixo
custo e nenhuma na fronteira do AC-20 — a mais relevante (a §2 FR-D3 não
alinhada) está registrada abaixo com o motivo de eu **não** a tratar como
IMPORTANTE.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 4.5 | AC-20 (texto vigente, `SPEC:408-419`) satisfeito nas cinco cláusulas: `make init` real (`/health` → `{"status":"ok","version":"0.7.0"}`, front 307 em :3010), portas conferidas em `docker-compose.dev.yml:61,99`, demo com credenciais coerentes com `SENHA_DEMO = "CalorIADemo2026!"`, 14/14 Mermaid parseados, 15 números com fonte reproduzida. Escopo travado intacto: `git diff --name-only 5f137f7..049f6e5 \| grep -E "test\|alembic\|CHANGELOG"` → vazio. Desconto: a §2 FR-D3 ainda diz "link da demo" (sugestão 1) |
| 2 | Arquitetura e direção de dependências | 3 | 5.0 | Diagramas conferem com o código (`services/ai/`, workers, arestas PG/Redis); conversão dos 9 fluxos fiel por `diff` contra os `.mermaid` antigos. A migração de cláusula respeita a direção certa: quem publica a instância (E.4) é quem cita a URL — `SPEC:440-443`, `SPEC:1380`, `SPEC:1391-1393` |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5.0 | `gitleaks detect --source . --config .gitleaks.toml` → `521 commits scanned` / `no leaks found`. Diff da tentativa 2 é markdown puro; nenhuma credencial nova. As 4 capturas seguem sendo só a conta demo com dados sintéticos |
| 4 | Reusar/espelhar, não duplicar | 3 | 5.0 | OQ24 reusa o mecanismo, não inventa: mesmo formato de OQ18 (`SPEC:1667`), OQ20 (`SPEC:1704`) e OQ22, numerada em sequência, antes da §9; a nota `> **Nota (data)**` dentro do AC copia o padrão já usado no AC-18 (`SPEC:400`) e no AC-15 (`SPEC:382`). Os três precedentes que a OQ24 cita — AC-1→AC-2 (A.1), OQ18, OQ20 — existem e dizem o que ela diz |
| 5 | Padrões de domínio/aplicação | 2 | 5.0 | 3 commits do rework em Conventional Commits pt-BR (`b2fa78d`, `049f6e5`, `a360f17`); `git log baf0c4c..a360f17 --format='%B' \| grep -iE "claude\|anthropic\|co-authored\|agente"` → vazio |
| 6 | Local e nomes dos arquivos | 2 | 5.0 | Frontmatter do rework correto pelo ARTIFACTS_SPEC §2.9.3: `status: rework`, `tentativa: 2`, `reprovacoes: 1`, `sha_inicial` **reusado** (`5f137f7`), `range` = `sha_inicial..sha_final` cobrindo a fase inteira, `sha_final` (`049f6e5`) ancestral de HEAD. Arquivo único sobrescrito, não versionado por tentativa |
| 7 | Qualidade de código | 2 | 4.5 | Diff da tentativa 2 = 2 arquivos, 59 inserções, 12 remoções, **zero linhas de código** — cirúrgico, exatamente os achados. `make lint-check` → `All checks passed!` + `149 files already formatted`; `make typecheck` → `Success: no issues found in 81 source files`. Desconto: prosa do relatório envelhecida em três pontos (§4 decisão 1, §6 e a contagem "5 commits") — ver §8 |
| 8 | Testes e cobertura | 2 | 5.0 | Nenhum arquivo de teste no range (NFR-6 e NFR-7 intactos). Reproduzi: `496 passed, 3 skipped` · `145 passed` · `118 passed / 20 suites` · `make check` exit 0. O `skip` de `TestCredenciaisPublicadas` que eu havia apontado como evidência imprecisa está agora declarado no próprio relatório (`:268-271`), que é a correção certa para uma condição herdada da E.3 |
| 9 | Migration safety (se aplicável) | 2 | [—] | Não se aplica: nenhuma migration criada ou alterada no range |

**Score:** (4.5·3 + 5.0·3 + 5.0·3 + 5.0·3 + 5.0·2 + 5.0·2 + 4.5·2 + 5.0·2) / 20 = 97.5/20 = 4.875 → **9.8/10**.

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

Nenhum.

Registro explícito de por que a lacuna que encontrei **não** é IMPORTANTE, para
que a decisão seja auditável e não pareça leniência de fim de ciclo:

A §2 **FR-D3** (`SPEC:266-268`) ainda diz que o README deve trazer "link da
demo". Está desalinhada do AC-20 que ela gera. Não é IMPORTANTE porque não cruza
nenhuma das duas linhas que eu mesmo usei para classificar os achados da
tentativa 1:

- **Não há perda durável de informação.** O motivo do IMP-1 era que a decisão
  vivia só num arquivo que o AC-21 manda a D.4 apagar. A OQ24 está na §8 da spec,
  que sobrevive à poda, e é referenciada do AC-20, do passo 1 da D.3, do AC-27,
  da Fase E.4 e das duas linhas da §9. Quem tropeçar na FR-D3 acha a explicação a
  duas seções de distância, por link explícito.
- **Não é contradição README × repositório.** O teste do AC-20
  (`SPEC:1175-1177`) cobra coerência entre o **README** e o estado do
  repositório. FR-D3 é texto de spec, não afirmação do README. O README não
  promete link nenhum — declara a ausência em `README.md:57`.

Também pesa que os três precedentes de migração desta spec não tiveram esse
alinhamento a fazer: nem FR-D1 mencionava "licença detectada pela API" (OQ18),
nem FR-C6/FR-C7 mencionavam "workflow registrado" (OQ20) ou "sem casos vazios"
(OQ21). A D.3 é o primeiro caso em que a cláusula migrada aparece **literalmente
no texto do FR** — não havia padrão a seguir. Fica como sugestão 1.

## 5. Sugestões

1. **`SPEC:266-268` (FR-D3) ainda pede "link da demo".** É o único lugar da spec
   onde a cláusula migrada sobreviveu; o relatório (§8) afirma ter alinhado
   "todos os lugares onde a cláusula aparecia", e este ficou de fora. Correção de
   uma linha: `"comando único de execução, a demo com credenciais, diagrama de
   arquitetura, e a seção de decisões técnicas com os números medidos"`, e — se
   quiser fechar o par — acrescentar o link à FR-E4 (`SPEC:283-284`), que hoje
   recebeu a cláusula no AC-27 sem tê-la no requisito de origem.

2. **A `Depende de` da E.4 não declara a D.3, e agora deveria.** O passo 6 novo
   (`SPEC:1391-1393`) manda publicar o link "ao lado das credenciais que a D.3 já
   publicou" e remover a linha de ausência que a D.3 escreveu — acoplamento real
   a uma fase que não está no grafo (`SPEC:1380`: `E.2`, `E.3`, `D.2`). As três
   dependências declaradas da E.4 estão **concluídas hoje**, então a §2.11.4 já a
   considera elegível para execução; o passo 6 pressupõe um README que só a D.3
   produz. Acrescentar `D.3` à linha `Depende de` fecha exatamente o tipo de
   buraco de modelagem que a OQ24 existe para tratar.

3. **`README.md:189` — a lista de exclusões do `make check` está incompleta.** A
   frase nova diz "fora `gitleaks` e o `next build` de produção", mas o alvo
   também não reproduz o **piso de cobertura**: `--cov-fail-under=72` só existe em
   `ci.yml:98`; `Makefile:247-253` roda `pytest tests/unit/ -v` e
   `pytest tests/integration/ -v`, sem `--cov`. Como a linha imediatamente acima
   na mesma tabela vende "`pytest` com piso de cobertura bloqueante", vale
   incluir o piso na exclusão. **A lacuna é da minha sugestão 2 da tentativa 1**,
   que nomeou só dois gates — o executor implementou o que eu pedi, corretamente.
   (Para o registro: a camada rápida do eval **é** coberta, porque
   `tests/unit/test_evals_*.py` entra no `make test-unit`.)

4. **Permanecem para a D.4**, inalteradas e corretamente não tocadas neste
   rework: `docs/flow.md:118` ("latência < 20ms") e a contagem "~19.500 alimentos"
   em `CLAUDE.md:97`, `docs/architecture.md:109`, `docs/deploy.md:250` e
   `docs/flow.md:240`.

## 6. Comandos rodados + saídas reais

### Gate estrutural da §5 (após as edições de §3, §5, §8 e §9)

```text
$ bash ~/.codeflow/framework/core/scripts/run-structural.sh .codeflow/specs/002-vitrine-eval-e-saneamento/SPEC_002_VITRINE_EVAL_E_SANEAMENTO.md
✓ ids de fase únicos (26 fases)
✓ heading de cada fase casa com o bullet `id`
✓ todos os slugs são kebab-case
✓ wave: multi com ao menos um id `<TRACK>.<n>`
✓ todo `id` em "Depende de" existe na §5
✓ cada track tem 3–8 fases
✓ grafo de dependências acíclico
✓ §5 estruturalmente válida
EXIT=0
```

### Estado git e isolamento do rework

```text
$ git merge-base --is-ancestor 049f6e5 HEAD && echo OK
OK
$ git log --oneline -4
a360f17 docs(specs): aplica o rework da fase d.3 na tentativa 2
049f6e5 docs(specs): migra o link da demo do ac-20 para o ac-27 pela oq24
b2fa78d docs(readme): separa ruff format do gate de ci e ajusta make check
baf0c4c docs(specs): avalia a fase d.3 com ressalvas na tentativa 1

$ git diff --stat baf0c4c..049f6e5 -- . ':(exclude).codeflow/specs/*/artefatos/*'
 .../SPEC_002_VITRINE_EVAL_E_SANEAMENTO.md | 64 +++++++++++++++++++---
 README.md                                 |  7 ++-
 2 files changed, 59 insertions(+), 12 deletions(-)

$ git diff --name-only 5f137f7..049f6e5 -- . ':(exclude)...artefatos/*' | grep -E "test|alembic|migration|CHANGELOG"
(vazio — nenhum teste, migration ou CHANGELOG no range completo)

$ git status --short
(vazio — árvore limpa antes e depois)
```

### Comandos de validação do projeto (`.codeflow/manifest.md`)

```text
$ make check
All checks passed!
149 files already formatted
Success: no issues found in 81 source files
======================== 496 passed, 3 skipped in 3.94s ========================
================== 145 passed, 5 warnings in 65.93s (0:01:05) ==================
Test Suites: 20 passed, 20 total
Tests:       118 passed, 118 total
Tudo OK.
EXIT=0
```

Gate `security` do manifest é `[—]`. Substituto rodado por mim:

```text
$ gitleaks detect --source . --config .gitleaks.toml --redact --no-banner --exit-code 1
INF 521 commits scanned.
INF scan completed in 14.7s
INF no leaks found
```

### Revalidação do produto da fase

```text
$ node check.mjs   # mermaid.parse() + jsdom, instalado fora do repositório
... 14 diagramas, 0 falhas

$ python3 links.py  # [texto](caminho) em README, CONTRIBUTING, git-workflow,
                    # architecture, docs/fluxos/README e os 9 fluxo.md
links relativos quebrados: 0
```

### IMP-2 — verificação da correção

`README.md:180-183`, depois do rework:

```markdown
| `ruff check` | pre-commit e CI |
| `ruff format --check` | pre-commit e `make check` |
```

Contra as fontes:

```text
$ grep -A1 "name: Lint — ruff" .github/workflows/ci.yml
      - name: Lint — ruff
        run: ruff check .          ← único passo de ruff no CI
$ sed -n '300p' Makefile
	@echo "...e ainda roda tsc e ruff format --check, que o CI nao roda."
$ sed -n '278-283p' Makefile
lint-check: ... ruff check .  /  ruff format --check .   ← o que make check invoca
$ grep -n "ruff" .pre-commit-config.yaml
      - id: ruff        (args: [--fix], files: ^backend/)
      - id: ruff-format (files: ^backend/)
```

A contradição desapareceu: nenhuma das duas linhas atribui `ruff format` ao CI.

### IMP-1 — verificação da correção, lugar por lugar

```text
SPEC:408-419   AC-20  → "a demo com credenciais de demonstração (hoje a local...)"
                        + bloco `> Nota (2026-08-10)` apontando AC-27 e OQ24      ✓
SPEC:440-443   AC-27  → recebe "o link da demo publicada entra no README"          ✓
SPEC:1166-1172 D.3 p1 → "a demo com credenciais", com a nota de migração           ✓
SPEC:1380      E.4    → "Arquivos alterados: cd.yml, docs/deploy.md, README.md"    ✓
SPEC:1391-1393 E.4 p6 → publicar o link e remover a linha de ausência              ✓
SPEC:1396-1397 E.4    → teste do AC-27 cobre "o link publicado no README abre..."  ✓
SPEC:1853-1878 OQ24   → (a) destino, (b) por que não inventar link, (c) por que
                        registrar na §8 — os três subitens no formato das OQ18/22  ✓
SPEC:1934-1936 §9 D.3 → declara a migração                                          ✓
SPEC:1942-1943 §9 E.4 → declara a cláusula recebida                                 ✓
SPEC:266-268   FR-D3  → NÃO alinhada — ainda diz "link da demo"     (sugestão 1)   ✗
```

Precedentes que a OQ24 invoca, conferidos na própria spec:

```text
AC-1 → AC-2 (A.1)          citado em SPEC:1676-1677 (dentro da OQ18)   existe
AC-18 → AC-19 (OQ18)       SPEC:1667-1679                              existe
gate de plataforma da C.7 → D.2 (OQ20)   SPEC:1704-1711                existe
"deploy órfão do frontend na Vercel, pendência da E.4" (OQ16)  SPEC:1639-1641  existe
"não prometer feature inexistente" como violação BLOQUEANTE da D.3  SPEC:1187-1189  existe
```

### Sugestões 2 e 3 da tentativa 1 — verificação

```text
README.md:189  "reproduz a maior parte dos gates do CI localmente — fora
                `gitleaks` e o `next build` de produção"        (era: "reproduz os gates do CI")
README.md:266  "HTTP 413 pedindo ~11,4 mil tokens"              (era: "`Requested 11357`")
```

O `~11,4 mil` não compete mais com o `11508` que a rodada `e1d39b0` registrou em
`history.jsonl` e que o próprio README publica como linha de base.

### O que revalidei da tentativa 1 (não confiei no já-avaliado)

Os 15 números da tabela de decisões, os 9 campos da linha de base contra
`history.jsonl`, a coerência README × `seed_dev_user.py`, a proteção da `main`
por `gh api` e as alegações de produto contra o código foram reconferidos e
seguem batendo — o diff da tentativa 2 não tocou nenhuma dessas linhas
(`git diff baf0c4c..049f6e5 -- README.md` mostra três hunks, todos na "Esteira de
qualidade" e na tabela de free tier).

## 7. Itens da fase / DoD não atendidos

Nenhum.

**Critério de conclusão da §5** (`SPEC:1190-1191`) — "AC-20 satisfeito; execução
limpa a partir do README validada": atendido. As cinco cláusulas do AC-20 no
texto vigente foram verificadas por mim; a execução a partir do README é real,
não simulada.

**Itens globais transversais da §9:**

| Item | Estado |
|---|---|
| `ruff check .` + `ruff format --check .` sem erros | ✓ reproduzido |
| `mypy app/` strict sem erros | ✓ `81 source files` |
| `npm run lint` + `npx tsc --noEmit` sem erros | ✓ (1 warning pré-existente em `Plasma.tsx`, fora do range) |
| `make test-unit` / `test-integration` / `test-frontend` verdes | ✓ 496 / 145 / 118 |
| Limiares de `test_golden_set.py` não regridem (NFR-6) | ✓ nenhum teste no range |
| Nenhum artefato com credencial/PII/`.env` (NFR-4) | ✓ gitleaks limpo em 521 commits |
| Nenhuma migration criada ou alterada (NFR-7) | ✓ |
| Commits em Conventional Commits pt-BR, sem menção a autor/IA | ✓ 7 commits no range + o do relatório |
| Toda decisão de escopo registrada em §8 ou em decision | ✓ **OQ23** (conjunto de arquivos) + **OQ24** (cláusula do AC-20) |

**Ressalva de método, mantida e agora durável:** `make init` foi validado sobre
volumes preexistentes; "a tabela `foods` nasce vazia" (`README.md:32`) é derivada
— nenhuma migration ou seed a popula —, não observada. Não é achado: verificar
custaria destruir o banco local do owner. Fica registrado aqui porque o
`EXECUCAO` some na D.4.

## 8. Divergências entre o relatório e o código real

1. **"Alinhei a redação em todos os lugares onde a cláusula aparecia"** (`:315`)
   — a §2 **FR-D3** (`SPEC:266-268`) não foi alinhada. É a sugestão 1; nove dos
   dez lugares foram cobertos.

2. **Prosa envelhecida no relatório, não corrigida no rework.** Três pontos
   descrevem o estado da tentativa 1 como se fosse o atual:
   - `:82-87` (decisão de design 1) diz *"O AC-20 pede 'link da demo com
     credenciais de demonstração'"* — o AC-20 já não pede, desde `049f6e5`.
   - `:253-255` cita o AC-20 pelo texto antigo, com "link da demo".
   - `:294` e `:300` falam em "5 commits"; o range tem **7** (5 da tentativa 1 +
     2 do rework), mais o commit do próprio relatório.
   Nenhum afeta o produto — a §8 do relatório descreve a migração corretamente —
   e nenhum sobrevive à poda da D.4. Registrado para completude.

3. **"12 diagramas, 0 falhas"** (`:171`) — o repositório tem **14** blocos
   ```` ```mermaid ````; os 2 a mais estão em `docs/auditoria/`, fora do escopo,
   e também parseiam. Subcontagem herdada da tentativa 1.

Nenhuma outra divergência. As tabelas de arquivos CRIADOS/ALTERADOS batem com o
`git diff --stat` do range, o frontmatter bate com a máquina de estados do
ARTIFACTS_SPEC §2.11, e todas as saídas coladas no relatório eu reproduzi com os
mesmos valores.

---

**Nenhuma alteração de código foi feita por esta avaliação.**

`APROVADO` conclui a fase D.3 pela §2.11.3. A §9 da spec pode ser marcada `[x]`
para a D.3, e a **D.4** fica liberada. As quatro sugestões acima não bloqueiam
nada; as 1 e 2 são de spec e cabem naturalmente no próximo toque na §2/§5, as 3 e
4 são material da D.4.
