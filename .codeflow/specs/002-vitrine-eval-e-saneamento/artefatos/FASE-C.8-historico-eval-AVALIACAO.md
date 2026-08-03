---
spec: 002-vitrine-eval-e-saneamento
fase: C.8
slug_fase: historico-eval
tentativa: 1
veredito: RESSALVAS
score: 9.2
threshold: 8.5
range_avaliado: 40e2941..f479f5d
---

# FASE C.8 — Avaliação independente

## 1. Veredito e score

**Veredito:** RESSALVAS · **Score:** 9.2 / threshold 8.5

`report.py` está bem construído: append-only imposto pelo código, `run_id`
derivado de commit + `sha` do dataset, gate que reprova caso vazio, série
temporal que anota sozinha o commit em que a versão de prompt muda. AC-16, lido
ao pé da letra, está satisfeito.

Três ressalvas, e a primeira é de substância: **as "duas execuções reais" do gate
são o mesmo relatório registrado duas vezes**, com `--git-commit` diferente. O
próprio executor levanta a questão na dúvida 2, o que é honesto — mas a resposta
é que não bastam.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 3 | AC-16 satisfeito na letra (`report.py:60-76` amarra commit, prompts com `sha`, modelo, amostragem, `sha` e `n` do dataset). Escopo travado respeitado: append-only imposto por `open("a")` + teste, nenhum segredo no registro, série em texto sem serviço externo. Desconto por C8-IMP-1 e C8-IMP-2. |
| 2 | Arquitetura e direção de dependências | 3 | 5 | `report.py` consome o JSON do runner e **não recalcula métrica nenhuma** — uma fonte de verdade. `carregar_historico`/`serie_temporal` funcionam sobre arquivo, sem banco e sem rede, e há teste que garante isso. |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | `test_o_registro_nao_carrega_segredo` varre a linha serializada por `gsk_`, `API_KEY`, `password`, `@gmail`. `.gitignore` recebeu `ultimo-relatorio.json` e `ultima-invariancia.json`, de modo que só o histórico curado é versionado. `gitleaks` sobre o range: zero achados. |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | A regra de imutabilidade de versão de prompt é imposta pelo teste de `sha` da C.1, não reimplementada aqui — o README só a documenta. |
| 5 | Padrões de domínio/aplicação | 2 | 5 | CLI com subcomandos (`registrar`/`serie`/`verificar`) no padrão dos demais módulos de `evals/`; `GateDoEvalError` como exceção nomeada, traduzida em `SystemExit(1)` só na fronteira do `main()`. |
| 6 | Local e nomes dos arquivos | 2 | 5 | `evals/report.py`, `evals/runs/history.jsonl`, `evals/runs/README.md`, `tests/unit/test_evals_report.py` — os declarados. |
| 7 | Qualidade de código | 2 | 5 | `mypy` strict limpo. `_git_commit_atual` degrada para `"desconhecido"` em vez de quebrar quando não há git — correto para um módulo que roda em container. |
| 8 | Testes e cobertura | 2 | 4 | 17 testes cobrindo a amarração, append-only, série sem rede, gate com caso vazio e com limiar rompido. Desconto: nenhum teste cobre a completude do que o passo 1 pede (tokens e latência), porque os campos não existem — C8-IMP-2. |
| 9 | Migration safety (se aplicável) | 2 | [—] | Nenhuma migration no range (NFR-7). |

Média ponderada das 8 dimensões aplicáveis: 92/20 = 4.6 → **9.2**.

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

**C8-IMP-1 — `backend/evals/runs/history.jsonl:1-2`: as duas linhas que satisfazem
o gate "histórico com ao menos duas execuções reais" são a mesma medição
registrada duas vezes.**

Medido:

```text
$ python3 -c "... history.jsonl ..."
1 cc849e71  n=10 mdape=3.89 sspb=1.25 <=10%=0.7
2 f479f5df  n=10 mdape=3.89 sspb=1.25 <=10%=0.7      <- idêntica à linha 1
3 298d7993  n=10 mdape=3.89 sspb=0.00 <=10%=0.9      <- pós-correção, legítima
```

E o próprio EXECUCAO §5 mostra o comando:

