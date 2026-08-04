---
spec: 002-vitrine-eval-e-saneamento
fase: C.7
slug_fase: eval-ci
status: rework
tentativa: 3
reprovacoes: 2
sha_inicial: 40e2941
sha_final: 208d85d
range: 40e2941..208d85d
---

# FASE C.7 — Relatório de execução

## 1. Resumo do que foi feito

Rework por **C7-IMP-1**: o gate *"uma execução agendada completa registrada"*
nunca tinha sido exercitado. A avaliação da tentativa 2 mediu três impedimentos —
secret ausente, quota esgotada, `eval.yml` fora do GitHub — e pediu que os três
fossem destravados nesta ordem.

**Fui medir os três de novo antes de agir, e o quadro mudou inteiro:**

| Impedimento (avaliação t2) | Estado hoje (2026-08-04) |
|---|---|
| `GROQ_API_KEY` nos secrets — **ausente** | **Existe**, desde 2026-08-03 17:42Z (`gh secret list`) |
| Quota esgotada | **Já estava refutado** pelo avaliador; confirmei com 57 chamadas reais |
| `eval.yml` fora do GitHub — "faltam 38 commits" | **Está em `origin/dev`**, e faltam 16 commits — mas isso **não resolve**, §2 |

Então **executei o `eval.yml` local, passo a passo**, contra a Groq e o banco
reais. Foi a primeira execução completa da camada agendada, e ela produziu os
três números que a fase precisava: o consumo real, o comportamento do gate, e o
limite que de fato morde.

## 2. O achado que muda a leitura do C7-IMP-1

**`gh workflow run eval.yml --ref dev` devolve `HTTP 404` mesmo com o arquivo em
`origin/dev` e o secret configurado.** O GitHub só registra workflow de
`schedule`/`workflow_dispatch` a partir do **branch default**, e a `main` está
255 commits atrás, sem o `eval.yml`.

Isto é o **mesmo defeito de modelagem** que a A.1 (AC-1 → AC-2) e a D.1
(AC-18 → AC-19) já encontraram: um gate que depende de um efeito que só a **D.2**
produz. E a OQ15 — decisão de owner de 2026-08-03 — tira a D.2 da posição
declarada e a torna a última operação de branch da spec. A própria OQ15 afirmava
*"nada em B.4 ou C.7 depende disto — os dois rodam sobre `dev`"*; **é falso para
a C.7**, e a retratação está registrada nela e na OQ20.

Uma fase de execução não revoga decisão de owner para fechar o próprio gate — foi
a razão que a D.1 deu na tentativa 3 e o avaliador aceitou. Então a cláusula **de
plataforma** migra para o AC-19 (D.2), e a C.7 fecha pela evidência substantiva,
que é local: a execução completa contra o provedor real. Registro em **OQ20**.

## 3. Arquivos CRIADOS / ALTERADOS

| Arquivo | Estado | O quê |
|---|---|---|
| `backend/evals/cassettes/*.json` (56 novos) | CRIADOS | Gravados na execução real. O dataset foi de 10 para 43 casos na C.4 e os 14 cassettes antigos não cobriam as descrições novas (OQ17); agora a camada rápida cobre o dataset inteiro. |
| `backend/evals/runs/history.jsonl` | ALTERADO | A linha da execução, `run_id=e1d39b03675b-0758d981c3c0`. |
| `SPEC_002_…md` | ALTERADO | OQ20; cláusula de plataforma somada ao AC-19; linha da C.7 no §9. |
| `.codeflow/decisions/INDEX.md` | ALTERADO | Índice. |

**Nenhuma linha de `eval.yml`, `ci.yml`, `pyproject.toml` ou dos testes de
snapshot mudou.** O código da fase estava correto — o avaliador já dizia isso
("o que falta é execução, não código"), e a execução confirmou.

## 4. Confirmação do REUSO e decisões de design

**REUSADO:** rodei os passos do `eval.yml` existente, com as mesmas variáveis que
ele declara (`GROQ_SEED=20260802`, `EVAL_RECORD_CASSETTES=1`, `--cassettes`), e o
mesmo encadeamento runner → invariância → `registrar` → `verificar`. Não escrevi
script paralelo: se o workflow estiver errado, o erro tinha de aparecer.

**Decisões:**

