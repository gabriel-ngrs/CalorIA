---
spec: 002-vitrine-eval-e-saneamento
fase: C.7
slug_fase: eval-ci
tentativa: 4
veredito: APROVADO
score: 9.8
threshold: 8.5
range_avaliado: 40e2941..b838c86
---

# FASE C.7 — Avaliação independente

## 1. Veredito e score

**Veredito:** APROVADO · **Score:** 9.8 / threshold 8.5 — zero BLOQUEANTES, zero
IMPORTANTES.

**O BLOQUEANTE da tentativa 3 está fechado, e fechado pelo caminho certo.** A
cláusula "sem casos vazios" não sumiu nem foi reinterpretada: ela tem **dono
nomeado** (`.codeflow/bugs/003-http-413-no-estrato-de-foto.md`), **condição de
fechamento explícita** ("ao corrigir, a exceção sai do AC-15"), **decision
registrada** e o **AC-15 reescrito com lista fechada de três `id`s** — não com
tolerância genérica. Conferi a lista contra o dataset e contra o artefato de
execução: os três `id`s do AC (`foto-coxinha-1-unidade`, `foto-ovo-frito-1-unidade`,
`foto-banana-1-unidade`) são **exatamente** os três casos do estrato `foto` em
`dataset/casos.jsonl` (n=3 de 43) e **exatamente** as três falhas registradas em
`history.jsonl`. Não sobra vazio fora da lista, e qualquer um que surja reprova o
AC — inclusive porque `evals/report.py:verificar()` continua estourando em
**qualquer** caso vazio, o que deixa a ferramenta mais rígida que o AC, e não o
contrário. A direção do erro é a segura.

**O teste que a D.1 estabeleceu passa.** `grep "casos vazios"` na spec devolve §3
(369), §5 (1054) e §9 (1787) dizendo a mesma coisa, e a NFR-3 (294) intacta com o
qualificador dela ("por `429`"), que é outro requisito. A OQ20 recebeu retificação
no próprio parágrafo onde o "por quota" tinha aparecido sem base — o executor
corrigiu a própria trilha em vez de apagá-la.

**Verifiquei que nada de código mudou**, que é o que o rework prometia:
`git diff 5ac94e6..b838c86 -- backend/ .github/ frontend/` são 32 linhas em dois
arquivos — 26 de markdown no README do harness e 9 de **comentário** no
`eval.yml`. O YAML foi reparseado por mim: `jobs: ['eval']`, `cron: 0 6 * * 1`,
`workflow_dispatch` com as mesmas entradas. Os limiares seguem em
`MDAPE_MAXIMO = 25.0` e `FRACAO_MINIMA_DENTRO_DE_10PCT = 0.50` — **não foram
recalibrados**, com o gate vermelho na mesa. É a mesma disciplina que a avaliação
anterior endossou, mantida sob a pressão de uma quarta tentativa, que é quando ela
custa mais.

**C7-IMP-3 também está fechado.** O passo 4 pedia a decisão de periodicidade "no
README do harness"; ela está em `backend/evals/README.md:158-181`, com o quadro
medido (TPD 100.000; 42.932 tokens / 57 chamadas por execução; 99.768 até o `429`)
e a conclusão explícita. O cabeçalho do `eval.yml` parou de pedir uma medição que
já existe e parou de dizer "~10 casos" para um dataset de 43.

