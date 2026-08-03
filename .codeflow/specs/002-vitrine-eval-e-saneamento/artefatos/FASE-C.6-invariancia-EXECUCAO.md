---
spec: 002-vitrine-eval-e-saneamento
fase: C.6
slug_fase: invariancia
status: rework
tentativa: 3
reprovacoes: 2
sha_inicial: e338ed4
sha_final: 769cf69b0964bc47f5a2e201729b244478ee1e7f
range: e338ed4..769cf69b0964bc47f5a2e201729b244478ee1e7f
---

# FASE C.6 — Relatório de execução

## Tentativa 3 — a remedição foi TENTADA, e o limite é medido

Veredito da tentativa 2: **RESSALVAS**, score 9.4, por C6-IMP-1 mantido. O achado
estava certo em cheio, e a crítica de método também: eu transportei "a quota está
esgotada" de 2026-08-02 para o rework de 2026-08-03 **sem retestar**, transformando
"não deu" em "não tentei". O free tier reseta por dia; a afirmação tinha validade de
um dia e foi usada como se fosse permanente.

### O que fiz nesta tentativa

Retestei antes de afirmar qualquer coisa. O provedor **respondeu**:

```text
$ ... pytest tests/smoke_test.py::test_groq_texto -q
1 passed, 1 warning in 2.64s
```

Com a porta aberta, rodei o eval completo contra o provedor (12 chamadas, 8.911 tokens
de entrada e 796 de saída — a primeira medição de custo real desta spec) e em seguida a
bateria de invariância, na ordem recomendada.

### O resultado: impossibilidade **medida**, não presumida

```text
$ docker compose -f docker-compose.dev.yml exec -T backend python -m evals.invariance
...
groq.RateLimitError: Error code: 429 - {'error': {'message': 'Rate limit reached for
model `llama-3.3-70b-versatile` in organization `org_...` service tier `on_demand` on
tokens per day (TPD): Limit 100000, Used 99151, Requested 1026. Please try again in
2m32.928s. ...', 'type': 'tokens', 'code': 'rate_limit_exceeded'}}
```

O limite não é RPM (por minuto), é **TPD — tokens por dia**: teto de 100.000, com
99.151 já consumidos. O backoff de `_espera_do_backoff` fez o seu trabalho (15s → 30s →
60s, dentro do teto de 120s declarado na C.2) e desistiu corretamente: esperar não
resolve um limite diário. Sobravam ~850 tokens; a bateria precisa de dezenas de
milhares.

**Isto é o dado que faltava, e vale mais que a remedição em si.** A spec registra o
risco R5 ("quota do free tier") como risco; agora ele é uma medida:

| item | tokens | fonte |
|---|---|---|
| eval completo, 10 casos, 12 chamadas | **9.707** | medido hoje (`custo` do relatório) |
| teto diário do free tier | **100.000** | mensagem do 429 |
| bateria de invariância (12 grupos, ~30 chamadas) | **não coube nos ~850 restantes** | medido hoje |

O eval completo cabe ~10× por dia. A bateria não coube **depois** de o dia já estar
99% consumido — pelas verificações da própria avaliação somadas à minha execução. Não é
que a bateria não caiba num dia; é que ela não cabe no mesmo dia em que se gasta a
quota verificando outras coisas.

### O que continua em aberto, e como fechar

A remedição do `inv-04` e dos quatro grupos atingidos pelo sanity check **não foi
feita**. Ela é o primeiro comando de um dia com quota limpa:

```bash
docker compose -f docker-compose.dev.yml exec -T backend python -m evals.invariance
```

Linha de base a comparar, da §5 deste relatório: **aprovação 0,417 · spread mediano
1,2115 · p95 3,5126**, com `inv-04` em 4,14. A nova medição entra como seção datada
aqui, sem apagar a antiga.

**Recomendação de ordem, aprendida hoje:** rodar a bateria **antes** do eval completo e
antes de qualquer verificação avulsa contra o provedor. O eval completo custa ~9.700
tokens e o histórico da C.8 já tem a execução real de que precisava — a bateria é agora
a única coisa que justifica gastar quota.


## Tentativa 2 — o que mudou

Veredito da tentativa 1: **RESSALVAS**, score 9.7. Dois achados IMPORTANTES: um
fechado, um **bloqueado por quota** e declarado como tal.

### C6-IMP-2 — correção das regras de porção sem decision registrada — **FECHADO**

**Aceito.** O achado `inv-04` é desta fase, mas a correção mexeu em
`backend/scripts/seed_portions.py`, que não consta dos "Arquivos alterados" de fase
nenhuma. O DoD global exige que toda decisão de escopo tomada durante a execução seja
registrada, e não estava.

Registrado em `.codeflow/decisions/2026-08-03-regras-de-porcao-para-gordura-de-passar.md`,
indexado em `.codeflow/decisions/INDEX.md` com as tags pedidas (`nutricao`, `portions`,
`eval`, `spec-002`, `fase-c6`), e referenciado na **OQ14** da spec. A decision registra
o defeito medido (spread 4,14 no `inv-04`, 880 kcal contra 212,6 kcal para a mesma
refeição), a mudança e o efeito esperado.

Uma correção de fato ao que a avaliação registrou: são **13 entradas** acrescentadas,
não sete — conferidas na tabela. Nenhuma entrada foi removida e nenhuma alterada; a
mudança é aditiva. Não há duplicata no estado final, e
`test_nenhum_par_termo_unidade_duplicado` garante isso (a coluna tem
`unique (term, unit)`, e uma duplicata derruba o seed inteiro).

### C6-IMP-1 — a medição é anterior às correções que a fase motivou — **EM ABERTO**

**Aceito, e não resolvido: falta quota.** O achado é procedente — a §5 deste relatório
descreve `7 de 12 reprovam` sobre um pipeline em que quatro dessas causas já foram
atacadas (o sanity check de fonte curada, e agora as regras de porção). Rodar a
bateria hoje produziria `RateLimitError`, não medição.

O que fica pronto para quando a quota voltar:

```bash
docker compose -f docker-compose.dev.yml exec -T backend python -m evals.invariance
```

Linha de base a comparar, da §5 deste relatório: **aprovação 0,417 · spread mediano
1,2115 · p95 3,5126**, com `inv-04` em 4,14 e `inv-03`, `inv-06`, `inv-10`, `inv-12`
atribuídos ao sanity check. A nova medição entra como **seção datada** neste relatório,
sem apagar a antiga — a antiga é a metade "antes" da narrativa.

**Consequência honesta:** enquanto isso não sair, esta fase não fecha, e uma
reavaliação agora deve manter RESSALVAS por este item. Está declarado aqui para que
o avaliador não precise descobrir.

### Evidência desta tentativa

```text
$ ... pytest --cov=app -q     → 620 passed, 1 skipped, 73.86% (piso 72%)
$ ... pytest tests/unit/test_portions_gorduras.py -q   → 20 passed
$ ... ruff check . && ruff format --check . && mypy app/ evals/  → limpos
```


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