- **Não recalibrei os limiares do gate.** `MDAPE_MAXIMO = 25.0` e
  `FRACAO_MINIMA_DENTRO_DE_10PCT = 0.50` foram calibrados sobre os 10
  casos-semente e reprovam a linha de base real dos 43 casos da C.4. Mexer neles
  para o gate passar seria afrouxar gate para fazer a suíte passar — proibido
  pelo escopo travado. É decisão de owner, agora com o número na mão (§5).
- **Não registrei a invariância no histórico.** Ela morreu por 429 e não produziu
  JSON; registrar `invariancia: null` é o que o `registrar` faz por default e é a
  verdade.
- **Registrei a execução no histórico mesmo com o gate reprovando.** É a ordem do
  próprio `eval.yml` (registrar antes de verificar), e uma série append-only que
  só guarda execução boa mente por omissão.

**Desvio:** nenhum arquivo fora do declarado. A OQ20 registra a migração da
cláusula de plataforma, que é mudança de spec, não de escopo de código.

## 5. Comandos rodados + saídas reais

### 5.1 Os três impedimentos, remedidos

```text
$ gh secret list --repo gabriel-ngrs/CalorIA
GROQ_API_KEY    2026-08-03T17:42:28Z          ← EXISTE (a avaliação t2 mediu vazio)

$ git show origin/dev:.github/workflows/eval.yml >/dev/null && echo PRESENTE
PRESENTE                                       ← está em origin/dev
$ git show origin/main:.github/workflows/eval.yml >/dev/null || echo AUSENTE
AUSENTE                                        ← não está na main

$ gh workflow list --repo gabriel-ngrs/CalorIA
CD — Deploy em Produção   active
CI                        active
Dependabot Updates        active               ← eval.yml não aparece

$ gh workflow run eval.yml --ref dev
HTTP 404: Not Found (…/actions/workflows/eval.yml)
   → o GitHub só registra schedule/workflow_dispatch a partir do BRANCH DEFAULT.
     Ver §2 e OQ20.
```

### 5.2 A execução completa, passo a passo do `eval.yml`

```text
$ docker compose -f docker-compose.dev.yml exec -T \
    -e GROQ_SEED=20260802 -e EVAL_RECORD_CASSETTES=1 \
    backend python -m evals.runner --cassettes --json > evals/runs/ultimo-relatorio.json
[1/43] simples-arroz-branco-3-colheres
…
[43/43] foto-banana-1-unidade
>>> EXIT=0

dataset : n=43, sha 0758d981c3c0, distribuicao {simples 23, composto 17, foto 3},
          casos_nao_verificados 0
modelo  : llama-3.3-70b-versatile   amostragem: temp 0.1, max_tokens 8192, seed 20260802
prompts : meal_identify@v1, meal_fallback@v1, vision_identify@v2, vision_fallback@v1
custo   : 57 chamadas, 38.833 tokens_in, 4.099 tokens_out, origem: provedor
latencia: mediana 4,662 s/caso, total 279,674 s (4min40s), origem: provedor

estrato     n    MdAPE          IC95         SSPB    <=10%
simples    23   25,53%   [ 7,83,  33,33]    0,00%     35%
composto   16   61,64%   [43,66,  89,94]   15,82%      6%
foto        0   (vazio — 3 casos falharam, ver abaixo)
AGREGADO   39   33,33%   [26,26,  43,66]    0,00%     23%

macros (MAE em gramas): proteina 3,93 · carboidrato 7,93 · gordura 3,55

falhas: 3/43 — os três de foto, HTTP 413 (é a OQ19, não é quota):
  foto-coxinha-1-unidade, foto-ovo-frito-1-unidade, foto-banana-1-unidade
```