**O que fica são sugestões, nenhuma delas gate.** A mais concreta: os comentários
de `eval.yml:135-137` e `report.py:112` ainda atribuem à **NFR-3** a regra "nenhum
caso vazio", que é sem qualificador e é do **AC-15** — a mesma conflação que o
`C7-BLQ-1` condenou, sobrevivendo nos dois lugares onde o gate mora. Não é defeito
de comportamento (o gate faz a coisa certa e mais estrita), é imprecisão de
citação; e um deles é arquivo da C.8. Vale a correção de uma linha quando o bug 003
for fechado, não uma reprovação agora.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 5 | AC-15 nas três camadas: rápida sem rede, 26 testes em **0,11 s** (teto 60 s); `test_prompt_alterado_sem_regravar_estoura` (`tests/unit/test_evals_snapshot.py:241`) verde, rodado por mim; camada completa em `history.jsonl` com falhas `['foto-coxinha-1-unidade','foto-ovo-frito-1-unidade','foto-banana-1-unidade']` = a lista nominada do AC (SPEC §3:369-372), e o estrato `foto` do dataset tem **exatamente** esses 3 casos. Escopo travado, item a item: sem `continue-on-error` no `eval.yml` (150 linhas, verificado); `on:` só `schedule`+`workflow_dispatch`, nunca `pull_request`; `grep -rlE "gsk_\|Authorization\|api[_-]?key"` nos 71 cassettes → vazio; limiares intactos (`report.py:29-30`) |
| 2 | Arquitetura e direção de dependências | 3 | 5 | Zero código de produção tocado (`git diff 5ac94e6..b838c86 -- backend/ .github/ frontend/` = README + comentário de YAML). A cláusula foi roteada para o artefato que pode carregá-la (registro de bugs) em vez de forçar uma 9ª fase num track fechado — checado contra ARTIFACTS_SPEC §2.8.6 #3 ("3 a 8 sub-seções por track"): Track C tem 8 |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | `gitleaks detect --config .gitleaks.toml` → **503 commits scanned, no leaks found**, EXIT 0; cassettes sem credencial; o diff da tentativa é markdown + comentário, sem superfície nova |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | A migração espelha o rito da OQ18 (AC-18 → AC-19) em vez de inventar outro; o bug 003 segue o frontmatter de `001`/`002` campo a campo; `bugs/INDEX.md` incrementou `proximo_numero` para `004` como a própria convenção do índice manda |
| 5 | Padrões de domínio/aplicação | 2 | 5 | Decisions com contexto → decisão → alternativas rejeitadas → consequência, no formato das 20 anteriores; OQ21 registrada na §8 com o mesmo padrão "RESOLVIDO (data)" das OQ13/OQ18/OQ20; `run-structural.sh` = **EXIT 0** depois das edições |
| 6 | Local e nomes dos arquivos | 2 | 5 | `.codeflow/bugs/003-<slug>.md`, `.codeflow/decisions/<data>-<titulo>.md`, seção nova dentro de "Consumo de quota" no README do harness — tudo onde a convenção do projeto põe |
| 7 | Qualidade de código | 2 | 4 | `ruff check .` + `ruff format --check .` + `mypy app/ evals/` limpos (149 arquivos, 81 fontes). Desconto: `eval.yml:135-137` e `report.py:112` seguem citando **NFR-3** para a regra sem qualificador que é do **AC-15** — o `eval.yml` foi editado nesta tentativa 4 linhas acima disso |
| 8 | Testes e cobertura | 2 | 5 | Rodados por mim: `pytest tests/unit -q` → **496 passed, 3 skipped in 4.04s**; `test_evals_snapshot.py` → **26 passed in 0.11s**; nenhum teste novo era devido (nenhuma linha de comportamento mudou) |
| 9 | Migration safety (se aplicável) | 2 | [—] | Nenhuma migration no diff da tentativa |

Score = 98 / 100 → 4,9 × 2 = **9.8**.

## 3. Achados BLOQUEANTES

Nenhum.

O `C7-BLQ-1` da tentativa 3 foi verificado como fechado, ponto a ponto:

