---
spec: 002-vitrine-eval-e-saneamento
fase: C.5
slug_fase: runner-metricas
tentativa: 1
veredito: RESSALVAS
score: 9.5
threshold: 8.5
range_avaliado: 0d4d9ec..e338ed4
---

# FASE C.5 — Avaliação independente

## 1. Veredito e score

**Veredito:** RESSALVAS · **Score:** 9.5 / threshold 8.5

`metrics.py` é o melhor arquivo do Track C: funções puras, justificativa
estatística correta e testes contra valor calculado à mão. E a fase entregou o
que o projeto inteiro existia para conseguir — o primeiro defeito de qualidade de
IA nomeado com número, não com opinião.

Duas ressalvas. A mais séria é uma armadilha de validade introduzida pela própria
rodada de correção: `--repeticoes N` combinado com `--cassettes` em modo replay
reporta ruído do modelo igual a zero **por construção**, e nada no relatório
avisa disso.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 5 | AC-13 completo: MdAPE e SSPB por estrato e agregado, `n` e IC95 por estrato (`runner.py:236-251`), macros em MAE com tolerância **absoluta** (`_mae_macros`, `TOLERANCIA_MACRO_G = 5.0`). Escopo travado: MdAPE é a headline e `mape()` existe só para exibir o contraste (`metrics.py:65-71`); nenhum percentual para macros; limiares de `test_golden_set.py` intocados. |
| 2 | Arquitetura e direção de dependências | 3 | 4 | `metrics.py` é puro e não conhece o pipeline — testável sem banco, sem rede, sem IA, como a fase exige. Desconto: `runner.py:168-171` chama `parser._identify_foods` e `parser._lookup_and_fill`, dois métodos privados do `MealParser` (§5). |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | Nenhum segredo no relatório emitido; `montar_relatorio` publica modelo, amostragem e `sha` de prompt, nunca chave. `gitleaks` sobre o range: zero achados. |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | Usa o `MealParser` **de produção**, não uma reimplementação — o que o eval mede é o que o usuário recebe. `instrumentar_lookup` reusa o padrão de monkeypatch de `scripts/instrument_meal_pipeline.py:118` e devolve a original para o chamador restaurar (`runner.py:439-440`, no `finally`), evitando vazamento entre execuções. |
| 5 | Padrões de domínio/aplicação | 2 | 5 | Dataclasses para resultado, enum para estrato, CLI por `argparse` como os demais módulos de `evals/`. Estrato vazio vira `n=0` em vez de sumir do relatório — decisão pequena e certa. |
| 6 | Local e nomes dos arquivos | 2 | 5 | `evals/metrics.py`, `evals/runner.py`, `tests/unit/test_evals_metrics.py` — exatamente onde a fase pediu. |
| 7 | Qualidade de código | 2 | 4 | `mypy` strict limpo; funções curtas; os docstrings explicam a escolha estatística, não a mecânica. Desconto pelo C5-IMP-1, que é de projeto de medição e não de estilo. |
| 8 | Testes e cobertura | 2 | 5 | 31 testes com o valor esperado escrito no comentário. O teste da assimetria do APE (erro de 2× e de ½× dão o mesmo módulo em log accuracy ratio e APEs de 100% e 50%) é a prova de que a escolha da métrica headline não é arbitrária. |
| 9 | Migration safety (se aplicável) | 2 | [—] | Nenhuma migration no range (NFR-7). |

Média ponderada das 8 dimensões aplicáveis: 95/20 = 4.75 → **9.5**.

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

**C5-IMP-1 — `backend/evals/runner.py:184-189` + `:340-351`: com `--cassettes` em
replay, o coeficiente de variação é zero por construção, e o relatório o publica
como se fosse medição de ruído do modelo.**

