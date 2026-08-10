---
spec: 002-vitrine-eval-e-saneamento
fase: D.3
slug_fase: readme-vitrine
tentativa: 1
veredito: RESSALVAS
score: 9.5
threshold: 8.5
range_avaliado: 5f137f7bc6887de33131daf36586df0c3c316507..5508747394e7e0d56c2f521c657f040d3f1950af
---

# FASE D.3 — Avaliação independente

## 1. Veredito e score

**Veredito:** RESSALVAS · **Score:** 9.5 / threshold 8.5

Score acima do gate e **zero BLOQUEANTES**. Dois achados IMPORTANTES impedem
`APROVADO` pela precedência estrita do ARTIFACTS_SPEC §2.10.3: (a) a decisão de
escopo que fechou a cláusula "link da demo" do AC-20 vive apenas no `EXECUCAO`,
que é exatamente o artefato que o AC-21 manda a D.4 remover — é o mesmo defeito
que reprovou a D.2 na tentativa 1; (b) uma linha da tabela "Esteira de qualidade"
do README afirma que o CI roda `ruff format --check`, o que o `ci.yml` não faz e
o próprio `Makefile:300` desmente — contradição README × repositório, que é a
cláusula literal do teste do AC-20.

O trabalho substantivo da fase está feito e verificado por mim de ponta a ponta:
os 8 números da tabela de decisões batem com as fontes citadas, os 4 números da
linha de base do eval batem com `history.jsonl`, os 14 blocos Mermaid do
repositório parseiam, os links relativos resolvem, `make check` sai `0` e o
`gitleaks` varre 517 commits sem achado. Ambos os achados são de baixo custo.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 4.0 | AC-20 verificado cláusula a cláusula (§6): `make init` real (containers `Up 30 minutes`, `/health` → `{"status":"ok","version":"0.7.0"}`), portas 3010/8010 conferidas contra `docker-compose.dev.yml:61,99`, credenciais `demo@caloria.app`/`CalorIADemo2026!` coerentes com `seed_dev_user.py` (`SENHA_DEMO = "CalorIADemo2026!"`), 14/14 Mermaid parseados, 8 linhas de decisão com fonte reproduzida. Escopo travado limpo: nenhuma métrica inventada; `CHANGELOG.md` fora do diff (`git diff --name-only \| grep -c CHANGELOG` → `0`); as duas features declaradas em `README.md:76` existem (`AnalysisReview.tsx:30,48,54` e `:266 disabled={... pendentes.length > 0}`). Descontos: cláusula "link da demo" fechada por declaração sem registro durável (IMP-1) e a contradição de `README.md:181` (IMP-2) |
| 2 | Arquitetura e direção de dependências | 3 | 5.0 | Diagramas conferem com o código: `services/ai` do `README.md:95` bate com `backend/app/services/ai/`; a conversão dos 9 fluxos é fiel — `diff` entre `git show 5f137f7:docs/fluxos/01/diagrama.mermaid` e o bloco novo = idêntico; em `05-analise-ia` a única mudança é `Gemini` → `Groq`, exatamente o declarado. `docs/architecture.md` ADR-006 passa a citar os 44 ms medidos (`CHANGELOG.md:31`, `docs/fluxos/06/fluxo.md:49-51`) e ADR-007 passa a descrever o tema real (`layout.tsx:15` aplica `dark` só se `localStorage` pedir) |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5.0 | `gitleaks detect --source . --config .gitleaks.toml` → `517 commits scanned` / `no leaks found`. As 4 capturas de `docs/imagens/` foram inspecionadas uma a uma: só a conta demo (`demo@caloria.a…` truncado na navbar) e dados sintéticos do seed; nenhum e-mail pessoal, token ou dado de terceiro. Único par de credenciais no diff é o da demo, público por desenho, com o parágrafo de isolamento em `README.md:53` conferindo com `test_seed_demo.py::TestPrivilegio` (o modelo `User` não tem campo de papel) |
| 4 | Reusar/espelhar, não duplicar | 3 | 5.0 | OQ23 inserida na §8 no mesmo formato de OQ19/OQ21/OQ22, numerada em sequência, antes da §9 — nenhum mecanismo novo inventado. Números vêm das fontes que já existiam (bug 001, decisions de 2026-07-26 e 2026-08-02, `CHANGELOG`, `history.jsonl`, `backend/evals/README.md`), nenhuma medição refeita. Badge de CI e a seção da conta demo da E.3 preservados. Diagramas migrados, não reescritos |
| 5 | Padrões de domínio/aplicação | 2 | 5.0 | 5 commits em Conventional Commits pt-BR, imperativo, minúsculas, ≤72 col; `git log 5f137f7..e380f71 --format='%B' \| grep -inE "claude\|anthropic\|co-authored\|agent"` → vazio. Corpo de commit explicando o "por quê" em 4 dos 5 |
| 6 | Local e nomes dos arquivos | 2 | 5.0 | Frontmatter do EXECUCAO coerente com a §5 (`SPEC:1150-1151`): `fase: D.3`, `slug_fase: readme-vitrine`, `status: executado`, `tentativa: 1`, `reprovacoes: 0`; `range` = `sha_inicial..sha_final` e ambos ancestrais de HEAD (`git merge-base --is-ancestor` → `0`). `docs/imagens/` é local novo e adequado; 4 PNG de 268–347 KB, abaixo do `--maxkb=1000` do hook |
| 7 | Qualidade de código | 2 | 4.5 | Diff de código = 2 linhas (`seed_dev_user.py:1380` `:3000`→`:3010`; `Sidebar.tsx:80` remove `V0.1`), ambas mínimas e corretas — o `3010` bate com `docker-compose.dev.yml:99` e a remoção do número evita a dessincronia voltar. `make lint-check` → `All checks passed!` + `149 files already formatted`; `make typecheck` → `Success: no issues found in 81 source files`. Desconto: a imprecisão de `README.md:181,188` (IMP-2 e sugestão 2) |
| 8 | Testes e cobertura | 2 | 4.5 | Nenhum arquivo de teste no diff (`git diff --name-only \| grep -E "test\|alembic"` → vazio), então NFR-6 e NFR-7 intactos. Reproduzi: `496 passed, 3 skipped` · `145 passed` · `118 passed / 20 suites`. Desconto: o guarda de coerência README × script (`test_seed_demo.py::TestCredenciaisPublicadas`) é justamente um dos 3 `skipped` sob `make test-unit` — ver §8 |
| 9 | Migration safety (se aplicável) | 2 | [—] | Não se aplica: nenhuma migration criada ou alterada no range (NFR-7 satisfeito por ausência) |