| O que o BLOQUEANTE exigia | Onde está | Verificado |
|---|---|---|
| Destino nomeado para a cláusula | `.codeflow/bugs/003-http-413-no-estrato-de-foto.md` | Arquivo lido; traz sintoma medido, as três camadas do defeito e **condição de fechamento** ("ao corrigir, a exceção sai do AC-15") |
| Decision registrando o rito | `2026-08-08-clausula-sem-casos-vazios-migra-da-c7-para-o-bug-003.md` | Lida; alternativas descartadas incluem os caminhos 1 e 3 do avaliador, com razão |
| Exceção nominada, não genérica | SPEC §3:369-372 + nota | Lista fechada de 3 `id`s; batem com o dataset (`estrato=foto`, n=3) e com `history.jsonl` |
| §3, §5 e §9 dizendo a mesma coisa | 369 / 1054 / 1787 | `grep "casos vazios"` conferido; NFR-3 (294) preservada com o qualificador próprio |
| Não reinterpretar o AC pela NFR-3 | EXECUCAO §6 | Os dois viraram itens separados, cada um com a evidência que lhe cabe |

## 4. Achados IMPORTANTES

Nenhum.

## 5. Sugestões

1. **A conflação AC-15 × NFR-3 sobreviveu nos comentários do gate.**
   `.github/workflows/eval.yml:135-137` — *"`verificar` falha quando há caso vazio
   (NFR-3)"* — e `backend/evals/report.py:112` — *"# NFR-3: nenhuma execução pode
   terminar com casos vazios"*. A regra sem qualificador é do **AC-15**; a NFR-3 só
   fala de `429`. É citação imprecisa, não comportamento errado (o gate estoura em
   qualquer vazio, mais estrito que o AC), mas é o último lugar onde a leitura que
   gerou o `C7-BLQ-1` continua escrita. Trocar "NFR-3" por "AC-15 e NFR-3" nas duas
   linhas custa nada; `report.py` é arquivo da C.8, então o momento natural é o
   fechamento do bug 003, quando a nota do AC-15 também cai.
2. **O quadro de quota mede 43 casos, mas cobra 40.** `backend/evals/README.md:163-167`
   apresenta 42.932 tokens / 57 chamadas como o custo de "43 casos, 1 repetição".
   Os três de foto morreram no `413` **antes** de gerar, e não entram nas 57
   chamadas. Quando o bug 003 fechar, cada um passa a pedir ~11,5 k tokens
   (`Requested 11508`, medido no próprio `history.jsonl`) e a execução do runner
   sobe para ~77 k. A conclusão não muda — só fica mais forte: diária continua
   impossível, semanal continua cabendo, e a invariância continua não cabendo
   junto. Vale uma linha no quadro dizendo que o número é do estado com o 413
   aberto, para que a próxima releitura não use 42.932 como orçamento.
3. **`11357` e `11508` são dois números do mesmo defeito.** O bug 003 (`:23-26`)
   cita `Requested 11357` e o atribui a "medição da Fase B.5 (OQ19) **e** da Fase
   C.7". O 11357 é da B.5; a execução da C.7 registrou **11508** nas três falhas.
   Os dois sustentam a tese (idêntico entre imagens de 111 KB, 200 KB e 291 KB), e
   nenhum é falso — mas o registro ficaria mais preciso citando os dois com sua
   origem, já que ele agora é o dono da cláusula.
4. **Os limiares seguem sem decisão de owner** (`MDAPE_MAXIMO = 25.0`,
   `FRACAO_MINIMA_DENTRO_DE_10PCT = 0.50` contra MdAPE 33,33% e 23% dentro de
   ±10%). Mantenho a leitura da avaliação anterior — separar limiar de **regressão**
   (bloqueante, ancorado na linha de base medida) de **meta de qualidade**
   (não-bloqueante, publicada) — e concordo com a recusa em aplicá-la aqui: mexer em
   limiar dentro do rework que pune afrouxamento seria contraditório. É item de
   mesa do owner, não da fase.
5. **A terceira migração de cláusula pede regra, não precedente.** A.1 (AC-1), D.1
   (AC-18 → AC-19) e agora C.7 (AC-15 → bug 003). Nas três o argumento se sustentou
   e nas três o rito foi reconstruído do zero. A decision já registra isso na seção
   "O que esta decisão não resolve"; segue sendo evolução de framework, fora do
   escopo de qualquer fase desta spec.