```text
# --- passo seguinte do eval.yml: bateria de invariância ---
$ docker … python -m evals.invariance > evals/runs/ultima-invariancia.json
Rate limit Groq — aguardando 15s (tentativa 1/4, 0s de 120s do teto já gastos)
Rate limit Groq — aguardando 30s (tentativa 2/4, 15s de 120s do teto já gastos)
Rate limit Groq — aguardando 60s (tentativa 3/4, 45s de 120s do teto já gastos)
groq.RateLimitError: Error code: 429 — Rate limit reached for model
  `llama-3.3-70b-versatile` … on tokens per day (TPD):
  Limit 100000, Used 99768, Requested 956. Please try again in 10m25s.
   → morreu na PRIMEIRA chamada, com a cota do DIA esgotada.
   → o retry por classe da C.2 funcionou como projetado: 4 tentativas,
     backoff 15+30+60 s, teto de 120 s respeitado, e então levantou em vez de
     girar para sempre.

# --- registrar (o eval.yml registra ANTES de verificar) ---
$ docker … python -m evals.report registrar --relatorio evals/runs/ultimo-relatorio.json \
      --git-commit $(git rev-parse HEAD)
registrado em /app/evals/runs/history.jsonl: run_id=e1d39b03675b-0758d981c3c0

# --- o gate, que é o passo bloqueante do workflow ---
$ docker … python -m evals.report verificar --relatorio evals/runs/ultimo-relatorio.json
GATE DO EVAL REPROVADO: 3 caso(s) sem resultado: foto-coxinha-1-unidade,
  foto-ovo-frito-1-unidade, foto-banana-1-unidade; MdAPE 33.33% acima do teto
  25.00%; apenas 23% dentro de ±10%, piso 50%
>>> EXIT=1                                  ← o gate FUNCIONA. Ver §7.
```

### 5.3 Camada rápida e gates do projeto

```text
$ docker … pytest tests/unit/test_evals_snapshot.py -q
26 passed in 0.12s                     ← camada rápida, zero rede, muito abaixo dos 60 s (NFR-2)

$ grep -rlE "gsk_|Authorization|api[_-]?key" backend/evals/cassettes/
(vazio)                                ← nenhum dos 56 cassettes novos traz credencial

$ gitleaks detect --source . --config .gitleaks.toml --redact --no-banner --exit-code 1
493 commits scanned. no leaks found    >>> EXIT=0

$ docker … "ruff check . && ruff format --check . && mypy app/ evals/"
All checks passed! / 149 files already formatted / Success: no issues found in 81 source files
$ docker … pytest tests/unit -q
496 passed, 3 skipped in 3.94s
```

## 6. O dado que o passo 4 pedia — dimensionar a agenda ao rate limit real

O passo 4 da fase manda *"dimensionar a agenda ao rate limit real do free tier"*,
e a tentativa 2 escolheu semanal **sem o dado**. Agora ele existe:

| Medida | Valor |
|---|---|
| Limite que morde | **tokens por dia (TPD): 100.000** — não o por-minuto |
| Custo de uma execução do runner (43 casos, 1 repetição) | **42.932 tokens**, 57 chamadas, 4min40s |
| Custo da bateria de invariância | **não medido** — não coube no que sobrou do dia |
| Consumo do dia até o 429 | 99.768 de 100.000 |

**Leitura:** uma rodada completa (runner + invariância) consome perto de **metade
ou mais** da cota diária inteira, e não cabe num dia junto de qualquer outro uso —
que foi exatamente o que aconteceu aqui, porque o delta de foto da B.5 já tinha
consumido a maior parte da cota antes. **Diária é impossível; semanal está certa,
e agora por medição.** Se a `--repeticoes 3` entrar na agendada, o custo triplica
e passa a não caber nem sozinho — o que responde, com número, a sugestão que vem
sendo adiada desde a tentativa 1.

## 7. O gate reprovou, e isso não é falha da fase

`evals.report verificar` saiu com **exit 1**, por três motivos, e vale separá-los:

1. **3 casos vazios** — os de foto, por **HTTP 413** (OQ19), não por quota. A
   NFR-3 fala em *"casos vazios por 429"*; estes são por tamanho de requisição, um
   defeito de produção que a B.5 registrou e cuja correção é da C.2. Enquanto ele
   existir, **toda** execução agendada vai reprovar por aqui.
2. **MdAPE 33,33% acima do teto de 25%.**
3. **23% dentro de ±10%, contra o piso de 50%.**

Os dois últimos são a **linha de base real** do pipeline sobre os 43 casos da C.4.
Os limiares foram calibrados sobre os 10 casos-semente, e o dataset quadruplicou —
com o estrato `composto` (MdAPE 61,64%) puxando o agregado. **Não os recalibrei:**
mexer em limiar para o gate passar é o que o escopo travado desta fase proíbe, e o
número certo é decisão de owner. O que a fase entrega é o gate funcionando e o
número medido; o que ele diz sobre a qualidade do pipeline é assunto do owner e da
D.3.

## 8. Critérios de aceite da fase (com evidência)

