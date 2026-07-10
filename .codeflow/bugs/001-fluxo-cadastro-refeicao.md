---
versão: 1.0
id: "001"
slug: 001-fluxo-cadastro-refeicao
título: Cadastro de refeição não-determinístico e impreciso; banco nutricional subutilizado
severidade: alto
área: backend/ai
status: aberto
criado: 2026-07-09
atualizado: 2026-07-09
reportado_por: owner (QA manual)
lote: —
melhoria_relacionada: 004-contexto-de-refeicao
---

# BUG 001 — Cadastro de refeição não-determinístico e impreciso

## Relato original (owner)

> O cadastro de refeições hoje é subjetivo, e talvez o banco não esteja sendo
> usado da melhor forma. Coloquei `1 pizza grande 8 fatias de calabresa` e depois
> `8 fatias pizza calabresa` e deu resultados diferentes — mas ainda assim os 2
> estavam errados. É necessária uma investigação do fluxo de cadastro de
> alimentos. E independente da pergunta, sempre está puxando a IA em vez do
> banco.

O terceiro ponto do relato (*"implantar um sistema de levar em conta o contexto
da refeição — restaurante, casa, quantidade de óleo"*) é pedido de feature e foi
migrado para [`melhorias/004-contexto-de-refeicao.md`](../melhorias/004-contexto-de-refeicao.md).

## Reprodução

1. Autenticado, ir ao registro de refeição por texto.
2. Registrar `1 pizza grande 8 fatias de calabresa` → anotar kcal/macros.
3. Registrar `8 fatias pizza calabresa` → anotar kcal/macros.
4. **Esperado:** as duas descrições denotam a mesma refeição → mesmo resultado (ou
   diferença dentro de uma tolerância declarada).
5. **Obtido:** resultados divergentes entre si, e ambos incorretos frente ao valor
   real de uma pizza grande de calabresa.

Repro ainda **não automatizada**. Ver "Próximos passos".

## Investigação do fluxo (2026-07-09)

Pipeline verificado em código. Duas chamadas de backend independentes:
`POST /api/v1/ai/analyze-meal` (`backend/app/api/v1/ai.py:46-72`) faz a análise e
**não persiste**; o front reenvia o resultado para `POST /api/v1/meals`
(`backend/app/services/meal_service.py:47-69`), que grava.

A análise (`backend/app/services/ai/meal_parser.py:249-273`) tem dois estágios:

| Estágio | O que faz | Onde |
|---|---|---|
| 1 — Identificação | IA devolve `food_name`, `quantity` **já em gramas**, `unit`, `preparation`, `confidence`, `kcal_estimate` | `meal_parser.py:110-126`, prompt em `:44-71` |
| 2 — Preenchimento | Lookup pg_trgm no banco item a item; itens sem match caem em fallback IA agrupado | `meal_parser.py:128-209`; fallback em `:211-247` |

### Achado A — a quantidade em gramas é sempre inventada pela IA, sem normalização

**Verificado.** Não existe no código nenhum parser de unidade→grama nem tabela de
porções consultável. A única referência de porção caseira é a constante textual
`_PORTIONS_REF` (`meal_parser.py:20-42`), embutida no prompt do Estágio 1 — e ela
**não contém pizza nem fatia de pizza**. Ou seja: converter `8 fatias` e
`1 pizza grande 8 fatias` para gramas depende inteiramente do conhecimento livre
do modelo, sem âncora determinística.

`MealItem.unit` é string livre (`backend/app/models/meal_item.py:23`, `String(50)`,
default `"g"`), validada só por tamanho (`backend/app/schemas/meal.py:12`).

Esta é a **causa-raiz mais provável da divergência** entre as duas descrições: a
`quantity` é insumo do Estágio 2, nunca sua saída. O banco só multiplica
`calories_100g × quantity/100` (`meal_parser.py:165-192`) — se a `quantity` vier
errada, o banco **amplifica** o erro em vez de corrigi-lo.

### Achado B — "sempre puxa a IA" é, em parte, o desenho atual

**Verificado.** O Estágio 1 chama a IA **sempre**, por construção — o banco não
participa da identificação. O banco só entra no Estágio 2, e é usado apenas
quando **duas** condições passam (`meal_parser.py:143-201`):

1. `lookup_food` retorna match com `score ≥ 0.65` (`_LOOKUP_MIN_SCORE`,
   `food_lookup.py:26`), onde `score = similarity × boost` e `boost` é `1.40` para
   fonte TACO (`_SOURCE_BOOST`, `food_lookup.py:31`; aplicação em `:107`).
2. O sanity check calórico passa: `divergence = |db_kcal − kcal_estimate| / kcal_estimate ≤ 0.35`
   (`meal_parser.py:149-163`).

Falhando qualquer uma, o item vai para o fallback IA agrupado, que marca
`data_source="ai_estimated"` (`meal_parser.py:242`).

**Hipótese (não verificada em runtime):** "pizza de calabresa" é **prato
composto** e provavelmente não existe como linha na tabela `foods` (TACO tem
ingredientes, não pratos montados). O lookup falha o threshold de 0.65 e o item
cai no fallback IA — não por bug, mas porque o banco não tem o que responder.
Confirmar inspecionando `data_source` dos `MealItem` gerados nos dois testes.

### Achado C — o sanity check pode descartar o banco justamente quando ele estava certo

**Verificado no código, impacto não medido.** O sanity check compara `db_kcal`
(calculado com a `quantity` da IA) contra `kcal_estimate` (também da IA). Se a IA
errar a quantidade, **os dois lados erram junto** e a divergência não acusa nada.
Inversamente, quando a IA acerta a quantidade mas chuta mal o `kcal_estimate`, um
match **bom** do banco é descartado por divergência > 35% (`meal_parser.py:162`).
O check protege contra lixo do Open Food Facts, mas não detecta erro de porção —
que é exatamente a falha deste bug.

### Achado D — a correção calórica não cobre o caminho do banco

**Verificado.** `correct_calories` (`backend/app/services/ai/utils.py:18-38`,
tolerância 10%) só é aplicada no fallback IA (`meal_parser.py:247`). Itens
resolvidos pelo banco não passam por nenhuma verificação de coerência
kcal ↔ macros (Atwater). Assimetria intencional? Não há registro de decisão.

### Achado E — nenhuma noção de contexto da refeição

**Verificado.** `ContextBuilder.build_meal_context`
(`backend/app/services/ai/context_builder.py:196-313`) injeta perfil/metas,
consumo do dia, porções habituais de 30 dias, últimas 3 refeições do mesmo tipo e
média por tipo. **Não** injeta ambiente (casa/restaurante) nem óleo adicionado.
Existe `Food.preparation` (`backend/app/models/food.py:23`) e
`IdentifiedFood.preparation` (`food_lookup.py:62`), concatenado na query de lookup
(`meal_parser.py:138-142`) — cobre "grelhado ≠ frito", não cobre o resto.
Tratado em [`melhorias/004`](../melhorias/004-contexto-de-refeicao.md).

## Impacto

Registro calórico incorreto é falha na **função central do produto**. Pior: o erro
é silencioso (o usuário não tem como saber que a porção foi mal convertida) e
contamina os agregados a jusante — TDEE, insights, `PatternAnalyzer` e as
"porções habituais" do `ContextBuilder`, que realimentam o prompt. Erro de porção
vira erro de contexto, que vira erro de porção.

## Próximos passos sugeridos

1. **Instrumentar antes de corrigir.** Rodar as duas descrições contra
   `analyze-meal` e capturar, por item: `food_name`, `quantity`, `data_source`,
   `confidence`, `kcal_estimate`, e o `score` do lookup. Isso decide entre os
   achados A, B e C. Sem esse dado, qualquer fix é chute.
2. Escrever um teste de regressão em `backend/tests/unit/test_meal_parser.py` com
   as duas descrições e um invariante de equivalência (mesma refeição → kcal
   dentro de ±X%).
3. Avaliar uma **tabela de porções consultável** (unidade caseira → gramas), em
   banco e não no prompt, com cobertura para pratos compostos (pizza, lasanha,
   sanduíche). Substitui `_PORTIONS_REF`.
4. Avaliar suporte a **pratos compostos** em `foods` (receita = soma de
   ingredientes) ou uma tabela `recipes` separada.
5. Revisitar o sanity check para detectar erro de porção (ex.: comparar
   `quantity` contra faixa plausível da porção caseira), não só divergência
   kcal ↔ kcal.
6. Decidir se `correct_calories` deve valer também para o caminho do banco
   (achado D) e registrar a decisão.

## Rastreabilidade

- Melhoria derivada: [`melhorias/004-contexto-de-refeicao.md`](../melhorias/004-contexto-de-refeicao.md)
- Lote de correção: — (ainda não aberto)
- Decision: — (ainda não gerada)
