---
spec: 002-vitrine-eval-e-saneamento
fase: C.5
slug_fase: runner-metricas
status: rework
tentativa: 3
reprovacoes: 2
sha_inicial: 0d4d9ec
sha_final: 769cf69b0964bc47f5a2e201729b244478ee1e7f
range: 0d4d9ec..769cf69b0964bc47f5a2e201729b244478ee1e7f
---

# FASE C.5 — Relatório de execução

## Tentativa 3 — o que mudou

Veredito da tentativa 2: **RESSALVAS**, score 9.5. Os dois achados da tentativa 1
foram confirmados fechados; um achado novo entrou. Ele está fechado.

### C5-IMP-3 — a latência era publicada sem origem — **FECHADO**

**Aceito, e o achado é bom: é o meu próprio C5-IMP-1 no campo irmão.** Corrigi o
ruído, corrigi o custo, e deixei a latência publicando `mediana_s: 0.073` sem
marcação — número certo sobre a coisa errada. O cenário descrito é o que importa: a
linha vai para a série append-only da C.8, e uma medição de disco ao lado de uma de
rede se lê como ganho de performance que nunca existiu.

`_resumo_da_latencia` agora recebe `origem` e a publica, espelhando `resumo_do_custo`.
A origem sai do próprio custo em `montar_relatorio` — uma definição só de "de onde veio
esta execução", dois consumidores, sem chance de divergirem.

Medido nas duas origens, hoje:

```text
# replay
latencia: {'n': 10, 'mediana_s': 0.058, 'total_s': 1.041,  'origem': 'replay'}
# provedor real
latencia: {'n': 10, 'mediana_s': 4.829, 'total_s': 72.302, 'origem': 'provedor'}
```

**83× de diferença.** Era exatamente essa a leitura falsa que o achado antecipou.

Três testes novos (`TestOrigemDaLatencia`): a origem acompanha o número, execução sem
custo medido não finge origem (`"nao medido"`), e execução vazia ainda declara a
origem em vez de devolver um dicionário mudo.

### Sobre a sugestão 3 do achado — `mediana_s: None` em replay

**Não adotada, e declaro a razão em vez de omitir.** A analogia com `ruido_do_modelo`
não se sustenta inteira: o CV em replay é zero *por construção* — não há informação
nenhuma ali. A latência em replay **é** informação real, só que sobre outra coisa: é o
tempo de execução do harness, que é o número que sustenta a NFR-2 e que se quer ver
subir quando o dataset crescer. Anular perderia isso. Com `origem: "replay"` explícito,
o leitor tem o número e sabe o que ele mede.

Se o avaliador discordar, a mudança é de uma linha e não tenho apego.

### Evidência

```text
$ ... pytest tests/unit/ -q      → 475 passed  (eram 472)
$ ... ruff check . && ruff format --check . && mypy app/ evals/   → limpos
```


## Tentativa 2 — o que mudou

Veredito da tentativa 1: **RESSALVAS**, score 9.5. Dois achados IMPORTANTES, ambos
fechados.

### C5-IMP-1 — `--repeticoes N` com `--cassettes` reportava ruído zero por construção

**Aceito integralmente, e o defeito era meu.** O `--repeticoes` foi acrescentado na
rodada de correção justamente para separar erro do pipeline de ruído de amostragem —
e em replay ele media o disco. As N repetições enviam o mesmo payload, `reproduzir()`
devolve N vezes a mesma string, `stdev` dá 0, e `_resumo_do_ruido` publicava
`cv_mediano: 0.0`. Um leitor concluiria "o modelo é determinístico" a partir de um
número que só diz "o disco é determinístico" — e replay é o modo barato, que a
documentação do runner incentiva.

Adotada a primeira correção sugerida, que é a mais barata: `repeticoes_efetivas()`
reduz a 1 quando há cassette sem gravação ligada, e o runner **avisa que reduziu**.
Com `EVAL_RECORD_CASSETTES=1` o provedor é chamado a cada repetição e o CV volta a
ser legítimo — o caso da execução agendada do `eval.yml`.

