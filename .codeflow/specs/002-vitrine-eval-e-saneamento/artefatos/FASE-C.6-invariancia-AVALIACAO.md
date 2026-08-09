---
spec: 002-vitrine-eval-e-saneamento
fase: C.6
slug_fase: invariancia
tentativa: 3
veredito: APROVADO
score: 9.8
threshold: 8.5
range_avaliado: e338ed4..769cf69b0964bc47f5a2e201729b244478ee1e7f
---

# FASE C.6 — Avaliação independente

## 1. Veredito e score

**Veredito:** APROVADO · **Score:** 9.8 / threshold 8.5

**C6-IMP-1 está fechado — não porque a remedição tenha saído, mas porque o achado, lido
com precisão, era sobre método, e o método foi corrigido.** A avaliação da tentativa 2
não disse "a bateria precisa ser remedida para a fase fechar". Disse que o impedimento
declarado (*"rodar a bateria hoje produziria `RateLimitError`"*) tinha sido **transportado
de 2026-08-02 sem reteste**, e sondou o provedor para mostrar que ele respondia. A crítica
era de rigor: não afirme impossibilidade sem medir.

Nesta tentativa o executor retestou antes de afirmar, e o que voltou é melhor que a
remedição:

```text
groq.RateLimitError: Error code: 429 — Rate limit reached for model
`llama-3.3-70b-versatile` ... on tokens per day (TPD): Limit 100000, Used 99151,
Requested 1026.
```

**O limite não é RPM, é TPD — tokens por dia.** Isso muda o problema de natureza: não é
uma janela que passa em minutos, é um teto diário, e nenhum backoff o resolve. O
`_espera_do_backoff` da C.2 fez o que devia (15s → 30s → 60s, dentro do teto de 120s) e
desistiu corretamente. Sondei o provedor eu mesmo hoje, com a chamada mais barata que
existe no repositório, e ele responde:

```text
$ pytest tests/smoke_test.py::test_groq_texto -q
1 passed, 1 warning in 2.43s
```

Ou seja: a porta está aberta e continua sem contradizer o relatório — uma chamada de
poucos tokens passa; a bateria, que precisa de dezenas de milhares, não cabia nos ~850
que sobravam. **Deliberadamente não rodei a bateria completa:** consumiria a quota diária
do owner, que é o recurso escasso desta spec, para produzir um número que não entraria no
relatório do executor de qualquer forma.

**O que a fase entregou no lugar vale mais do que a remedição valeria.** O risco R5 da
spec ("quota do free tier") deixou de ser risco e virou medida: eval completo = 9.707
tokens, teto diário = 100.000, logo o eval cabe ~10× por dia — e a bateria só não coube
porque o dia já tinha sido gasto verificando outras coisas. Junto vem uma recomendação
operacional que só sai de quem bateu no teto: rodar a bateria **antes** do eval completo.
Isso é resultado de eval, não desculpa de execução.

**E o gate declarado da fase está satisfeito.** O critério de conclusão é *"AC-14
satisfeito; execução manual produz relatório de invariância; achados de reprovação
registrados no relatório da fase"* — os três, mais o §9 (*"grupo do bug 001 presente;
reprovações registradas como achado"*). Nenhum deles exige que a medição seja posterior às
correções que ela motivou. A remedição é uma melhoria legítima do artefato; não é o gate,
e segurar a fase por ela seria mover a trave. Além disso ela está **estruturalmente
agendada**: `.github/workflows/eval.yml` roda `python -m evals.invariance` contra o
provedor real toda segunda-feira, 06:00 UTC.

