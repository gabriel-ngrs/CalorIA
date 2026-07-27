---
data: 2026-07-26
título: Limiares e estratégia de busca no banco nutricional
status: ativa
tags: [ai, food-lookup, pg_trgm, thresholds, bug-001]
---

# Limiares e estratégia de busca no banco nutricional

## Contexto

O bug 001 apontou que "sempre está puxando a IA em vez do banco". A investigação
por instrumentação (ver `bugs/001-fluxo-cadastro-refeicao.md`, seção
"Instrumentação (data)") mostrou que o `food_lookup` erra por vários mecanismos
independentes. Esta decision registra **quais parâmetros mudam e por qual número**,
para não repetir o padrão de ajuste por intuição que produziu a migration
`20260320_e6f7a8b9c0d1_fix_search_text_taco.py` (ajuste manual de `search_text`
de 7 alimentos para "ganhar" score).

## Método

Conjunto rotulado de 40 consultas em `backend/scripts/eval_food_lookup.py`:
36 que **devem** casar (com faixa de kcal/100g aceitável, derivada da fonte curada
`taco` e de valores de referência) e 4 que **não devem** casar (`tacacá`, `sal`,
`orégano`, `água`). As consultas reproduzem o que o Estágio 1 realmente emite,
observado no baseline instrumentado.

Métrica: precisão (dos itens resolvidos, quantos caíram na faixa correta), recall
(dos que deveriam casar, quantos casaram certo) e F1. Sete estratégias × nove
limiares.

## Medição

F1 no limiar de produção (0,65) e no melhor limiar de cada estratégia:

| estratégia | F1 @0,65 | melhor F1 | precisão @0,65 | recall @0,65 |
|---|---:|---:|---:|---:|
| **A** atual (n-grama + `similarity` + boost taco 1,40×) | 0,776 | 0,806 @0,30 | 83,9% | 72,2% |
| **B** = A + `unaccent()` nos dois lados | **0,857** | **0,861** @0,30 | **88,2%** | **83,3%** |
| C `unaccent` + query inteira + score composto + prioridade | 0,656 | 0,806 @0,30 | 80,0% | 55,6% |
| D = C sem linhas `ai_estimated` | 0,491 | 0,725 @0,45 | 76,5% | 36,1% |
| E = C + filtro de plausibilidade Atwater | 0,656 | 0,806 @0,30 | 80,0% | 55,6% |
| F = B + prioridade dura de fonte (em vez do boost) | 0,746 | 0,761 @0,45 | 80,6% | 69,4% |
| G = F + filtro de plausibilidade | 0,746 | 0,761 @0,45 | 80,6% | 69,4% |
| H = B sem linhas `ai_estimated` | 0,769 | 0,776 @0,55 | 86,2% | 69,4% |
| I = B + `ai_estimated` penalizado 0,75× | 0,857 | 0,857 @0,65 | 88,2% | 83,3% |

## Decisão

**1. Normalizar acento nos dois lados da comparação. Limiar permanece 0,65.**

É a única mudança de scoring com ganho medido: F1 0,776 → **0,857** (+8,1 pp),
precisão 83,9% → 88,2%, recall 72,2% → 83,3%. Causa: `_normalize()`
(`food_lookup.py:34-37`) remove acentos da consulta, mas `search_text` no banco
**mantém** — `similarity('feijao carioca cozido','feijão carioca cozido')` = 0,75
em vez de 1,00. Atinge 43% das linhas `taco` (98 de 228), justamente os básicos
brasileiros: Feijão, Óleo, Macarrão, Pão, Açúcar, Limão, Maçã.

O limiar **não muda**. Em B, 0,65 é o ponto de melhor precisão (88,2%) mantendo o
recall no platô (83,3%); baixar para 0,30 ganharia 0,004 de F1 e introduziria
3 falsos-positivos (`sal` → `Sala` 400 kcal/100g; `orégano` → `Orégano` 280).
Num diário alimentar, falso-positivo é pior que ausência: um item errado entra
silenciosamente no total do dia, enquanto um item ausente cai no fallback marcado.