```text
$ python -m evals.runner --cassettes --repeticoes 3
aviso: --repeticoes 3 reduzido a 1 — em replay as repetições devolvem a mesma
gravação e o coeficiente de variação sairia zero por construção. Regrave com
EVAL_RECORD_CASSETTES=1 para medir ruído do modelo.
[1/10] simples-arroz-cozido-100g
...
amostragem  : {'temperature': 0.1, 'max_tokens': 8192, 'seed': -1, 'repeticoes': 1}
```

Quatro testes travam o comportamento nos quatro quadrantes (replay reduz; gravando
preserva; sem cassette preserva; `repeticoes=1` nunca é alterado).

### C5-IMP-2 — o relatório não declarava o que o replay mede e o que não mede

**Aceito.** A tabela "composto MdAPE 23,81% → 6,86%" é o resultado mais citado desta
spec, e o desenho por trás dela é bom — pareado, mesmos cassettes, só o código mudou.
O que faltava era a **condição de validade**: isso vale porque as correções são de
pós-processamento. Uma correção futura que mude o payload não é medível por esse
caminho, e chamar as duas coisas de "antes e depois" induz erro.

Acrescentada a seção **"O que a execução em replay mede — e o que ela não mede"** ao
`evals/README.md`, junto da análise de poder, declarando os dois lados e apontando o
grupo `inv-08` da bateria de invariância como o lugar onde ruído de modelo é medido
de verdade (a bateria chama o `AIClient` direto, sem cassette).

### Também entregue nesta tentativa

Custo e latência no relatório do runner (achado C8-IMP-2, que cai neste arquivo):
`custo: {chamadas, tokens_in, tokens_out, origem}` e
`latencia: {n, mediana_s, total_s}`. A **origem** importa tanto quanto o número —
em replay, `tokens_in: 0` significa "veio do disco", não "saiu de graça".

### Evidência

```text
$ python -m evals.runner --cassettes
custo       : {'chamadas': 0, 'tokens_in': 0, 'tokens_out': 0, 'origem': 'replay'}
latencia    : {'n': 10, 'mediana_s': 0.058, 'total_s': 1.041}
AGREGADO       10    3.89% [  0.00,   6.16]     0.00%    90%   ← inalterado

$ ... pytest --cov=app -q     → 620 passed, 1 skipped, 73.86%
$ ... ruff check . && ruff format --check . && mypy app/ evals/  → limpos
```

As sugestões da §5 da avaliação (acoplamento a métodos privados, `TOLERANCIA_MACRO_G`,
dataset em medida caseira, `ape()` devolvendo 100 para previsto ≤ 0) **não** foram
implementadas: são sugestões, e três delas a própria avaliação recomenda decidir
junto do dataset real, na C.4.


## 1. Resumo do que foi feito

`metrics.py` com funções puras (sem banco, sem rede, sem IA) e `runner.py`, que
executa o `MealParser` **de produção** por caso e agrega por estrato e no
agregado. O relatório sai em texto legível e em JSON estruturado.

## 2. Arquivos CRIADOS

| Arquivo | Propósito |
|---------|-----------|
| `backend/evals/metrics.py` | `ape`, `log_accuracy_ratio`, `mdape`, `mape`, `sspb`, `mae`, acurácia por tolerância absoluta e percentual, `ic95_bootstrap`, `percentil`. |
| `backend/evals/runner.py` | `executar_caso`, `resumir`, `montar_relatorio`, `formatar_texto`, `instrumentar_lookup`, CLI `python -m evals.runner`. |
| `backend/tests/unit/test_evals_metrics.py` | 31 testes, validados contra valores calculados à mão. |

## 3. Arquivos ALTERADOS

Nenhum arquivo pré-existente. Os limiares de
`tests/integration/test_golden_set.py` não foram tocados.

## 4. Confirmação do REUSO e decisões de design