**Score:** (4.0·3 + 5.0·3 + 5.0·3 + 5.0·3 + 5.0·2 + 5.0·2 + 4.5·2 + 4.5·2) / 20 = 95/20 = 4.75 → **9.5/10**.

## 3. Achados BLOQUEANTES

Nenhum.

Registro explícito do que **não** é bloqueante, por ter sido verificado:

- **"Link da demo" do AC-20 sem URL viva não é BLOQUEANTE.** A instância hospedada
  é entregável da E.4, adiada por decisão de owner (ADR-009 / OQ16). Publicar um
  link inexistente violaria a violação bloqueante declarada da própria fase
  ("não prometer feature inexistente", `SPEC:1178-1180`). O README entrega a demo
  local com credenciais e declara a ausência em `README.md:57`. O problema é o
  **registro** dessa decisão, não a decisão — ver IMP-1.
- **Escopo travado íntegro.** Nenhuma métrica inventada (as 12 conferidas abaixo),
  nenhuma feature inexistente prometida (as duas alegações de produto de
  `README.md:76` foram achadas no código), `CHANGELOG.md` histórico intocado.

## 4. Achados IMPORTANTES

### IMP-1 — A decisão de escopo do AC-20 vive só no `EXECUCAO`, que a D.4 vai apagar

**Onde:** `.codeflow/specs/002-vitrine-eval-e-saneamento/artefatos/FASE-D.3-readme-vitrine-EXECUCAO.md:76-82`
(decisão de design 1) e `:276-282` (dúvida 1) · falta em
`SPEC_002_VITRINE_EVAL_E_SANEAMENTO.md` §8.