```text
$ python -m evals.report registrar --relatorio /tmp/rel.json --git-commit cc849e71...
$ python -m evals.report registrar --relatorio /tmp/rel.json --git-commit f479f5df...
```

O **mesmo arquivo** `/tmp/rel.json` alimentou as duas linhas. Não houve segunda
execução do runner: houve um segundo registro, com um rótulo de commit diferente.

O relatório defende a identidade dos números como demonstração de NFR-5
("reprodutibilidade"), e a defesa seria válida **se o runner tivesse rodado duas
vezes**. Rodar `registrar` duas vezes sobre o mesmo JSON não demonstra
reprodutibilidade de nada — demonstra que `json.load` é determinístico. A
demonstração real de NFR-5 existe e está na C.7 (mesma saída com `GROQ_API_KEY`
inválida, provando o replay); é ali que ela deveria ser citada.

Consequência prática: o `run_id` (`commit[:12]-dataset_sha[:12]`) foi projetado
para dizer "duas execuções do mesmo commit sobre o mesmo dataset são a mesma
medição". Aqui, duas medições idênticas receberam `run_id` diferentes porque o
commit foi passado à mão — o campo perdeu justamente a propriedade que o justifica.

**Correção sugerida:** a linha 3 (`298d7993`, pós-correção) **é** uma execução
distinta e legítima — métricas diferentes, código diferente. Basta uma segunda
execução real para fechar o gate com honestidade. Quando a quota voltar: rodar
`python -m evals.runner --cassettes --json`, registrar, e ajustar a §5 do EXECUCAO
para descrever o que foi feito. Alternativamente, remover a linha 2 do histórico
— mas isso colide com o append-only, então prefiro a primeira saída.

**C8-IMP-2 — `backend/evals/report.py:60-76`: a linha do histórico não registra
custo em tokens nem latência, que o passo 1 da fase lista explicitamente.**

`SPEC_002...md:1036-1039` pede que cada linha amarre:

> `run_id`, `git_commit`, versões e `sha` de cada prompt, modelo e parâmetros de
> amostragem, `sha` do dataset e `n`, métricas por estrato e agregadas, **custo em
> tokens e latência**.

`montar_linha` grava tudo, menos os dois últimos. Confirmei nas três linhas
gravadas: as chaves são `agregado, amostragem, casos_nao_verificados,
dataset_distribuicao, dataset_n, dataset_sha, falhas, git_commit, invariancia,
modelo, por_estrato, prompts, run_id`. Nem `tokens`, nem `latencia`.

AC-16, que é o gate formal, não menciona os dois campos — por isso isto é
IMPORTANTE e não BLOQUEANTE. Mas eles não são enfeite: token é o recurso que já
derrubou duas rodadas de eval (risco R5), e sem a série de consumo a decisão
"semanal ou diário" continua sem dado. O `AIClient` já loga
`tokens_in`/`tokens_out` a cada chamada (`ai_client.py:262-271`); o dado existe e
não é agregado.

**Correção sugerida:** acumular `prompt_tokens`/`completion_tokens` e o tempo de
parede por caso no runner (o `AIClientComCassette` é o ponto natural, já que
envolve toda chamada), publicá-los em `montar_relatorio` e propagá-los em
`montar_linha` como `custo: {tokens_in, tokens_out}` e `latencia: {mediana_s,
total_s}`. Isso também fecha a dúvida 2 da C.2 sobre `GROQ_MAX_TOKENS`.

## 5. Sugestões

- **O histórico gravado pela execução agendada nunca volta ao repositório.**
  `eval.yml:122-130` roda `evals.report registrar`, que escreve no
  `history.jsonl` do runner do Actions; o passo seguinte publica o arquivo como
  artifact (retenção 90 dias) e o job termina. Não há commit de volta. Ou seja: a
  "série temporal **versionada**" só cresce quando alguém copia o artifact e
  commita à mão. Duas saídas — um passo que commite a linha na `dev` (com
  `[skip ci]` e permissão de escrita), ou registrar no README de `runs/` que o
  fluxo é manual, com o comando pronto. Prefiro a primeira; sem ela, a série
  perde linhas por esquecimento, que é o modo de falha silencioso.