**REUSADO:** o padrão de monkeypatch de
`scripts/instrument_meal_pipeline.py:118` para capturar o ranking do lookup —
`instrumentar_lookup` envolve `lookup_food` registrando o top-3 e o motivo da
rejeição, e devolve a função original para o chamador restaurar (o monkeypatch é
global e não pode vazar entre execuções). O runner usa o `MealParser` real, não
uma reimplementação: o que o eval mede é o que o usuário recebe.

**Decisões de design:**
- **MdAPE como headline, MAPE só para exibir o contraste.** A justificativa está
  na §4 da spec e é decisão travada; `mape()` existe para o relatório poder
  **mostrar** a diferença, não para ser função objetivo. Há teste demonstrando
  que o MAPE premia quem subconta.
- **Macros em MAE com tolerância absoluta.** `acuracia_por_tolerancia_absoluta`
  é a única forma usada para macros; o teste do café preto (0,1 g de gordura,
  200% de erro percentual, 0,2 g de erro real) documenta o porquê.
- **Bootstrap com semente fixa** (`SEMENTE_PADRAO = 20260802`). Um intervalo que
  muda a cada execução impede distinguir melhora real de ruído do próprio
  cálculo (NFR-5).
- **Estrato vazio vira `n=0`, não some**; caso que falha vira linha de falha e
  **não derruba a execução** — o `except` em `executar_caso` é o que impede que
  um `RateLimitError` no terceiro caso mate a rodada inteira, como aconteceu em
  2026-07-26.
- **Referência de macros viaja no `ResultadoCaso`.** A primeira versão relia o
  dataset dentro de `resumir()`; foi refatorada porque acoplava a agregação ao
  arquivo em disco e quebrava sobre resultados sintéticos.

**Desvio:** nenhum além do já declarado na C.3.

## 5. Comandos rodados + saídas reais

```text
$ ruff check . && ruff format --check .
All checks passed!

$ mypy app/ evals/
Success: no issues found in 78 source files

$ pytest tests/unit/test_evals_metrics.py -q
31 passed in 0.42s

$ pytest tests/unit -q
323 passed in 3.85s
```

**Execução manual do runner — EXECUTADA contra o pipeline real.** Docker ligado
pelo owner; Postgres 16 com `pg_trgm`/`unaccent`, banco nutricional semeado
(42.168 alimentos) e Groq real (conectividade confirmada). Saída real:

```text
$ docker compose -f docker-compose.dev.yml exec backend python -m evals.runner
[1/10] simples-arroz-cozido-100g
[...]
Sanity check falhou para 'feijoada completa': banco=110 kcal vs IA=350 kcal
  (divergencia=69%, source=taco) — usando estimativa IA
Sanity check falhou para 'lasanha de carne': banco=146 vs IA=300 (51%)
Sanity check falhou para 'strogonoff de carne': banco=155 vs IA=350 (56%)
========================================================================
EVAL DO PIPELINE DE IA — CalorIA
========================================================================
dataset sha : 426cb61f64af9b68  (n=10)
distribuicao: {'simples': 6, 'composto': 4, 'foto': 0}
nao verific.: 10 caso(s) com `verificada=false`
modelo      : llama-3.3-70b-versatile
amostragem  : {'temperature': 0.1, 'max_tokens': 8192, 'seed': -1}

estrato         n    MdAPE               IC95      SSPB   <=10%
------------------------------------------------------------------------
simples         6    1.26% [  0.00,   5.71]     1.25%   100%
composto        4   23.81% [  0.00,  41.03]    14.43%    25%
foto            0   (vazio)
------------------------------------------------------------------------
AGREGADO       10    3.89% [  0.00,  18.56]     1.25%    70%

macros (MAE em gramas, tolerancia absoluta — nunca %):
  proteina_g     MAE=  1.00 g   dentro de ±5 g: 100%
  carboidrato_g  MAE=  1.34 g   dentro de ±5 g: 86%
  gordura_g      MAE=  0.81 g   dentro de ±5 g: 100%
```

