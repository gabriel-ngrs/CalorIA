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

**Execução manual da bateria — EXECUTADA contra o pipeline real**, com Docker
ligado pelo owner, banco semeado e Groq real:

```text
$ docker compose -f docker-compose.dev.yml exec backend python -m evals.invariance
n_grupos: 12 | aprovacao: 0.417 | spread mediano: 1.2115 | p95: 3.5126

OK       inv-01-pizza-calabresa       spread=1.0     tol=1.10  kcal=[2160.0, 2160.0]
OK       inv-02-ovos-numeral-extenso  spread=1.0     tol=1.10  kcal=[171.0, 171.0]
REPROVOU inv-03-pf-vago-vs-gramas     spread=1.5221  tol=1.25  kcal=[859.2, 564.5]
REPROVOU inv-04-pao-manteiga          spread=4.1392  tol=1.25  kcal=[880.0, 212.6]
OK       inv-05-leite-copo-ml         spread=1.0     tol=1.15  kcal=[133.4, 133.4]
REPROVOU inv-06-marmita-strogonoff    spread=1.4812  tol=1.25  kcal=[945.0, 638.0]
REPROVOU inv-07-tacaca-ausente        spread=3.0     tol=1.30  kcal=[140.0, 420.0]
REPROVOU inv-08-determinismo          spread=1.2355  tol=1.02  kcal=[859.2, 859.2, 695.4]
OK       inv-09-ordem-arroz-feijao    spread=1.0238  tol=1.05  kcal=[533.2, 520.8]
REPROVOU inv-10-unidade-g-kg          spread=1.75    tol=1.05  kcal=[1120.0, 640.0]
OK       inv-11-ruido-cortes          spread=1.0     tol=1.05  kcal=[128.0, 128.0]
REPROVOU inv-12-escala-dobro          spread=1.1875  tol=1.05  kcal=[128.0, 304.0]
```

### Achados de reprovação — 7 de 12 grupos

A fase declara que **uma reprovação é um achado, não um defeito do teste**.
Nenhuma tolerância foi afrouxada e nenhum grupo foi removido. Em ordem de
gravidade:

1. **`inv-04` pão com manteiga — spread 4,14 (880 vs 212,6 kcal).** O caso
   patológico que o p95 existe para revelar. "1 pão francês com manteiga" dá
   880 kcal; "50g pão francês + 10g manteiga" dá 212,6. Mais de 4× de diferença
   para a mesma refeição.
   **CORRIGIDO em 2026-08-02:** a IA emite `unit="porção"` para a manteiga e não
   havia regra `(manteiga, porcao)` em `portions` — valia a genérica de 100 g,
   que são ~720 kcal de manteiga. Regras próprias adicionadas para as sete
   gorduras/pastas de passar.
2. **`inv-07` tacacá — spread 3,00 (140 vs 420).** Item ausente do banco: os
   dois lados caem no fallback da IA e divergem por 3×. Mede a instabilidade do
   caminho de fallback, que é o pior caminho do pipeline.
3. **`inv-10` unidade g↔kg — spread 1,75 (1120 vs 640).**
   **Diagnóstico revisto em 2026-08-02: minha leitura inicial estava errada.**
   `0,5 kg` **é** convertido corretamente para 500 g — medido direto no
   `PortionNormalizer`. O lado que errava era o **outro**: `500 g de arroz`
   recebia `kcal_estimate=1750` da IA, o sanity check de 35% descartava o match
   correto do banco (640 kcal) e adotava a estimativa (1120). O `0,5 kg` recebia
   `kcal_estimate=875`, divergência de 27%, passava, e usava o banco. Mesma
   refeição, dois caminhos, por causa do check. **Corrigido pelo item 1 das
   correções pós-validação**, não por mudança de unidade.
4. **`inv-03` prato feito vago vs gramas — 1,52** e **`inv-06` marmita — 1,48.**
   Ambos acima da tolerância de 1,25, que já era folgada por reconhecer a
   incerteza da porção caseira.
5. **`inv-12` escala — resíduo 1,19 (128 → 304 em vez de 256).** Dobrar a porção
   não dobra as calorias: sobram 48 kcal (18,75%).
6. **`inv-08` determinismo — CV ≠ 0 (859,2 / 859,2 / 695,4).** A mesma string
   repetida três vezes deu dois valores. **Contradiz a medição do bug 001**, que
   observara 572,3 kcal idênticos em três execuções — mas era outra frase e outro
   prompt. Achado relevante: o não-determinismo do modelo **existe** e é
   dependente da entrada, então qualquer comparação A/B precisa de repetição.

**O que passou, e por que importa:** `inv-01`, a **reprodução oficial do bug
001**, deu spread **1,000** (2160 = 2160 kcal). É a confirmação, medida agora e
não em maio, de que a correção do bug 001 **se mantém**. Junto com `inv-02`
(numeral vs extenso), `inv-05` (copo vs ml), `inv-09` (ordem) e `inv-11`
(ruído), mostra que as invariâncias de forma da frase estão sólidas; o que
quebra é **conversão de porção e o caminho de fallback**.

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
- [x] **Execução manual produzindo relatório de invariância** — executada (§5):
      12 grupos, taxa de aprovação 0,417, spread mediano 1,2115, p95 3,5126.
- [x] **Achados de reprovação registrados no relatório da fase** — os 7
      reprovados estão em §5, com números e ordem de gravidade.

## 7. Dúvidas para o avaliador

1. ~~7 de 12 grupos reprovam~~ — **duas causas-raiz corrigidas** em 2026-08-02:
   o sanity check descartando fonte curada (afetava `inv-03`, `inv-06`, `inv-10`
   e provavelmente `inv-12`) e a regra genérica de porção para gordura de passar
   (`inv-04`). Ver `CORRECOES-2026-08-02-POS-VALIDACAO.md` §1 e §2.
2. ~~`inv-08` mostra não-determinismo do modelo~~ — **RESOLVIDO**: o runner
   ganhou `--repeticoes N`, com mediana por caso e coeficiente de variação
   reportado à parte. Falta o owner decidir se a execução agendada usa 3
   (triplica o consumo de quota).
3. As tolerâncias dos 5 grupos novos foram escolhidas por raciocínio. Com a
   medição em mãos, `ordem` (1,0238 medido) e `ruido` (1,0 medido) parecem bem
   calibradas; `escala` e `unidade` reprovam por bug, não por tolerância
   apertada. Confirmar?
4. A bateria não é gate de CI nesta fase, por escopo travado. Com 41,7% de
   aprovação, travá-la agora deixaria o CI vermelho. Em que fase ela vira gate,
   e com que piso?