O AC-20 pede cinco coisas, e uma delas — *"link da demo com credenciais de
demonstração"* — foi fechada por declaração, não por artefato. A decisão é
defensável e eu a endosso. Mas ela **é** uma decisão de escopo tomada durante a
execução, e o item global da §9 (`SPEC:1913-1914`) exige: *"Toda decisão de
escopo tomada durante a execução está registrada aqui em §8 ou numa decision do
framework."* A OQ23 registrou apenas a extensão do conjunto de arquivos; a
cláusula do AC não aparece em lugar nenhum da spec.

O agravante é específico desta spec: o AC-21 manda a **D.4** remover do
versionamento os `FASE-*-EXECUCAO.md` (`SPEC:412-414`). Depois da poda, a §9 vai
mostrar `[x] D.3 — AC-20` e não haverá, no repositório, uma linha explicando por
que a fase fechou sem link — nem para onde a cláusula foi. É literalmente o
IMP-1 pelo qual a D.2 fechou com RESSALVAS na tentativa 1 (*"decisões de escopo
sem registro durável"*, `FASE-D.2-release-v070-AVALIACAO.md:65`, resolvido pela
OQ22 com a justificativa *"viviam só num artefato que a poda vai remover"*).

**Correção sugerida:** acrescentar **OQ24** na §8 da spec, no mesmo formato de
OQ18/OQ20/OQ22 — a cláusula "link da demo" do AC-20 é reconhecidamente dependente
da E.4; declarar o destino (migrar a cláusula para o AC-27/E.4, como OQ18 fez de
AC-18 para AC-19 e OQ20 fez de C.7 para D.2), o que a D.3 entregou no lugar
(demo local com credenciais publicadas, `README.md:38-57`) e por que inventar
URL seria violação bloqueante desta fase. Um hunk aditivo na §8; nenhum código
muda.

### IMP-2 — O README afirma que o CI roda `ruff format --check`; o `ci.yml` não roda, e o `Makefile` diz o contrário

**Onde:** `README.md:181` — linha `| \`ruff check\` + \`ruff format --check\` | pre-commit e CI |`

`.github/workflows/ci.yml` tem um único passo de ruff:

```yaml
      - name: Lint — ruff
        run: ruff check .
```

Não há passo de `ruff format`. E o próprio repositório desmente a afirmação em
voz alta — `Makefile:300`, no alvo `check`:

```make
	@echo "$(BLUE)e ainda roda tsc e ruff format --check, que o CI nao roda.$(NC)"
```

Isso é uma contradição README × repositório, que é exatamente a cláusula final
do teste do AC-20 (`SPEC:1175-1177`) e a razão de ser desta fase — a mesma classe
de defeito que a fase corrigiu em `CONTRIBUTING.md:42`, `docs/git-workflow.md` e
`Makefile:137`. A consequência prática é pequena; a inconsistência interna, não:
o leitor que cruzar o README com o `make check` encontra duas respostas.

**Correção sugerida:** quebrar a linha em duas na tabela de `README.md:179-186`:

| Gate | Onde roda |
|---|---|
| `ruff check` | pre-commit e CI |
| `ruff format --check` | pre-commit e `make check` |

## 5. Sugestões

1. **`docs/flow.md:118` ainda diz "latência < 20ms com ~19.800 registros".** É a
   afirmação exata que esta fase corrigiu em `docs/architecture.md` (ADR-006 →
   44 ms medidos). `docs/flow.md` não está nos "Arquivos alterados" da D.3 nem é
   linkado pelo README, então está **fora do escopo** desta fase e não é achado.
   Fica registrado para a D.4: hoje o repositório tem dois números de latência em
   dois documentos.

2. **`README.md:188` — "`make check` reproduz os gates do CI localmente" é uma
   aproximação.** `make check` = `lint-check` + `typecheck` + `test-unit` +
   `test-integration` + `test-frontend`; não roda `gitleaks` nem `next build`,
   ambos gates do CI listados duas linhas acima na mesma tabela. O próprio
   `Makefile:301` avisa do `npm run build`. Trocar por "reproduz a maior parte
   dos gates do CI (fora `gitleaks` e o build de produção)" custa uma linha e
   fecha a última folga da seção.

