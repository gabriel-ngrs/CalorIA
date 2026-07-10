---
versão: 1.0
id: "004"
slug: 004-contexto-de-refeicao
título: Contexto da refeição (casa/restaurante/preparo) no pipeline de análise
tipo: evolução
área: backend/ai
esforço: médio
prioridade: alta
status: a fatiar
criada: 2026-07-09
atualizada: 2026-07-09
proposta_por: owner
bug_origem: 001-fluxo-cadastro-refeicao
linked_spec: —
---

# MELHORIA 004 — Contexto da refeição no pipeline de análise

## Relato original (owner)

> É importante implantar um sistema de levar em conta o contexto da refeição — se
> é restaurante, se é em casa... porque isso interfere nos ingredientes,
> quantidade de óleo...

Extraído do relato de [`bugs/001`](../bugs/001-fluxo-cadastro-refeicao.md), onde
veio junto com o reporte de imprecisão. É pedido de feature, não defeito — daí a
migração.

## Problema / valor

O mesmo prato tem perfil nutricional muito diferente conforme onde e como foi
feito. Comida de restaurante costuma levar mais óleo, mais sal e porções maiores
que a mesma receita feita em casa. Hoje o pipeline não sabe disso.

**Estado verificado do código:**
- `ContextBuilder.build_meal_context` (`backend/app/services/ai/context_builder.py:196-313`)
  injeta perfil/metas, consumo do dia, porções habituais de 30 dias, últimas 3
  refeições do mesmo tipo e média por tipo. **Nada sobre ambiente ou preparo.**
- Existe `Food.preparation` (`backend/app/models/food.py:23`) e
  `IdentifiedFood.preparation` (`backend/app/services/ai/food_lookup.py:62`),
  concatenado na query de lookup (`meal_parser.py:138-142`). Os prompts reforçam
  "grelhado ≠ frito ≠ cozido ≠ assado" (`meal_parser.py:51,91`).
- **Não existe:** campo de ambiente (casa/restaurante), óleo adicionado, ou
  qualquer contexto estruturado. `Meal` tem `notes` e `source` (enum), que não
  capturam isso. `MealItem` e `Food` não têm campo de contexto.

Logo: o preparo já é meio-caminho andado; o ambiente é do zero.

## Escopo proposto (a validar)

### Fatia 1 — Capturar o contexto
- `Meal.context` — enum ou tabela (`casa`, `restaurante`, `fast-food`, `lanchonete`,
  `marmita`, `padaria`...). Um campo, um dropdown, valor default por tipo de
  refeição.
- **Custo de UX é o risco.** Um passo a mais no registro diário derruba a adesão.
  Sugestão: inferir do texto (a IA já recebe a descrição livre — "almocei no
  restaurante X") e só perguntar quando ambíguo. Nunca bloquear o registro.

### Fatia 2 — Usar o contexto na análise
- Injetar o contexto no `ContextBuilder` → prompt do Estágio 1 do `MealParser`.
- Multiplicadores por contexto: fator de óleo/porção aplicado à estimativa.
  **Ver questões em aberto** — a fonte desses fatores importa.

### Fatia 3 — Aprender o contexto do usuário
- O `ContextBuilder` já calcula porções habituais de 30 dias
  (`context_builder.py:257-285`). Estender para porções habituais **por
  contexto**: "no restaurante, este usuário come em média 1.4× a porção que come
  em casa".
- Isso é o pedido do owner na sua forma mais forte: não um fator genérico, mas o
  padrão observado do próprio usuário.

## Questões em aberto (decisão do owner / pesquisa necessária)

- **[procedência — crítico]** De onde vêm os multiplicadores de óleo/porção por
  contexto? Inventar `restaurante = 1.3×` é exatamente o tipo de número plausível
  e infundado que este projeto já sofre no cadastro de refeição. Opções: (a) fonte
  publicada (estudos de porção fora de casa), citada no código; (b) deixar a IA
  ajustar qualitativamente pelo prompt, sem fator numérico; (c) aprender do
  próprio histórico do usuário (fatia 3), sem prior. **Recomendação: (b) no MVP,
  (c) quando houver dado suficiente. Nunca (a) sem fonte real.**
  `[não verificado]` — nenhuma fonte consultada.
- **[decisão de produto]** Contexto por refeição ou por item? "Almocei em casa mas
  a sobremesa foi da padaria" existe, mas modelar por item dobra o custo de UX
  para um ganho marginal. Sugestão: por refeição.
- **[decisão de produto]** Perguntar ou inferir? Inferir erra silenciosamente;
  perguntar cansa. Provável: inferir + mostrar o contexto detectado como chip
  editável na tela de confirmação.
- **[técnica]** O contexto entra também no lookup do banco (`food_lookup.py`)?
  "Batata frita de restaurante" e "batata frita de casa" não são linhas distintas
  em `foods`. Provavelmente o contexto atua só na estimativa, não no match.

## Dependências

- **Depende de [`bugs/001`](../bugs/001-fluxo-cadastro-refeicao.md).** Adicionar
  contexto a um pipeline cuja conversão de porção é não-determinística
  (achado A do bug) melhora um número que já está errado por outra causa. Corrigir
  a base de porções primeiro; contexto depois. Ordem importa.
- Sinergia com [`melhorias/002`](002-modulo-dieta.md): a dieta prescrita é uma
  forma forte de contexto.

## Notas de esforço

Fatias 1–2 são pequenas em código (um campo, um trecho de prompt) e grandes em
decisão de produto. A fatia 3 é a que entrega o valor real e depende de volume de
histórico — só faz sentido depois de meses de uso.