**2. Manter o boost multiplicativo de `taco` em 1,40×; NÃO adotar prioridade dura de fonte.**

Contraria a intuição, mas foi medido: prioridade dura (F/G) piora o F1 para 0,746.
O motivo é que ela promove linhas `taco` semanticamente erradas — `'ovo cozido'`
passa a casar com `'Chuchu cozido'` (19 kcal/100g) porque ambos compartilham a
palavra "cozido".

Sensibilidade do boost medida sobre a implementação final (limiar 0,65):

| boost | ok | errados | perdidos | falso+ | precisão | recall | F1 |
|------:|---:|--------:|---------:|-------:|---------:|-------:|---:|
| 1,00 | 23 | 7 | 6 | 1 | 76,7% | 63,9% | 0,697 |
| **1,40** | 29 | 5 | 2 | 1 | 85,3% | 80,6% | **0,829** |
| 1,60 | 30 | 5 | 1 | 1 | 85,7% | 83,3% | 0,845 |
| 1,80 | 31 | 4 | 1 | 1 | 88,6% | 86,1% | 0,873 |
| 2,50 | 32 | 4 | 0 | 1 | 88,9% | 88,9% | 0,889 |

**O F1 aponta 2,50 e mesmo assim 1,40 foi mantido.** Inspecionar os erros mostra
por quê: em 2,50 o boost passa a aceitar match `taco` de similaridade bruta 0,43,
e aparecem falhas catastróficas que não existem em 1,40 —
`'arroz branco cozido'` → **`'Brócolis cozido'`** (25 kcal/100g, bruto 0,43) e
`'ovo cozido'` → **`'Chuchu cozido'`** (19 kcal/100g, bruto 0,44). O casamento
acontece pela palavra "cozido", compartilhada. Em 1,40, a menor similaridade
bruta aceita de uma linha `taco` é 0,48 (`'frango grelhado'` →
`'Frango peito grelhado'`), que é um match legítimo.

Registro metodológico: **o F1 agregado é enganoso aqui**. Ele premia trocar
"perdido" por "errado", mas num diário alimentar um item errado de 19 kcal no
lugar de 146 kcal é pior que um item ausente, que ao menos cai no fallback
marcado. A escolha foi feita olhando a distribuição dos erros, não só o agregado.

**3. EXCLUIR as linhas `source='ai_estimated'` do lookup.**

> **Esta decisão foi revertida depois de medir melhor.** A primeira versão dizia
> "não excluir", baseada no conjunto rotulado de `eval_food_lookup.py`. O conjunto
> dourado — mais próximo do produto — mostrou o contrário. O registro da reversão
> fica aqui de propósito: o erro foi de método, não de execução.

**Por que a primeira medição enganou.** `eval_food_lookup.py` usa consultas
*limpas* (`"arroz branco cozido"`) e mede F1 de "o alimento casado cai na faixa
calórica esperada". Duas distorções:

1. Usuário não escreve "arroz branco cozido", escreve **"arroz"**. Com a consulta
   curta, `'arroz'` casa com a linha `Arroz` [ai_estimated] de **349 kcal/100g**
   — arroz **cru** — em vez de `Arroz parboilizado cozido` (127). Erro de **175%**
   no alimento mais registrado do país. O conjunto limpo nunca expôs isso.
2. F1 conta acerto/erro binário. Não distingue errar por 5% de errar por 175%.

**O que o conjunto dourado mediu** (`eval_golden_set.py`, 30 refeições brasileiras
em unidades caseiras, erro calórico contra a fonte curada):

| tratamento de `ai_estimated` | resolvidos | alimento ok | **erro médio** | ≤10% | erro máx |
|---|---:|---:|---:|---:|---:|
| nenhum | 26/29 | 14/29 | **16,7%** | 18/26 | 174,8% |
| penalidade 0,85× | 26/29 | 16/29 | 15,9% | 19/26 | 174,8% |
| penalidade 0,75× | 26/29 | 17/29 | 14,6% | 20/26 | 174,8% |
| **excluir** | 23/29 | **19/29** | **4,1%** | **21/23** | 72,5% |