O `--repeticoes N` foi acrescentado na rodada de correção justamente para separar
duas fontes de erro (`CORRECOES-2026-08-02-POS-VALIDACAO.md` §3): erro do
pipeline contra a referência, e ruído de amostragem do modelo. O segundo sai em
`ruido_do_modelo.cv_mediano`.

Mas o cassette é indexado pelo `sha256` do payload
(`evals/cassettes/__init__.py:107-116`), e as N repetições de um caso enviam
**exatamente o mesmo payload**. Em replay, `reproduzir()` devolve N vezes a mesma
string gravada. Logo:

- `medidas` fica com N valores idênticos;
- `statistics.stdev(medidas)` = 0;
- `cv` = 0.0;
- `_resumo_do_ruido` reporta `cv_mediano: 0.0`, `cv_maximo: 0.0`.

Um leitor do relatório conclui "o modelo é determinístico" a partir de um número
que só diz "o disco é determinístico". E é o cenário mais provável de acontecer:
replay é a forma barata de rodar, e é o que a documentação do runner incentiva.

Vale notar o que **não** é o problema: no `eval.yml` a execução agendada roda com
`EVAL_RECORD_CASSETTES=1`, e nesse modo o envelope chama o provedor real a cada
repetição (`cassettes/__init__.py:91-100`), de modo que o CV é legítimo. O
defeito é a execução manual em replay, que não distingue os dois casos.

**Correção sugerida** (qualquer uma resolve; a primeira é a mais barata):

1. Em `executar()`, quando `usar_cassettes and not gravacao_ligada() and
   repeticoes > 1`, emitir aviso e forçar `repeticoes = 1` — repetir em replay
   não produz informação nenhuma, só custo.
2. Ou propagar a origem do valor até `_resumo_do_ruido` e publicar
   `{"n": 0, "cv_mediano": None, "origem": "replay — CV não medível"}` em vez de
   zeros.

**C5-IMP-2 — o relatório da fase não distingue a execução em rede da execução em
replay ao apresentar os números "antes e depois" da correção.**

A tabela de §5 do EXECUCAO ("composto MdAPE 23,81% → 6,86%") é o resultado mais
citado desta spec, e a citação em `CORRECOES...md` §1 declara corretamente a
metodologia: `python -m evals.runner --cassettes`, mesmo dataset, mesmos
cassettes, só o código mudou. Isso é um desenho **bom** — é pareado, e isola a
mudança de código do ruído do modelo.

O que falta é a declaração da limitação que o desenho impõe: as correções são de
pós-processamento (o sanity check roda **depois** da resposta da IA), então o
replay as mede corretamente; mas qualquer correção futura que mude o payload
enviado **não** é medível por esse caminho, e comparar as duas coisas com o mesmo
vocabulário ("antes e depois") vai induzir erro. O README do harness tem a seção
certa para isso e é onde a limitação deveria estar registrada.

**Correção sugerida:** acrescentar ao `evals/README.md`, junto da análise de
poder, um parágrafo declarando o que o eval em replay mede (mudança de
pós-processamento, com pareamento perfeito) e o que ele **não** mede (qualquer
mudança de prompt ou de parâmetro de amostragem, que invalida os cassettes por
desenho).

## 5. Sugestões

- **Acoplamento a métodos privados.** `runner.py:168-171` e `invariance.py:220-221`
  chamam `_identify_foods` e `_lookup_and_fill`. É deliberado — o eval precisa dos
  estágios intermediários, e `parse()` só devolve o fim — mas significa que
  renomear um método privado do `MealParser` quebra o harness em silêncio, e o
  `mypy` não avisa que a fronteira foi cruzada. Promover os dois a públicos (ou
  expor um `analisar_por_estagios()` no parser) tornaria o contrato explícito. Não
  cabia nesta fase; cabe numa de arrumação do Track C.
- **`TOLERANCIA_MACRO_G = 5.0`** ficou folgada demais depois da correção (100%
  dentro de ±5 g nos três macros). A dúvida 2 do EXECUCAO propõe ±3 g na C.4 —
  concordo, e sugiro decidir isso **junto** do dataset real, não antes.
