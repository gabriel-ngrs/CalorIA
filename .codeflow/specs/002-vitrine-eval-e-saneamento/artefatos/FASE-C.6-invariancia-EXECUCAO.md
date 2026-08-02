---
spec: 002-vitrine-eval-e-saneamento
fase: C.6
slug_fase: invariancia
status: executado
tentativa: 1
reprovacoes: 0
sha_inicial: e338ed4
sha_final: 36d68cc
range: e338ed4..36d68cc
---

# FASE C.6 — Relatório de execução

## 1. Resumo do que foi feito

Bateria de invariância metamórfica com as relações modeladas **como dados**, em
`dataset/grupos_invariancia.jsonl`. Os 7 pares de
`scripts/instrument_meal_pipeline.py:41-88` migraram, com a reprodução oficial
do bug 001 como grupo de primeira classe, mais 5 grupos novos cobrindo as
relações que faltavam.

## 2. Arquivos CRIADOS

| Arquivo | Propósito |
|---------|-----------|
| `backend/evals/invariance.py` | `GrupoInvariancia`, `Relacao`, `spread`, `coeficiente_variacao`, `avaliar_grupo`, `resumir`, CLI. |
| `backend/evals/dataset/grupos_invariancia.jsonl` | 12 grupos, 6 relações. |
| `backend/tests/unit/test_evals_invariance.py` | 29 testes. |

## 3. Arquivos ALTERADOS

`backend/evals/metrics.py` — `_percentil` virou `percentil` (público), porque a
bateria precisa dele para o p95 do spread e importar um `_privado` de outro
módulo é acoplamento mal declarado.

## 4. Confirmação do REUSO e decisões de design

**REUSADO:** os 7 pares e o teste de determinismo de
`instrument_meal_pipeline.py`, migrados sem perder nenhum — há teste que lista
os sete `id` esperados e falha se algum sumir. `ColetorDeEstagios` e
`instrumentar_lookup` vêm do runner da C.5, não foram duplicados.

**Decisões de design:**
- **Relações como dados.** As seis relações (`parafrase`, `escala`, `ordem`,
  `unidade`, `ruido`, `autoconsistencia`) são valores de um enum, e cada grupo
  declara a sua tolerância. Acrescentar um grupo é acrescentar uma linha JSONL —
  não mexer em código.
- **`escala` normaliza pelo fator antes de medir.** Dobrar a porção **deve**
  dobrar as kcal; o que se mede é o resíduo depois de dividir pelo fator
  esperado. Sem isso, um pipeline correto reprovaria com spread 2,0.
- **`autoconsistencia` é distinta de invariância.** A entrada é literalmente a
  mesma string, repetida; o que se reporta é o coeficiente de variação, que mede
  não-determinismo puro do modelo. A medição do bug 001 (3 execuções dando
  572,3 kcal idênticos) é a linha de base — daí a tolerância apertada, 1.02.
- **p95 do spread, além da mediana.** A mediana esconde o caso patológico; o p95
  é o que o revela.
- **Coerência de relação imposta pelo schema:** `escala` sem `fator_esperado` é
  rejeitada; `autoconsistencia` com duas descrições ou uma única repetição é
  rejeitada; qualquer outra relação com uma só descrição é rejeitada.

**Escopo travado respeitado:** nenhuma tolerância foi afrouxada, nenhum grupo foi
removido, e a bateria **não** foi transformada em gate bloqueante de CI nesta
fase — o `eval.yml` da C.7 a executa e publica, sem travar PR sobre um
comportamento ainda não caracterizado.

## 5. Comandos rodados + saídas reais

```text
$ ruff check . && ruff format --check .
All checks passed!

$ mypy app/ evals/
Success: no issues found in 79 source files

$ pytest tests/unit/test_evals_invariance.py -q
29 passed in 0.13s

$ pytest tests/unit -q
352 passed in 3.94s
```

**Execução manual da bateria — [—] por ambiente**, pelo mesmo motivo da C.5: sem
`pg_trgm`/`unaccent` no Postgres de espaço de usuário e sem alcance a
`api.groq.com`, nenhum grupo pode ser medido contra o pipeline real. O cálculo
de spread e de coeficiente de variação está validado em casos sintéticos,
incluindo os números reais do bug 001 (3486 vs 2098 → spread 1,6615) e do teste
de determinismo (572,3 × 3 → CV 0,0).

**Achados de reprovação: nenhum registrado**, porque nenhuma medição real foi
possível. A primeira execução agendada (C.7) produz os primeiros achados.

## 6. Checklist dos ACs / critério de conclusão

- [x] **AC-14, cálculo de spread validado em casos sintéticos** —
      `TestSpread` (5 testes) e `TestAvaliacaoDeGrupo` (7 testes), com o valor
      do bug 001 como caso nomeado.
- [x] **AC-14, grupo do bug 001 presente** —
      `test_a_reproducao_do_bug_001_e_cidada_de_primeira_classe` verifica as
      duas descrições exatas dentro do grupo `inv-01-pizza-calabresa`.
- [x] **AC-14, relatório com taxa de aprovação e p95** — `TestResumo`, incluindo
      o caso em que o reprovado aparece com os números que o reprovaram.
- [x] **Os 7 pares originais migraram** —
      `test_os_sete_pares_originais_migraram` lista os sete `id` esperados.
- [x] **O teste de autoconsistência migrou** — `repeticoes: 3`, como no original.
- [—] **Execução manual produzindo relatório de invariância** — bloqueada por
      ambiente (§5).

## 7. Dúvidas para o avaliador

1. As tolerâncias dos 5 grupos novos (`ordem` 1.05, `unidade g↔kg` 1.05, `ruido`
   1.05, `escala` 1.05) foram escolhidas por raciocínio, não por medição.
   Confirmar ou ajustar depois da primeira execução real?
2. A bateria não é gate de CI nesta fase, por determinação do escopo travado.
   Em que fase ela deve virar gate?