6. **`actionlint` no CI** continua anotado para a E.4. Sem objeção — o `eval.yml`
   foi validado por parse nesta avaliação, mas parse não é lint.

## 6. Comandos rodados + saídas reais

```text
# --- gate estrutural da §5 (antes de classificar a fase) ---
$ bash ~/.codeflow/framework/core/scripts/run-structural.sh \
    .codeflow/specs/002-vitrine-eval-e-saneamento/SPEC_002_VITRINE_EVAL_E_SANEAMENTO.md
✓ ids de fase únicos (26 fases)
✓ heading de cada fase casa com o bullet `id`
✓ todos os slugs são kebab-case
✓ wave: multi com ao menos um id `<TRACK>.<n>`
✓ todo `id` em "Depende de" existe na §5
✓ cada track tem 3–8 fases
✓ grafo de dependências acíclico
✓ §5 estruturalmente válida
EXIT=0

# --- estado git: branch e ancestralidade do range ---
$ git branch --show-current
dev
$ git merge-base --is-ancestor b838c86 HEAD && echo OK
b838c86 é ancestral de HEAD (ou HEAD)
$ git merge-base --is-ancestor 40e2941 HEAD && echo OK
40e2941 ancestral OK

# --- o que a tentativa 4 mudou de fato (nada de código) ---
$ git diff 5ac94e6..b838c86 --stat -- backend/ .github/ frontend/
 .github/workflows/eval.yml |  9 ++++++---
 backend/evals/README.md    | 26 ++++++++++++++++++++++++++
 2 files changed, 32 insertions(+), 3 deletions(-)

$ python3 -c "import yaml; d=yaml.safe_load(open('.github/workflows/eval.yml')); \
    print('jobs:',list(d['jobs'].keys()),'| on:',d[True])"
jobs: ['eval'] | on: {'schedule': [{'cron': '0 6 * * 1'}], 'workflow_dispatch':
  {'inputs': {'estrato': {...'options': ['', 'simples', 'composto', 'foto']}}}}
   → cron e gatilhos intactos; só o bloco de comentário 9-15 mudou

# --- a lista nominada do AC-15, conferida contra dataset e execução ---
$ python3 -c "import json; d=[json.loads(l) for l in \
    open('backend/evals/dataset/casos.jsonl') if l.strip() and not l.startswith('//')]; \
    print('total',len(d),'| foto',[c['id'] for c in d if c.get('estrato')=='foto'])"
total 43 | foto ['foto-coxinha-1-unidade','foto-ovo-frito-1-unidade','foto-banana-1-unidade']

$ python3 -c "import json; r=json.loads(open('backend/evals/runs/history.jsonl') \
    .read().splitlines()[-1]); print(r['run_id'], r['dataset_n'], r['custo']); \
    print([f['id'] for f in r['falhas']])"
e1d39b03675b-0758d981c3c0 43 {'chamadas': 57, 'origem': 'provedor',
                              'tokens_in': 38833, 'tokens_out': 4099}
['foto-coxinha-1-unidade','foto-ovo-frito-1-unidade','foto-banana-1-unidade']
   → 38.833 + 4.099 = 42.932 tokens. A lista do AC = o estrato inteiro = as falhas.
   → erro real das três: "413 … tokens per minute (TPM): Limit 8000, Requested 11508"

# --- coerência §3 × §5 × §9 (o teste da D.1) ---
$ grep -n "casos vazios" .codeflow/specs/.../SPEC_002_VITRINE_EVAL_E_SANEAMENTO.md
294:  sem abortar: nenhuma execução pode terminar com casos vazios por `429`. ← NFR-3
369:  completa roda contra o provedor real e conclui sem casos vazios **além dos   ← §3
1054: conclui sem casos vazios além dos nominados no bug 003 (os três de foto, por ← §5
1787:      `workflow_dispatch` no GitHub, para a D.2 (OQ20); a de "sem casos vazios" ← §9

# --- escopo travado ---
$ grep -n "continue-on-error\|pull_request\|schedule\|cron" .github/workflows/eval.yml
17:  schedule:
18:    - cron: "0 6 * * 1"
135:  # Bloqueante por desenho: sem `continue-on-error` em nenhum passo acima.
   → nenhum `continue-on-error`; nenhum `pull_request`
$ grep -rlE "gsk_|Authorization|api[_-]?key" backend/evals/cassettes/
(vazio)
$ ls backend/evals/cassettes/*.json | wc -l
71
$ grep -n "MDAPE_MAXIMO\|FRACAO_MINIMA_DENTRO_DE_10PCT" backend/evals/report.py
29:MDAPE_MAXIMO = 25.0
30:FRACAO_MINIMA_DENTRO_DE_10PCT = 0.50
   → limiares NÃO recalibrados

# --- passos 1 a 4 da fase, verificados no artefato ---
$ sed -n '141,150p' .github/workflows/eval.yml
      - name: Publicar relatório como artifact          ← passo 3, artifact
$ grep -n "actions/cache@v4\|concurrency\|EVAL_RECORD_CASSETTES" .github/workflows/eval.yml
27:concurrency: {group: eval, cancel-in-progress: false}   ← concorrência limitada
93:  - uses: actions/cache@v4  (path: backend/evals/cassettes)  ← cache em disco
113:  EVAL_RECORD_CASSETTES: "1"   ← só na agendada; a camada rápida replica do disco
$ grep -n "Camada RÁPIDA" -A 6 .github/workflows/ci.yml
79: # Camada RÁPIDA do eval: zero rede, roda a cada PR …
84: run: pytest tests/unit/test_evals_snapshot.py … -q
$ grep -n "Medição de 2026-08-04\|TPD\|semanal cabe" backend/evals/README.md
158:#### Medição de 2026-08-04 — por que a agenda é semanal    ← passo 4, C7-IMP-3
165:| Limite que morde | **tokens por dia (TPD): 100.000** …
180:impossível; semanal cabe.** …

# --- gates do projeto (manifest.md), rodados por mim ---
$ docker compose -f docker-compose.dev.yml exec -T backend sh -c \
    "ruff check . && ruff format --check . && mypy app/ evals/"
All checks passed!
149 files already formatted
Success: no issues found in 81 source files

$ docker compose -f docker-compose.dev.yml exec -T backend pytest tests/unit -q
496 passed, 3 skipped in 4.04s

$ docker compose -f docker-compose.dev.yml exec -T backend \
    pytest tests/unit/test_evals_snapshot.py -q
26 passed in 0.11s                    ← NFR-2: teto de 60 s

$ docker compose -f docker-compose.dev.yml exec -T backend \
    pytest tests/unit/test_evals_snapshot.py -q -k "regravar or estoura or prompt"
7 passed, 19 deselected in 0.05s      ← inclui test_prompt_alterado_sem_regravar_estoura

$ (cd frontend && npx tsc --noEmit); echo "TSC_EXIT=$?"
TSC_EXIT=0

$ gitleaks detect --source . --config .gitleaks.toml --redact --no-banner --exit-code 1
503 commits scanned. no leaks found    >>> EXIT=0

$ git status --short
(vazio — árvore limpa ao fim da avaliação)
```