3. **`README.md:265` cita `Requested 11357` (bug 003) enquanto a execução cuja
   linha de base o README publica registrou `11508`** (`history.jsonl`, campo
   `falhas[].erro` do run `e1d39b0`). Os dois números são medições reais de
   rodadas diferentes e ambos têm fonte, mas aparecem na mesma página. Nomear a
   rodada ou arredondar ("~11,4 mil tokens") remove o atrito.

4. **A contagem de alimentos continua divergente entre documentos** — `CLAUDE.md:97`,
   `docs/architecture.md:109`, `docs/deploy.md:250` e `docs/flow.md:240` dizem
   "~19.500"; a nota 4 do EXECUCAO mede 42.168 linhas, 18.770 consultáveis. O
   README novo acertou em **não** repetir o número solto. Fica para a D.4, que já
   nomeia `data/README.md`.

## 6. Comandos rodados + saídas reais

### Gate estrutural da §5

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

### Estado git e isolamento do range

```text
$ git merge-base --is-ancestor 5508747 HEAD && echo OK
OK
$ git log --format="%h %s" 5f137f7..5508747
5508747 docs(specs): registra na oq23 os arquivos da d.3 alem do declarado
0f82bd9 fix: remove servico inexistente, porta errada e versao desatualizada
d5ab959 docs: corrige afirmacoes falsas sobre hooks, protecao e deploy
abfb2cf docs(readme): reescreve o readme como peca de portfolio
5731096 docs(fluxos): embute os diagramas mermaid dentro dos fluxo.md

$ git diff --stat 5f137f7..5508747 -- . ':(exclude).codeflow/specs/*/artefatos/*'
 31 files changed, 498 insertions(+), 344 deletions(-)

$ git status --short
(vazio — árvore limpa antes e depois da avaliação)
```

### Comandos de validação do projeto (`.codeflow/manifest.md`)

```text
$ make lint-check
Lint check backend (sem corrigir)...
All checks passed!
149 files already formatted
Lint check frontend (sem corrigir)...
> next lint --no-cache
./components/auth/Plasma.tsx
156:26  Warning: The ref value 'containerRef.current' will likely have changed ...  react-hooks/exhaustive-deps
LINT_EXIT=0
                              (warning pré-existente, fora do range; não é erro)

$ make typecheck
Type check backend (mypy)...
Success: no issues found in 81 source files
Type check frontend (tsc)...
TYPE_EXIT=0                   (tsc sem saída = sem erro)

$ make test-unit
======================== 496 passed, 3 skipped in 4.26s ========================
UNIT_EXIT=0

$ make test-integration
================== 145 passed, 5 warnings in 84.69s (0:01:24) ==================

$ make check
Test Suites: 20 passed, 20 total
Tests:       118 passed, 118 total
Tudo OK.                      (exit 0)
```

Gate `security` do manifest é `[—]` (não há gate configurado no CI/Makefile).
Substituto real rodado por mim:

```text
$ gitleaks detect --source . --config .gitleaks.toml --redact --no-banner --exit-code 1
INF 517 commits scanned.
INF scan completed in 14.8s
INF no leaks found
```

### Verificações específicas do AC-20

**Serviços no ar e comando único:**

```text
$ docker ps
caloria_frontend       Up 30 minutes   0.0.0.0:3010->3000/tcp
caloria_backend        Up 30 minutes   0.0.0.0:8010->8000/tcp
caloria_celery_worker  Up 30 minutes
caloria_celery_beat    Up 30 minutes
caloria_postgres       Up 30 minutes (healthy)
caloria_redis          Up 30 minutes (healthy)

$ curl -s http://localhost:8010/health
{"status":"ok","version":"0.7.0"}
$ curl -s -o /dev/null -w "front=%{http_code}\n" http://localhost:3010/
front=307
```