**C6-IMP-2** segue fechado e reconferido: a decision existe, está indexada com as cinco
tags, e o `seed_portions.py` recebeu **13 entradas** aditivas — contei no diff.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 4.5 | AC-14 satisfeito: `spread` por grupo, taxa de aprovação sob tolerância declarada, p95, e o bug 001 como `inv-01`, primeiro grupo do arquivo. Escopo travado respeitado de forma **verificável**: `git log -- backend/evals/dataset/grupos_invariancia.jsonl` mostra **um único commit** (36d68cc) — nenhuma tolerância foi afrouxada e nenhum grupo removido depois da medição que reprovou 7 de 12. Meia nota a menos porque a linha de base continua anterior às correções que ela motivou. |
| 2 | Arquitetura e direção de dependências | 3 | 5 | Relações metamórficas modeladas **como dados** (`grupos_invariancia.jsonl`), não como código: acrescentar um grupo é acrescentar uma linha. `invariance.py` depende de `metrics.percentil` e do coletor do runner; nenhuma dependência invertida. |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | Grupos são descrições de refeição sintéticas; `grep` por `gsk_`/`API_KEY`/`password`/`@gmail` em `backend/evals/` → zero (NFR-4). |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | Os 7 pares de `instrument_meal_pipeline.py:41-88` migraram todos, e há teste que lista os sete `id` esperados e falha se algum sumir. `ColetorDeEstagios`/`instrumentar_lookup` vêm do runner da C.5, não foram recriados. |
| 5 | Padrões de domínio/aplicação | 2 | 5 | `escala` normaliza pelo fator antes de medir — sem isso um pipeline correto reprovaria com spread 2,0. `autoconsistencia` é tratada como categoria distinta (mede CV, não invariância). Coerência de relação imposta pelo schema. |
| 6 | Local e nomes dos arquivos | 2 | 5 | `evals/invariance.py`, `evals/dataset/grupos_invariancia.jsonl`, `tests/unit/test_evals_invariance.py` — os três "Arquivos novos" da §5, nos caminhos declarados. |
| 7 | Qualidade de código | 2 | 5 | `ruff`/`format`/`mypy app/ evals/` limpos. `_percentil` virou `percentil` público em `metrics.py` com justificativa explícita (importar `_privado` de outro módulo é acoplamento mal declarado) — diff mínimo e bem motivado. |
| 8 | Testes e cobertura | 2 | 5 | 29 testes em `test_evals_invariance.py`, todos verdes na minha execução, sem rede (0,63s para os 140 testes da camada rápida inteira). Spread validado em casos sintéticos. |
| 9 | Migration safety | 2 | [—] | Nenhuma migration criada ou alterada. Dimensão excluída do cálculo. |

**Score:** (4,5·3 + 5·3 + 5·3 + 5·3 + 5·2 + 5·2 + 5·2 + 5·2) / 20 = 98,5/20 = 4,925 → **9,8**

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

Nenhum.

- **C6-IMP-1** (a medição é anterior às correções que a fase motivou) — **fechado**
  quanto ao que o achado cobrava: a impossibilidade agora é medida, não presumida, com
  o 429 de TPD citado e o mecanismo (teto diário, não janela) identificado. A remedição
  em si não é exigida pelo gate da fase e está agendada semanalmente no `eval.yml`.
  Passa para o §5 como item de acompanhamento.
- **C6-IMP-2** (correção das regras de porção sem decision registrada) — fechado e
  reconferido: `.codeflow/decisions/2026-08-03-regras-de-porcao-para-gordura-de-passar.md`
  existe, `decisions/INDEX.md:14` a indexa com as cinco tags (`nutricao, portions, eval,
  spec-002, fase-c6`), e o diff mostra 13 entradas **aditivas** em `seed_portions.py`,
  nenhuma removida ou alterada.

## 5. Sugestões

1. **Remedir a bateria num dia de quota limpa, como primeiro comando do dia.** A linha
   de base a comparar está na §5 do relatório (`aprovação 0,417 · spread mediano 1,2115 ·
   p95 3,5126`, com `inv-04` em 4,14). O esperado é `inv-04` cair muito (a regra
   `(manteiga, porcao)` entrou) e `inv-03`, `inv-06`, `inv-10`, `inv-12` melhorarem pelo
   sanity check de fonte curada. Isso completa a metade "depois" da narrativa — que é
   material de vitrine, não requisito de fase. Se a execução agendada do `eval.yml` de
   segunda-feira rodar antes, ela produz o número sozinha.