**Não rodei:** nova execução completa contra a Groq (nenhuma linha de
comportamento mudou desde a execução avaliada, e a cota é recurso escasso que a
C.8 ainda precisa) nem `npm run lint` completo — o diff da tentativa não tem
arquivo de frontend; rodei `tsc --noEmit` mesmo assim, por baixo custo. O
`eval.yml` no GitHub segue indisparável (`HTTP 404` da OQ20), e essa cláusula é da
D.2 desde a tentativa 3.

## 7. Itens da fase / DoD não atendidos

Nenhum.

| Item (§5 / §9) | Estado |
|---|---|
| AC-15 — camada rápida sem rede, < 60 s | ✓ 26 testes, 0,11 s |
| AC-15 — prompt alterado sem regravar quebra o CI | ✓ `test_evals_snapshot.py:241`, verde nesta avaliação |
| AC-15 — camada completa sem casos vazios **além dos nominados no bug 003** | ✓ 3 vazios, e são exatamente os 3 `id`s da lista fechada |
| NFR-2 | ✓ 0,11 s contra teto de 60 s |
| NFR-3 — nenhum caso vazio por `429` | ✓ zero 429 no runner |
| Passo 1 — gravação/replay com CI sem gravar | ✓ `EVAL_RECORD_CASSETTES` só na agendada (`eval.yml:113`) |
| Passo 2 — snapshot do payload como diff legível | ✓ 26 testes de snapshot versionados |
| Passo 3 — agendado, cache, concorrência, artifact, falha por limiar | ✓ `actions/cache@v4`, `concurrency: eval`, `upload-artifact@v4`, `verificar` sem `continue-on-error` |
| Passo 4 — agenda dimensionada por medição, registrada **no README** | ✓ `README.md:158-181` — **C7-IMP-3 fechado** |
| Gate — execução completa registrada em `history.jsonl` | ✓ `run_id=e1d39b03675b-0758d981c3c0` |
| Escopo travado — sem `continue-on-error`, sem eval por PR, cassette sem chave, imagens licenciadas, limiar não afrouxado | ✓ todos |
| Cláusula de plataforma (workflow registrado no GitHub) | migrada para o AC-19 / D.2 (OQ20), aceita na tentativa 3 |
| Cláusula "sem casos vazios" sem qualificador | migrada para o bug 003 (OQ21), com rito — **C7-BLQ-1 fechado** |

