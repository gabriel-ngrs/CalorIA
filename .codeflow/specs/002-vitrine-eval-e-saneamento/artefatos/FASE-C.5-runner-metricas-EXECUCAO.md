---
spec: 002-vitrine-eval-e-saneamento
fase: C.5
slug_fase: runner-metricas
status: executado
tentativa: 1
reprovacoes: 0
sha_inicial: 0d4d9ec
sha_final: e338ed4
range: 0d4d9ec..e338ed4
---

# FASE C.5 — Relatório de execução

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

**Execução manual do runner — PARCIAL, por limitação de ambiente.** O runner foi
exercitado ponta a ponta contra Postgres real, com o provedor substituído por um
dublê determinístico. Saída real:

```text
========================================================================
EVAL DO PIPELINE DE IA — CalorIA
========================================================================
dataset sha : 426cb61f64af9b68  (n=10)
distribuicao: {'simples': 6, 'composto': 4, 'foto': 0}
nao verific.: 10 caso(s) com `verificada=false` — a metrica ainda nao
              sustenta afirmacao publica
modelo      : llama-3.3-70b-versatile
amostragem  : {'temperature': 0.1, 'max_tokens': 8192, 'seed': -1}
prompts     : {'meal_identify': {'versao': 1, 'sha': 'f1334ef6...'},
               'meal_fallback': {'versao': 1, 'sha': '713ea1c5...'}}

estrato         n    MdAPE               IC95      SSPB   <=10%
------------------------------------------------------------------------
simples         0   (vazio)
composto        0   (vazio)
foto            0   (vazio)
------------------------------------------------------------------------
AGREGADO        0   (vazio)

falhas: 10
  simples-arroz-cozido-100g: ProgrammingError: function
  caloria_unaccent(text) does not exist
```

**O que essa saída prova e o que não prova.** Prova que o runner carrega o
dataset, monta o relatório com procedência (sha do dataset, modelo, parâmetros,
versão e sha de cada prompt), reporta os três estratos incluindo os vazios, e
**absorve a falha de cada caso sem morrer** — os 10 casos falharam e a execução
concluiu com relatório. **Não prova** a métrica sobre dados reais.

**Motivo da limitação, medido:** não há Docker nesta máquina; o Postgres de
espaço de usuário (`pgserver`) que viabilizou os testes de integração **não traz
os contribs** `pg_trgm` e `unaccent`, dos quais o `food_lookup` depende
(`CREATE EXTENSION IF NOT EXISTS pg_trgm` → `extension "pg_trgm" is not
available`). E `api.groq.com` não é alcançável desta sessão
(`groq.APIConnectionError`). O gate "execução manual com os três estratos
preenchidos" fica, portanto, **[—] por ambiente**, e é satisfeito pela execução
agendada da C.7 no CI, que tem Postgres 16 completo e a chave real.

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
- [—] **Execução manual do runner com os três estratos** — bloqueada por
      ambiente (§5). Demonstrada a estrutura; a medição real fica para a
      execução agendada da C.7.

## 7. Dúvidas para o avaliador

1. A execução manual do runner ficou `[—]` por ausência de `pg_trgm`/`unaccent`
   e de rede para a Groq. Isso reprova a fase, ou é aceitável dado que a C.7
   entrega a execução real no CI?
2. `TOLERANCIA_MACRO_G = 5.0` é valor de partida, não medido. Calibrar na
   primeira execução completa?