Todos os 13 alvos citados no README existem no `Makefile` (`init`, `help`,
`seed-demo`, `dev`, `dev-d`, `down`, `check`, `test-unit`, `test-integration`,
`migrate`, `psql`, `typecheck`, `lint-check`) e `make init` de fato cria o `.env`
a partir do `.env.example` (`Makefile:114-121`).

**Diagramas Mermaid — parser oficial, por mim, sobre o repositório inteiro:**

```text
$ node check.mjs   # mermaid.parse() + jsdom, instalado fora do repositório
ok   README.md #1
ok   README.md #2
ok   docs/architecture.md #1
ok   docs/auditoria/01-arquitetura.md #1
ok   docs/auditoria/runbook.md #1
ok   docs/fluxos/01-autenticacao/fluxo.md #1
ok   docs/fluxos/04-registro-refeicao-web/fluxo.md #1
ok   docs/fluxos/05-analise-ia/fluxo.md #1
ok   docs/fluxos/06-lookup-nutricional/fluxo.md #1
ok   docs/fluxos/07-insights-relatorios/fluxo.md #1
ok   docs/fluxos/08-lembretes-notificacoes/fluxo.md #1
ok   docs/fluxos/09-celery-tarefas/fluxo.md #1
ok   docs/fluxos/10-dashboard-frontend/fluxo.md #1
ok   docs/fluxos/11-logs-saude/fluxo.md #1

14 diagramas, 0 falhas

$ git ls-files | grep -c "\.mermaid$"
0
$ for f in docs/fluxos/*/fluxo.md; do grep -q '```mermaid' "$f" || echo "SEM: $f"; done
(nada — os 9 fluxos têm diagrama)
```

**Fidelidade da conversão** (o diagrama não foi reescrito de memória):

```text
$ diff <(git show 5f137f7:docs/fluxos/01-autenticacao/diagrama.mermaid) <bloco novo>
(idêntico)
$ diff <(git show 5f137f7:docs/fluxos/05-analise-ia/diagrama.mermaid) <bloco novo>
2c2  <  B["Estagio 1: Gemini identifica alimentos"]  ---  >  B["Estagio 1: Groq ..."]
7c7  <  G[Gemini estima macros]                      ---  >  G[Groq estima macros]
$ diff <(git show 5f137f7:docs/fluxos/10-dashboard-frontend/diagrama.mermaid) <bloco novo>
(idêntico)
```

**Links relativos** (varredura própria em README, CONTRIBUTING, git-workflow,
architecture, docs/fluxos/README e os 9 `fluxo.md`):

```text
links relativos quebrados: 0
```

**Cada número da tabela de decisões, contra a fonte que o README cita:**

| Afirmação do README | Fonte verificada | Confere |
|---|---|---|
| 3386 vs 2094 kcal, 38,2% | `bugs/001…md:134` | ✓ |
| 3 execuções → 572,3 kcal | `bugs/001…md:141` | ✓ |
| F1 0,776 → 0,857 | `decisions/2026-07-26…md:38-39,52` | ✓ |
| F1 0,829 na implementação final | `decisions/2026-07-26…md:77` | ✓ |
| 23.398 linhas `ai_estimated` | `decisions/2026-07-26…md:138` | ✓ |
| erro 16,7% → 4,1%; ±10% 69% → 91% | `decisions/2026-07-26…md:118-124` | ✓ |
| 6 de 29 itens caem no fallback | `…:121` (23/29 casam) | ✓ |
| boost 2,50 tem F1 0,889, rejeitado; `arroz branco cozido` → `Brócolis cozido`, bruto 0,43 | `decisions/2026-07-26…md:80-85` | ✓ |
| 238 ms por n-grama → 44 ms | `CHANGELOG.md:31`, `docs/fluxos/06/fluxo.md:49-51` | ✓ |
| MdAPE composto 23,81% → 6,86%; ±10% 25% → 75% | `decisions/2026-08-02…md:21-24` | ✓ |
| MdAPE headline por assimetria do MAPE | `backend/evals/README.md:186-194` | ✓ |
| POF 2011 (medida→g) e TACO 4ª ed. (g→kcal) | `backend/evals/README.md:81-82` | ✓ |
| schema rejeita a tabela `portions` como fonte | `backend/evals/schema.py:26` | ✓ |
| TPM visão 8.000, `Requested 11357` | `bugs/003…md:23,42` | ✓ |
| TPD 100.000, 99.768 consumidos | `backend/evals/README.md:165-175` | ✓ |

**Linha de base do eval, contra `backend/evals/runs/history.jsonl` (última linha):**

```text
git_commit e1d39b03675b…            → README "e1d39b0"                     ✓
modelo llama-3.3-70b-versatile      → idem                                 ✓
dataset_n 43; {simples 23, composto 17, foto 3}                            ✓
chamadas 57; tokens_in 38833 + tokens_out 4099 = 42932  → "42.932"         ✓
latencia.mediana_s 4.662            → "4,7 s"                              ✓
simples:  mdape 25.53 · ic95 [7.83, 33.33] · dentro 0.348 · n 23           ✓
composto: mdape 61.64 · ic95 [43.66, 89.94] · dentro 0.062 · n 16          ✓
agregado: mdape 33.33 · ic95 [26.26, 43.66] · dentro 0.231 · n 39          ✓
falhas: 3 × HTTP 413 no estrato de foto; 43 − 3 − 1 = 39                   ✓
```

**Proteção da `main`, na plataforma (não no documento):**

```text
$ gh api repos/gabriel-ngrs/CalorIA/branches/main/protection
required_status_checks.contexts = ["Backend — lint e testes","Frontend — lint e build"]
required_status_checks.strict   = true
enforce_admins.enabled          = true
allow_force_pushes.enabled      = false
allow_deletions.enabled         = false
required_pull_request_reviews   = ausente
```

Confere com `README.md:188` e com a tabela de `docs/git-workflow.md`.

**Coerência README × script do seed** (o teste que a travaria está `skipped` no
runner — ver §8; verifiquei à mão):

```text
seed_dev_user.py: SENHA_DEMO = "CalorIADemo2026!"
README contém 'demo@caloria.app':  True
README contém 'CalorIADemo2026!':  True
README contém 'make seed-demo':    True
```

**Capturas de tela** — as quatro abertas e conferidas contra a legenda:
`dashboard.png` (tema claro, cards de macro, hidratação, humor, peso, série de 7
dias), `refeicoes.png` (refeições do dia com macros por item), `peso.png`
("Evolução — últimos 90 dias" + histórico), `dashboard-escuro.png` (mesma tela,
tema escuro). Todas mostram a conta `demo@caloria.a…` com dados sintéticos e o
rodapé já corrigido ("Feito por Gabriel Negreiros"), o que confirma que foram
tiradas **depois** do fix do `Sidebar.tsx`.

**Alegações de produto do README, contra o código:**

```text
README:76 "origem de cada número declarada na tela"
  → frontend/components/refeicoes/AnalysisReview.tsx:30,48,54 (taco / openfoodfacts / ai_estimated)
  → frontend/app/(dashboard)/refeicoes/page.tsx:369 <SourceDot source={item.data_source} />