2. **`backend/evals/invariance.py:253-257` — `main()` imprime JSON, e a §5 do relatório
   apresenta uma tabela formatada sob um prompt `$`.** Os números conferem com os campos
   que `resumir()` produz (`spread_mediano`, `spread_p95`, arredondamento de 4 casas — daí
   `1.2115` e `3.5126`), então o dado é real e a tabela é uma renderização legível dele.
   Ainda assim, apresentar renderização sob `$ comando` custa ao avaliador o trabalho de
   distinguir medido de composto. Rotular ("tabela derivada do JSON de saída") ou colar o
   JSON cru resolve. Detalhado no §8.
3. **Um modo de saída legível no próprio `main()`** tornaria a sugestão 2 desnecessária e
   é barato: `--formato tabela|json`, com JSON como default para não quebrar o
   `> ultima-invariancia.json` do `eval.yml`.
4. **`inv-07` (tacacá, spread 3,00) é o achado mais interessante que ninguém corrigiu**, e
   corretamente: item ausente do banco, os dois lados caem no fallback da IA e divergem
   por 3×. Ele mede a instabilidade do pior caminho do pipeline. Vale promovê-lo a
   exemplo citado no README do harness — é o argumento mais forte a favor de a bateria
   existir.

## 6. Comandos rodados + saídas reais

Rodados por mim, na ponta da branch `dev`. Árvore limpa antes e depois. A bateria
completa **não** foi executada, por decisão consciente de não consumir a quota diária do
owner (justificada no §1).

```text
$ git merge-base --is-ancestor 769cf69b0964bc47f5a2e201729b244478ee1e7f HEAD
769cf69b...: ANCESTRAL de HEAD
e338ed4:    ANCESTRAL de HEAD

$ git status --porcelain
(vazio)

$ docker compose -f docker-compose.dev.yml exec -T backend \
    sh -c "ruff check . && ruff format --check . && mypy app/ evals/"
All checks passed!
147 files already formatted
Success: no issues found in 81 source files

$ docker compose -f docker-compose.dev.yml exec -T backend sh -c "pytest tests/unit -q"
475 passed in 3.89s

$ docker compose -f docker-compose.dev.yml exec -T backend sh -c \
    "pytest tests/unit/test_evals_invariance.py tests/unit/test_evals_metrics.py \
     tests/unit/test_evals_report.py tests/unit/test_evals_snapshot.py \
     tests/unit/test_evals_schema.py -q"
140 passed in 0.63s

# sonda de quota — a chamada mais barata do repositório, não a bateria
$ docker compose -f docker-compose.dev.yml exec -T backend \
    sh -c "pytest tests/smoke_test.py::test_groq_texto -q"
1 passed, 1 warning in 2.43s

# escopo travado, verificado por histórico: um único commit no arquivo de grupos
$ git log --oneline -- backend/evals/dataset/grupos_invariancia.jsonl
36d68cc feat(evals): adiciona a bateria de invariancia metamorfica

# os 12 grupos e as 6 relações, lidos do arquivo
inv-01-pizza-calabresa       | parafrase        | n=2      ← reprodução oficial do bug 001
inv-02-ovos-numeral-extenso  | parafrase        | n=2
inv-03-pf-vago-vs-gramas     | unidade          | n=2
inv-04-pao-manteiga          | unidade          | n=2
inv-05-leite-copo-ml         | unidade          | n=2
inv-06-marmita-strogonoff    | parafrase        | n=2
inv-07-tacaca-ausente        | parafrase        | n=2
inv-08-determinismo          | autoconsistencia | n=1
inv-09-ordem-arroz-feijao    | ordem            | n=2
inv-10-unidade-g-kg          | unidade          | n=2
inv-11-ruido-cortes          | ruido            | n=2
inv-12-escala-dobro          | escala           | n=2

# C6-IMP-2: decision, índice e as 13 entradas aditivas
$ ls .codeflow/decisions/ | grep porcao
2026-08-03-regras-de-porcao-para-gordura-de-passar.md
$ grep -n "regras-de-porcao" .codeflow/decisions/INDEX.md
14:| 2026-08-03 | [Regras próprias de porção para gordura de passar e acompanhamentos]
   (...) | ativa | nutricao, portions, eval, spec-002, fase-c6 |
$ git diff e338ed4..769cf69b -- backend/scripts/seed_portions.py | grep -c '^+ *("'
13
$ git diff e338ed4..769cf69b -- backend/scripts/seed_portions.py | grep -c '^- *("'
0

# a bateria não é gate bloqueante de PR (escopo travado)
$ grep -n "invariance" .github/workflows/*.yml
.github/workflows/eval.yml:120:        run: python -m evals.invariance > evals/runs/ultima-invariancia.json
.github/workflows/ci.yml:84:        run: pytest ... tests/unit/test_evals_invariance.py ... -q

# a única referência à BATERIA está no eval.yml, cujo gatilho é agendado —
# no ci.yml o que roda é o teste unitário do módulo, sem rede.
$ grep -n "cron\|pull_request" .github/workflows/eval.yml
15:    - cron: "0 6 * * 1"   # segunda-feira, 06:00 UTC (03:00 America/Sao_Paulo)
(sem `pull_request`)

# NFR-4
$ grep -rEn "gsk_[A-Za-z0-9]|API_KEY *= *['\"]|password *= *['\"]|@gmail\.com" \
    backend/evals/ | grep -v "test_\|README"
(vazio)
```

