# Fluxo de Analise de IA (Pipeline 2 Estagios)

## Visao Geral

Tanto o `MealParser` (texto) quanto o `VisionParser` (foto) usam o mesmo pipeline de 2 estagios:

1. **Estagio 1 — Identificacao:** A IA identifica os alimentos e estima quantidades
2. **Estagio 2 — Lookup + Macros:** O sistema busca no banco de alimentos e calcula macronutrientes

---

## 1. Estagio 1 — Identificacao (Texto)

1. `MealParser.parse()` recebe descricao + contexto + db
2. `ContextBuilder.build_meal_context()` monta 5 secoes de contexto:
   - Perfil e metas (meta calorica, sexo, idade, peso)
   - Consumo de hoje (calorias e proteinas ja consumidas)
   - Porcoes historicas (top 15 alimentos dos ultimos 30 dias)
   - Refeicoes recentes do mesmo tipo (ultimas 3)
   - Media por tipo de refeicao (30 dias)
3. Envia para Gemini com `IDENTIFY_SYSTEM_PROMPT`:
   - Instrucoes para identificar cada alimento separadamente
   - Tabela de porcoes de referencia
   - Formato JSON esperado
4. Gemini retorna: `[{food_name, quantity, unit, preparation, confidence}]`

---

## 2. Estagio 1 — Identificacao (Foto)

1. `VisionParser.parse_base64()` recebe imagem em base64 + contexto + db
2. Envia para Gemini Vision com prompt de calibracao visual:
   - Prato raso brasileiro (26-28cm)
   - Espessura de proteinas (fino ~1cm → 80-100g)
   - Recipientes comuns (tigela 300ml, copo 200ml)
3. Gemini Vision identifica alimentos e estima porcoes em gramas
4. Retorna mesmo formato JSON

---

## 3. Estagio 2 — Lookup e Preenchimento de Macros

Para cada `IdentifiedFood` retornado pelo estagio 1:

1. Monta query: `food_name + preparation` (ex: "arroz cozido")
2. Chama `lookup_food(query, db)` — busca fuzzy no banco
3. Se encontrou com score suficiente:
   - Calcula fator: `quantity / 100`
   - Escala todos os macros: `calories = cal_100g × fator`
   - Cria `ParsedFoodItem` com macros do banco
4. Se nao encontrou:
   - Agrupa na lista de itens sem correspondencia
5. Para itens sem correspondencia:
   - Faz chamada unica ao Gemini com `FALLBACK_SYSTEM_PROMPT`
   - IA estima macros baseando-se em nome + preparo + quantidade
   - Cria `ParsedFoodItem` com macros estimados

---

## 4. Pos-processamento

### Correcao de Calorias (Atwater)
- Para cada item: calcula `expected = protein×4 + carbs×4 + fat×9`
- Se divergencia > 10%: substitui calorias pelo valor calculado

### Flag de Baixa Confianca
- Se qualquer item tem `confidence < 0.6`: `low_confidence = true`
- Bots e frontend exibem aviso ao usuario

---

## 5. Contexto do Usuario (5 secoes)

| Secao | Conteudo | Fonte |
|-------|----------|-------|
| Perfil e metas | Meta calorica, sexo, idade, altura, peso | `users` + `profiles` |
| Consumo de hoje | Calorias e proteinas ja consumidas | `meals` + `meal_items` |
| Porcoes historicas | Top 15 alimentos (30 dias) com medias | `meal_items` |
| Refeicoes recentes | Ultimas 3 do mesmo tipo | `meals` |
| Media por tipo | Calorias medias por tipo (30 dias) | `meals` |

---

## 6. GeminiClient — Cache e Retry

- **Cache:** SHA256 do prompt → Redis com TTL de 7 dias
- **Analise de refeicao:** sempre `use_cache=False` (cada refeicao e unica)
- **Retry:** exponencial com max 3 tentativas para erros 429/500
- **Timeout:** configuravel por tipo de chamada

---

## Arquivos-chave

| Arquivo | Responsabilidade |
|---------|------------------|
| `services/ai/meal_parser.py` | Parser de texto — pipeline 2 estagios |
| `services/ai/vision_parser.py` | Parser de foto — pipeline 2 estagios |
| `services/ai/food_lookup.py` | Busca no banco de alimentos |
| `services/ai/context_builder.py` | Monta contexto personalizado |
| `services/ai/gemini_client.py` | Cliente Gemini com cache e retry |
| `services/ai/utils.py` | `correct_calories()` e utilitarios |