- **Limiares folgados** (dúvida 1 do EXECUCAO): `MDAPE_MAXIMO = 25` contra 3,89%
  medido e `FRACAO_MINIMA = 0.50` contra 90%. Concordo com a recomendação de
  esperar a C.4 — apertar sobre `n=10` não verificado trava ruído. Mas vale
  registrar os valores medidos num comentário junto das constantes, como a B.4 fez
  no `pyproject.toml`, para que apertar depois seja decisão com número.
- `invariancia` está `None` nas três linhas, porque o registro manual não passou
  `--invariancia`. O `eval.yml` passa (`:129`), então a agendada preenche. Vale um
  aviso no `registrar` quando o campo vier vazio.

## 6. Comandos rodados + saídas reais

Ambiente: container `caloria_backend`, branch `dev`, HEAD `e3a974a`.
`git merge-base --is-ancestor f479f5d HEAD` → OK.

```text
$ python3 -c "... chaves de cada linha do history.jsonl ..."
['agregado','amostragem','casos_nao_verificados','dataset_distribuicao','dataset_n',
 'dataset_sha','falhas','git_commit','invariancia','modelo','por_estrato','prompts','run_id']
  run_id= cc849e7172fe-426cb61f64af   commit= cc849e7172fe48ec93b8b0af9f60058fba0ac10a
  run_id= f479f5dfa9a0-426cb61f64af   commit= f479f5dfa9a00292ad39820032b3c4da98e695c6
  run_id= 298d79939a66-426cb61f64af   commit= 298d79939a664199f0e09a98331601856a643462
# sem 'custo'/'tokens'/'latencia' em nenhuma  → C8-IMP-2

$ python3 -c "... métricas por linha ..."
1 cc849e71  mdape=3.89 sspb=1.25 <=10%=0.7
2 f479f5df  mdape=3.89 sspb=1.25 <=10%=0.7    # idêntica → C8-IMP-1
3 298d7993  mdape=3.89 sspb=0.00 <=10%=0.9

# como o arquivo cresceu, commit a commit
$ git log --oneline --follow -- backend/evals/runs/history.jsonl
e3a974a chore(evals): registra a execucao pos-correcao no historico
6050dd8 docs(specs): fecha os gates de c.5 a c.8, b.4 e d.5 com medicao real
f479f5d chore(evals): registra a primeira execucao real no historico
$ for c in cc849e7 f479f5d e3a974a; do git show $c:backend/evals/runs/history.jsonl | wc -l; done
0 / 1 / 3      # append-only confirmado: o arquivo só cresce

# append-only e gate, pelos testes
$ docker compose -f docker-compose.dev.yml exec -T backend pytest --cov=app --cov-report=term -q
581 passed, 1 skipped, 5 warnings in 88.01s
Required test coverage of 72.0% reached. Total coverage: 73.10%

$ ... ruff check . && ... ruff format --check . && ... mypy app/ evals/
All checks passed! / 147 files already formatted / Success: no issues found in 81 source files

$ gitleaks detect --config .gitleaks.toml --log-opts="d8cc463~1..HEAD"
22 commits scanned.  no leaks found

$ git status --short
(limpo)
```

## 7. Itens da fase / DoD não atendidos

- **"Histórico com ao menos duas execuções reais"** (gate da fase e §9 do DoD) —
  atendido só na forma. Há três linhas; duas delas são o mesmo relatório
  (C8-IMP-1). A terceira é legítima, então falta **uma** execução para fechar de
  verdade.
- **Passo 1: custo em tokens e latência** — não entregue (C8-IMP-2).
- AC-16, lido literalmente, está satisfeito, e o registro **é** rastreável.

## 8. Divergências entre o relatório e o código real

1. **"Duas execuções reais registradas, em dois commits reais"** (EXECUCAO §5 e
   checklist §6) — a evidência colada no próprio relatório mostra o mesmo
   `/tmp/rel.json` nas duas invocações. A afirmação vai além do que o comando
   demonstra. A dúvida 2 do executor tangencia o ponto ("não vieram do `eval.yml`"),
   mas a questão maior não é a origem no Actions: é que houve uma medição, não
   duas.
2. **"Nasce vazio"** (§2, sobre `history.jsonl`) — confere: em `cc849e7` o arquivo
   tem 0 linhas.
3. O resto confere. Verifiquei append-only no histórico do git, o gate reprovando
   caso vazio, a ausência de segredo e a série sendo gerada sem rede.