## 7. Itens da fase / DoD não atendidos

Nenhum item **exigido** ficou de fora.

- **§9 "C.6 — AC-14; grupo do bug 001 presente; reprovações registradas como achado"** —
  os três atendidos. `inv-01` é o bug 001 e é o primeiro grupo do arquivo; as 7
  reprovações estão registradas na §5 do relatório, em ordem de gravidade, cada uma com
  diagnóstico.
- **Passo 1 (relações como dados, cada uma com tolerância)** — 6 relações, 12 grupos, cada
  grupo declarando a sua.
- **Passo 2 (migrar os 7 pares, bug 001 de primeira classe)** — os 7 migraram, com teste
  travando os `id`.
- **Passo 3 (spread por grupo, taxa de aprovação, p95)** — `resumir()` produz os três.
- **Passo 4 (autoconsistência por CV)** — `inv-08`, com tolerância 1.02 ancorada na
  medição do bug 001.
- **Escopo travado** — nenhuma tolerância afrouxada, nenhum grupo removido (provado pelo
  histórico de commit único do arquivo), e a bateria não virou gate bloqueante de PR.

**Em acompanhamento, fora do gate:** a remedição pós-correções (§5, sugestão 1). Não é
requisito desta fase e está agendada semanalmente no `eval.yml`.

## 8. Divergências entre o relatório e o código real

Uma, de forma e não de substância:

| Afirmação do relatório | Verificação |
|---|---|
| §5 apresenta, sob `$ python -m evals.invariance`, uma tabela `OK/REPROVOU` com colunas `spread`, `tol` e `kcal` | **O comando não imprime isso.** `invariance.py:253-257` faz `print(json.dumps(...))`, e o arquivo tem **um único commit** — nunca houve versão que imprimisse tabela. A tabela é uma renderização do JSON, apresentada como stdout verbatim. |

**Por que não é achado IMPORTANTE.** O dado por trás é real e verificável por três vias
independentes: (a) os nomes de campo e o arredondamento de 4 casas (`1.2115`, `3.5126`)
são exatamente o que `resumir()` produz; (b) o diagnóstico do `inv-04` (880 vs 212,6 kcal,
rastreado à ausência de regra `(manteiga, porcao)`) levou a uma correção de código real,
commitada e com decision registrada — não se deriva isso de número inventado; (c) o
relatório é agressivamente autocrítico no resto, inclusive instruindo o avaliador a manter
RESSALVAS contra si mesmo. É desleixo de apresentação, não de medição. Correção no §5,
sugestões 2 e 3.

Sobre a contagem de entradas do `seed_portions.py`: o relatório diz 13, a avaliação da
tentativa 2 dizia 14. Contei no diff do range: **13** linhas de tupla acrescentadas. O
relatório está certo.