**Primeiro achado real do harness.** O estrato `composto` tem MdAPE de 23,81%
contra 1,26% do `simples`, e apenas 25% dos casos dentro de ±10%. A causa
aparece no log: em 3 dos 4 pratos compostos o **sanity check descarta o match do
banco**, porque a estimativa da IA para "100 g" do prato (350 kcal) diverge
mais de 35% do valor do banco (110 kcal) — a IA está estimando a porção
inteira, não os 100 g pedidos. O banco tem a linha certa e ela é jogada fora.

Isso é exatamente o tipo de defeito que o eval existe para tornar visível, e é a
primeira vez que o projeto consegue nomeá-lo com números. **Não foi corrigido
nesta fase** — está fora do escopo da C.5, que constrói o instrumento e não
redesenha o pipeline.

**Corrigido em 2026-08-02, por decisão do owner**, e medido com este mesmo
runner: o sanity check deixou de descartar match de fonte curada. Resultado:

| métrica | antes | depois |
|---|---|---|
| `composto` — MdAPE | 23,81% | **6,86%** |
| `composto` — dentro de ±10% | 25% | **75%** |
| agregado — dentro de ±10% | 70% | **90%** |
| agregado — SSPB | +1,25% | **0,00%** |
| MAE carboidrato | 1,34 g | **0,49 g** |

Ver `CORRECOES-2026-08-02-POS-VALIDACAO.md` §1 e
`.codeflow/decisions/2026-08-02-sanity-check-nao-descarta-fonte-curada.md`.

**Reprodutibilidade verificada (NFR-5).** Com os cassettes da C.7, o mesmo
relatório é reproduzido **byte a byte** com `GROQ_API_KEY` inválida — mesma
MdAPE, mesmo SSPB, mesmos MAE de macros.

## 6. Checklist dos ACs / critério de conclusão

- [x] **AC-13, métricas** — MdAPE e SSPB por estrato e no agregado, com `n` e
      IC95 por estrato, e macros em MAE com tolerância absoluta.
      *Evidência:* `TestAgregacaoDoRunner::test_relatorio_traz_os_tres_estratos_e_a_procedencia`
      e `TestAgregacaoDoRunner::test_resumo_traz_n_e_ic95`.
- [x] **Métricas validadas contra cálculo à mão** — `TestApe`, `TestMdape`,
      `TestSspb`, `TestMaeEToleranciaAbsoluta`, todos com o valor esperado
      escrito no comentário do teste.
- [x] **Assimetria do APE demonstrada por teste** —
      `TestAssimetriaDoErroPercentual`: o mesmo erro em razão (2× e ½×) dá o
      mesmo módulo de log accuracy ratio e APEs de 100% e 50%; e o MAPE premia
      quem subconta.
- [x] **`make test-unit` verde** — 323 testes na fase.
- [x] **Execução manual do runner com os três estratos** — executada contra o
      pipeline real, com Groq real e banco semeado (§5). Os três estratos
      aparecem no relatório, com `n`, IC95 e SSPB; `foto` como `n=0`.

## 7. Dúvidas para o avaliador

1. ~~Achado do estrato composto~~ — **CORRIGIDO** em 2026-08-02 (§5).
2. `TOLERANCIA_MACRO_G = 5.0` era valor de partida. Depois da correção: MAE de
   0,49 a 0,99 g, com **100% dentro de ±5 g nos três macros**. A tolerância
   ficou claramente folgada — apertar para ±3 g na C.4, junto do dataset real?
3. Os casos-semente descrevem "100 g de X", o que é pouco natural. Vale a C.4
   usar porções caseiras ("1 concha de feijão"), que é como o usuário escreve?
4. `--repeticoes` foi acrescentado ao runner (mediana + coeficiente de variação)
   por causa do achado `inv-08`. A execução agendada deve usar 3? Triplica o
   consumo de quota.