Erro médio cai de 16,7% para **4,1%**; itens dentro de ±10% sobem de 69% para 91%;
o erro máximo cai pela metade. No conjunto antigo o F1 cai de 0,829 para 0,788,
mas a precisão sobe (85,3% → 86,7%) e os falsos-positivos vão a **zero**.

**Custo aceito:** 6 dos 29 itens deixam de ter match e caem no fallback da IA
(`'arroz'`, `'alface'`, `'tapioca'`, `'cuscuz de milho'`, `'açaí na tigela'`,
`'coxinha'`). Lá eles chegam ao usuário **marcados como estimados**. É a troca
certa: um item marcado como incerto é melhor que um item errado que se apresenta
como dado de banco.

**Por que exclusão e não penalidade.** Com limiar 0,65, qualquer penalidade
≤ 0,65 já é exclusão na prática (o score bruto máximo de `similarity` é 1,00).
Entre uma penalidade que exclui disfarçadamente e uma exclusão declarada, a
segunda é legível. Implementada em `food_lookup._FONTES_EXCLUIDAS`.

As 23.398 linhas continuam na tabela — removê-las é migração de dados destrutiva
e fora do escopo deste trabalho. Higienizá-las (ou reimportá-las de fonte real)
fica registrado como melhoria própria.

**4. NÃO adotar score composto (`strict_word_similarity × similarity`).**

Medido pior (C: F1 0,656 @0,65). A hipótese era que ele impediria casamento por
fragmento; a medição mostrou que ele custa recall demais.

**5. O filtro de plausibilidade Atwater NÃO serve para filtrar linhas do banco.**

E/G têm F1 idêntico a C/F: o filtro não descartou nenhuma linha ruim. Motivo:
`enrich_foods.py:129-133` **recalcula** as calorias a partir dos macros quando
divergem mais de 30%, então as linhas `ai_estimated` são internamente coerentes
por construção — coerência Atwater não distingue chute de dado real. O filtro
continua válido no caminho do fallback da IA, onde a incoerência é real.

## Consequência

A precisão de 88,2% no melhor cenário de scoring significa que **ajustar o lookup
não resolve o bug 001 sozinho**. Os ganhos maiores estão fora do scoring, nos
mecanismos identificados na instrumentação:

- consultar o **prato composto** antes de decompor (a fonte `taco` tem
  `Pizza calabresa`, `Feijoada completa`, `Lasanha`, `Strogonoff` — nunca são
  consultados porque o prompt força decomposição em ingredientes);
- **normalizar a porção** por tabela consultável (fonte dominante do erro);
- **limpar a query** antes do lookup (hoje `preparation` cru entra concatenado:
  `"azeite não aplicável"` → 0,6364, abaixo do limiar; `"azeite"` → 1,00);
- **não casar por fragmento** (`lookup_food` de um alimento delega a
  `find_foods_in_text`, que fatia em n-gramas: `"manteiga derivado do leite"`
  casou com `Leite` via o fragmento `"do leite"`).

## Alternativas descartadas

- **Baixar o limiar para 0,30** (melhor F1 absoluto de B, 0,861): ganho de 0,004
  em F1 ao custo de 3 falsos-positivos. Rejeitado pelo critério de que
  falso-positivo é mais danoso que ausência num diário alimentar.
- **Reescrever `search_text` sem acento por migration**, em vez de aplicar
  `unaccent()` na consulta: equivalente em resultado, mas exigiria reprocessar
  42.103 linhas e manter a normalização em todos os scripts de importação
  (`import_off_local.py`, `import_usda.py`, `import_tbca.py`, `normalize_foods.py`,
  `enrich_foods.py`, `translate_foods.py`). `unaccent()` na consulta concentra a
  regra num lugar só. Custo: exige índice de expressão para não perder o GIN.

## Reprodução

    docker compose -f docker-compose.dev.yml exec -T backend python scripts/eval_food_lookup.py