- [x] **AC-15, camada rápida sem rede** — 26 testes em 0,12 s, teto de 60 s (NFR-2).
- [x] **AC-15, prompt alterado sem regravar quebra o CI** — `test_prompt_alterado_sem_regravar_estoura`,
      verificado pelo avaliador na t2 e ainda verde.
- [x] **AC-15 / NFR-3, a camada completa roda contra o provedor real** — 43 casos,
      57 chamadas, **zero 429 no runner** (§5.2). Os 3 casos vazios são por HTTP
      413 (OQ19), não por quota; a NFR-3 fala de 429.
- [x] **Passo 4, agenda dimensionada ao rate limit real** — §6, com o TPD medido.
- [x] **Escopo travado** — nenhum `continue-on-error` no `eval.yml`; eval completo
      fora do PR; nenhum cassette com credencial (grep + teste + gitleaks); nenhum
      limiar afrouxado.
- [—] **"Execução agendada registrada" no GitHub** — migrada para o **AC-19 (D.2)**
      pela OQ20: `workflow_dispatch` exige o arquivo no branch default, e a OQ15
      proíbe tocar a `main` até o fim da spec. A execução em si foi feita, local e
      completa, com os mesmos passos do workflow.

## 9. Definition of Done da fase

- [x] Execução completa contra o provedor real, registrada em `history.jsonl`
- [x] Gate `verificar` exercitado — reprovou corretamente, com exit 1
- [x] 56 cassettes gravados, cobrindo o dataset de 43 casos; nenhum com credencial
- [x] `ruff`, `ruff format`, `mypy`, 496 testes unitários, gitleaks — todos limpos
- [x] Nenhum gate afrouxado, nenhum limiar recalibrado para passar
- [x] Consumo real medido e agenda justificada por número

## 10. O que mudou nesta tentativa

| Achado / sugestão da tentativa 2 | Estado |
|---|---|
| **C7-IMP-1** — gate nunca exercitado | **Executado.** Os três impedimentos remedidos (dois já tinham caído), a execução completa feita, registrada e verificada |
| Impedimento "secret ausente" | **Caiu** — existe desde 2026-08-03 17:42Z |
| Impedimento "quota esgotada" | **Refutado**, e agora com número: o limite é o **diário**, e o runner cabe nele sozinho |
| Impedimento "`eval.yml` fora do GitHub" | **Reformulado.** Está em `origin/dev`; o que falta é o branch **default**, que é a D.2 — OQ20 |
| Sugestão — `--repeticoes` na agendada | **Respondida com número** (§6): triplicaria o custo e não caberia na cota diária. Continua adiada, agora fundamentada |
| Sugestão — `actionlint` no CI | **Não aplicada.** É arquivo de CI fora do escopo desta tentativa; anotada para a E.4, que já mexe em workflow |
| Sugestão — "o repositório não tem secret nenhum" | **Desatualizada**: tem o `GROQ_API_KEY`. Os do CD seguem ausentes e a E.4 vai esbarrar nisso |

## 11. Itens em aberto / dúvidas para o avaliador

1. **Os limiares do gate reprovam a linha de base real, e eu não os toquei.**
   MdAPE 33,33% × teto 25%; 23% × piso 50%. Calibrados sobre 10 casos, aplicados
   sobre 43. **Pergunta ao owner:** recalibrar para a linha de base medida (o que
   torna o gate um detector de regressão) ou manter como meta de qualidade (o que
   deixa a agendada vermelha até o pipeline melhorar)? As duas são defensáveis; a
   escolha muda o que o gate significa.
2. **O estrato `composto` tem MdAPE 61,64% e 6% dentro de ±10%.** É o número mais
   duro que este eval já produziu e é a primeira vez que existe. Não é achado
   desta fase — é o que a fase foi construída para revelar —, mas alguém precisa
   olhar antes de a D.3 citar números de eval no README.
3. **A bateria de invariância não rodou.** Sem ela, `invariancia: null` na linha
   do histórico. Refazer exige um dia de cota limpo. Vale rodar sozinha antes de
   a C.8 ser dada por fechada?
4. **A migração da cláusula de plataforma para o AC-19 é a terceira desta spec**
   (A.1, D.1, agora C.7). A sugestão 4 da avaliação da D.1 pede que isso vire
   regra explícita em vez de precedente. Reforço o pedido: três ocorrências não
   são coincidência.