README:76 "item sem âncora determinística bloqueia o salvamento até confirmação"
  → backend/app/services/ai/meal_parser.py:192-193; schemas/ai.py:33,37
  → AnalysisReview.tsx:255-266 (botão disabled enquanto houver pendentes)
README:268 "cache Redis por 7 dias (chave sha256 incluindo o modelo)"
  → backend/app/services/ai/ai_client.py:354-373 ([MODEL] na assinatura)
README:268 "retry por classe de exceção com teto de tempo"
  → ai_client.py:241-262 (_espera_do_backoff com teto)
README:182 "mypy em modo strict"
  → backend/pyproject.toml [tool.mypy] strict = true
README:81  "PWA — instalável"
  → frontend/app/manifest.ts
```

## 7. Itens da fase / DoD não atendidos

**Critério de conclusão da §5 (`SPEC:1181-1182`) — "AC-20 satisfeito; execução
limpa a partir do README validada":** substancialmente atendido. As cinco
cláusulas do AC-20 foram verificadas por mim; quatro integralmente, a de "link da
demo" por substituição declarada (ver IMP-1). A execução a partir do README é
real e não simulada — os serviços estão no ar e responderam.

**Itens globais da §9 (`SPEC:1902-1914`):**

| Item | Estado |
|---|---|
| `ruff check .` + `ruff format --check .` sem erros | ✓ reproduzido |
| `mypy app/` strict sem erros | ✓ `81 source files` |
| `npm run lint` + `npx tsc --noEmit` sem erros | ✓ (1 warning pré-existente) |
| `make test-unit` / `test-integration` / `test-frontend` verdes | ✓ 496 / 145 / 118 |
| Limiares de `test_golden_set.py` não regridem (NFR-6) | ✓ nenhum arquivo de teste no diff |
| Nenhum artefato com credencial/PII/`.env` (NFR-4) | ✓ gitleaks limpo em 517 commits |
| Nenhuma migration criada ou alterada (NFR-7) | ✓ nenhuma no diff |
| Commits em Conventional Commits pt-BR, sem menção a autor/IA | ✓ 5 commits |
| **Toda decisão de escopo registrada em §8 ou em decision** | **✗ — IMP-1**: a OQ23 cobre o conjunto de arquivos, não a cláusula "link da demo" do AC-20 |

**Ressalva de método declarada pelo executor e mantida por mim:** `make init` foi
validado sobre volumes preexistentes; ninguém rodou `make reset`. A afirmação de
`README.md:32` ("a tabela `foods` nasce vazia") é derivada, não observada. Não é
achado — o custo de verificar é destruir o banco local do owner, e a derivação é
sólida (nenhuma migration ou seed popula `foods`). Registrada aqui para que a
lacuna não desapareça com o `EXECUCAO`.

## 8. Divergências entre o relatório e o código real

1. **Evidência do AC-20 que não foi exercitada.** O EXECUCAO (`:239-241`) cita
   `test_seed_demo.py::TestCredenciaisPublicadas` como prova de que os três
   strings do README batem com o script. Esses três testes estão entre os
   `3 skipped` de `make test-unit`:

   ```text
   SKIPPED [1] tests/unit/test_seed_demo.py:92: README.md da raiz não é alcançável
              daqui (container monta só backend/)   (idem :95 e :100)
   ```

   O guarda existe mas não roda no runner padrão. Condição **pré-existente da
   E.3**, não introduzida pela D.3, e o `skipif` é honesto e comentado. Verifiquei
   as três asserções à mão (§6) e todas passam. Sem impacto no veredito; fica
   registrado porque o relatório apresenta como verificado algo que a execução
   citada pulou.

2. **Contagem de diagramas.** O EXECUCAO (`:166`) diz "12 diagramas, 0 falhas";
   o repositório tem **14** blocos ```` ```mermaid ````. Os 2 a mais estão em
   `docs/auditoria/` (fora do escopo da fase) e também parseiam. Subcontagem no
   relatório, sem defeito no produto.

3. **Contagem de commits.** O EXECUCAO fala em "5 commits" (`:268`) e o resumo de
   handoff fala em "6". Ambos corretos em contextos diferentes: 5 no `range`
   auditado + o commit `e380f71` do próprio relatório, em cima de `sha_final`,
   como o ARTIFACTS_SPEC §2.9.1 manda.

4. **`README.md:181` afirma o que o `Makefile:300` nega** — ver IMP-2. É a única
   divergência entre o que o relatório declara ter corrigido ("afirmações falsas")
   e o que o repositório contém.

Nenhuma outra divergência: as tabelas de arquivos CRIADOS/ALTERADOS do EXECUCAO
correspondem exatamente ao `git diff --stat` do range, e todas as saídas coladas
no relatório eu reproduzi com os mesmos valores.

---

**Nenhuma alteração de código foi feita por esta avaliação.** As correções voltam
ao chat executor: aplicar IMP-1 (OQ24 na §8) e IMP-2 (uma linha da tabela do
README), depois reavaliar em chat zerado, `tentativa: 2`.