## 8. Divergências entre o relatório e o código real

Nenhuma divergência material. O que encontrei de diferente entre o EXECUCAO e o que
medi, e que não muda conclusão nenhuma:

1. **Números de execução ligeiramente diferentes, todos a favor.** O relatório
   declara "camada rápida 26 testes em 0,22 s"; medi **0,11 s**. Declara "gitleaks
   500 commits"; medi **503** (três commits novos desde então), também sem achado.
   `496 unit tests` bate exatamente.
2. **`Requested 11357` × `11508`.** O bug 003 e a decision citam 11357, que é o
   número da B.5 (OQ19); a execução da própria C.7 registrou 11508. Os dois
   sustentam a mesma tese e nenhum é inventado — ver sugestão 3.
3. **O §4 do relatório declara os desvios de arquivo antes de eu perguntar**
   (spec, `.codeflow/decisions/`, `.codeflow/bugs/`, README do harness), e cada um
   se justifica: os três primeiros são o próprio remédio do BLOQUEANTE, que é
   defeito de coerência de spec e não se corrige sem editar a spec; o README é
   mandado pelo passo 4 da fase. `eval.yml` está na lista de arquivos da fase.
   Nenhum amplia o escopo funcional. Precedente idêntico aceito na OQ18 (D.1) e na
   OQ20 (C.7 t3).

---

**Próximo passo:** APROVADO conclui a fase C.7 (`tentativa: 4`, no teto do §2.11.4
destravado pelo owner em
`.codeflow/decisions/2026-08-08-quarta-tentativa-da-c7-autorizada-no-teto.md`).

Duas coisas seguem na mesa do owner e **não** são pendência desta fase: os limiares
do gate (sugestão 4) e o estrato `composto` (MdAPE 61,64%), que a D.3 esbarra ao
escrever o README de portfólio. E uma consequência declarada, que precisa ser lida
como escolha e não como surpresa: **enquanto o bug 003 estiver aberto, toda execução
agendada do `eval.yml` vai reprovar por esses três casos** — a análise por foto está
quebrada em produção no free tier, e isso agora tem registro próprio, com dono e
condição de fechamento, em vez de morar num `[x]` de relatório.