- **Os casos-semente descrevem "100 g de X"** (dúvida 3), o que não é como o
  usuário escreve. Vale mais que uma sugestão: o estrato `composto` só teve o
  defeito do sanity check exposto porque a descrição em gramas colide com a
  estimativa de porção inteira da IA. Dataset em medida caseira, como a OQ2 agora
  permite (POF → gramas), mede o caminho real e provavelmente revela outro
  conjunto de defeitos.
- `ape()` devolve 100.0 quando `previsto <= 0` (`runner.py:196`), o que trata
  "pipeline não devolveu nada" como "errou 100%". Defensável, mas mistura falha
  com erro; hoje só aparece se um caso retornar zero kcal sem levantar exceção.

## 6. Comandos rodados + saídas reais

Ambiente: container `caloria_backend`, branch `dev`, HEAD `e3a974a`.
`git merge-base --is-ancestor e338ed4 HEAD` → OK.

```text
$ docker compose -f docker-compose.dev.yml exec -T backend pytest --cov=app --cov-report=term -q
581 passed, 1 skipped, 5 warnings in 88.01s
Required test coverage of 72.0% reached. Total coverage: 73.10%

$ ... ruff check . && ... ruff format --check . && ... mypy app/ evals/
All checks passed! / 147 files already formatted / Success: no issues found in 81 source files

# a série temporal, gerada do histórico que este runner alimenta
$ python3 -c "... history.jsonl ..."
1 cc849e71  n=10 mdape=3.89 sspb=1.25 <=10%=0.7  amostragem={'max_tokens':8192,'seed':-1,'temperature':0.1}
2 f479f5df  n=10 mdape=3.89 sspb=1.25 <=10%=0.7  amostragem={'max_tokens':8192,'seed':-1,'temperature':0.1}
3 298d7993  n=10 mdape=3.89 sspb=0.00 <=10%=0.9  amostragem={...,'repeticoes':1,...}

A linha 3 é a pós-correção e confirma os números da tabela do EXECUCAO no
agregado: SSPB 1,25% → 0,00% e dentro de ±10% 70% → 90%.

# escopo travado: limiares do gate determinístico intocados
$ git diff --name-only 0d4d9ec..e338ed4 | grep -c "test_golden_set"
0
$ ... pytest tests/integration/test_golden_set.py -q
5 passed, 1 warning in 2.12s

$ git status --short
(limpo)
```

Não reexecutei o runner contra a rede: a quota do free tier da Groq está esgotada
(a própria rodada de correção bateu em `RateLimitError`, com log registrado). A
verificação que fiz foi sobre o código, sobre os testes e sobre o histórico
gravado — que é o artefato que o runner produz.

## 7. Itens da fase / DoD não atendidos

Nenhum item do gate. "AC-13 satisfeito; `make test-unit` verde; uma execução
manual do runner produz relatório com os três estratos" está cumprido — o estrato
`foto` aparece como `n=0`, que é o comportamento projetado e não uma omissão.

As duas ressalvas são de qualidade da medição, não de entrega.

## 8. Divergências entre o relatório e o código real

1. **`ruido_do_modelo` sob replay** — o EXECUCAO §7 dúvida 4 apresenta
   `--repeticoes` como a resposta ao achado `inv-08`, sem a ressalva de que o
   modo replay zera o CV por construção (C5-IMP-1). Não é afirmação falsa; é
   omissão de uma condição de validade que o leitor não tem como inferir.
2. **Contagens de teste** — §5 do relatório cita `323 passed` na suíte unitária da
   época; hoje a suíte inteira dá `581 passed, 1 skipped`. Evolução esperada.
3. O restante confere: verifiquei `mape()` existindo só para contraste, a
   tolerância absoluta nos macros, o `finally` que restaura o `lookup_food`
   original, e o `n`/IC95 por estrato.
