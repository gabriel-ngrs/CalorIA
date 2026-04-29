# CalorIA — Fluxo Completo: do Registro ao Banco

Este documento descreve o caminho percorrido desde o input do usuário no dashboard até a persistência da refeição no banco de dados.

---

## Visão Geral

```
Usuário (Dashboard Web)
        │
        ▼
  [1] Recepção da entrada (texto ou foto)
        │
        ▼
  [2] Contexto do usuário
        │
        ▼
  [3] Estágio 1 — IA identifica alimentos (sem macros)
        │
        ▼
  [4] Estágio 2 — Lookup nutricional (pg_trgm) + sanity check
        │           └── Fallback: estimativa em batch pela IA
        ▼
  [5] Pós-processamento (Atwater)
        │
        ▼
  [6] Confirmação no frontend
        │
        ▼
  [7] Persistência no banco (PostgreSQL)
```

---

## [1] Recepção da Entrada

O frontend chama diretamente:

```
POST /api/v1/ai/analyze-meal    — análise por texto
POST /api/v1/ai/analyze-photo   — análise por foto
POST /api/v1/meals              — persistência da refeição confirmada
```

---

## [2] Contexto do Usuário

**`services/ai/context_builder.py`** → `build_meal_context(user_id, db, today, description)`

Antes de chamar a IA, o sistema monta um contexto personalizado com 5 seções:

| Seção | O que contém |
|---|---|
| **Perfil e metas** | Meta calórica diária, sexo, idade, altura, peso atual |
| **Consumo de hoje** | Calorias e proteínas já consumidas no dia |
| **Porções históricas** | Top 15 alimentos mais registrados nos últimos 30 dias com médias de quantidade e calorias |
| **Refeições recentes do mesmo tipo** | Últimas 3 refeições do mesmo tipo (café, almoço, etc.) com lista de itens |
| **Média por tipo de refeição** | Calorias médias de cada tipo de refeição nos últimos 30 dias |

O tipo de refeição é inferido a partir da descrição (ex: "café com pão" → `breakfast`).

---

## [3] Estágio 1 — Identificação pela IA

**`services/ai/meal_parser.py`** (texto) / **`services/ai/vision_parser.py`** (foto)

A IA (Gemini 2.5 Flash) recebe a descrição/foto + contexto e retorna apenas a **identificação** dos alimentos, sem calcular macros:

```json
[
  {
    "food_name": "arroz branco cozido",
    "quantity": 200,
    "unit": "g",
    "preparation": "cozido",
    "kcal_estimate": 256,
    "confidence": 0.85
  },
  {
    "food_name": "frango peito grelhado",
    "quantity": 130,
    "unit": "g",
    "preparation": "grelhado",
    "kcal_estimate": 212,
    "confidence": 0.90
  }
]
```

O campo `kcal_estimate` é uma estimativa bruta da IA usada **exclusivamente** como sanity check no estágio seguinte — não substitui os macros reais do banco.

Para fotos, o system prompt inclui referências visuais de calibração (tamanhos de pratos brasileiros, espessura de proteínas, recipientes comuns).

---

## [4] Estágio 2 — Lookup Nutricional + Sanity Check

**`services/ai/food_lookup.py`** → `lookup_food(query, db)`

Para cada alimento identificado no Estágio 1:

### a) Query SQL

```sql
SELECT id, name, calories_100g, protein_100g, carbs_100g, fat_100g,
       fiber_100g, sodium_100g, sugar_100g, saturated_fat_100g,
       source, similarity(search_text, :q) AS score
FROM foods
WHERE search_text %>> :q OR similarity(search_text, :q) >= 0.18
ORDER BY score * CASE WHEN source='taco' THEN 1.4 ELSE 1.0 END DESC
LIMIT 5
```

- `%>>` é o operador word similarity do pg_trgm
- Índice GIN em `search_text` garante latência < 20ms com ~19.800 registros
- Dados TACO recebem boost **1.40×** para prevalecerem sobre Open Food Facts

### b) Threshold e sanity check

Se o melhor match tiver score ≥ 0.65:
- Calcula macros como `valor_100g × (quantity / 100)`
- Compara as calorias calculadas com `kcal_estimate` da IA
- Se divergência > **35%**: descarta o match e usa estimativa da IA (`data_source="ai_estimated"`)
- Se divergência ≤ 35%: usa macros do banco (`data_source = food.source`)

Isso evita que registros incorretos do Open Food Facts (ex: feijão carioca a 40 kcal vs TACO 76 kcal) contaminem o resultado.

### c) Itens sem match

Enviados juntos para `_estimate_macros_batch` — uma única chamada à IA com todos os itens sem match. Resultado com `data_source="ai_estimated"`, `food_id=None`.

---

## [5] Pós-processamento

### Correção de calorias (Atwater)

Aplicada após ambos os parsers:

```python
def correct_calories(items):
    for item in items:
        expected = item.protein * 4 + item.carbs * 4 + item.fat * 9
        if abs(item.calories - expected) / max(expected, 1) > 0.10:
            item.calories = round(expected, 1)
```

### Flag de baixa confiança

Se qualquer item tiver `confidence < 0.6`, `MealAnalysisResponse.low_confidence = True`. O frontend usa isso para alertar o usuário.

---

## [6] Confirmação no Frontend

O resultado é exibido no modal de refeição. O usuário pode:
- **Confirmar** → `POST /api/v1/meals` com os dados
- **Editar** → ajustar itens antes de confirmar
- **Cancelar** → descartar

---

## [7] Persistência no Banco

**`services/meal_service.py`** → `MealService.create_meal(user_id, data)`

```python
meal = Meal(user_id=user_id, meal_type=..., date=..., source="manual", ...)
db.add(meal)
await db.flush()

for item in data.items:
    db.add(MealItem(
        meal_id=meal.id,
        food_name=item.food_name,
        quantity=item.quantity,
        unit=item.unit,
        calories=item.calories,
        protein=item.protein,
        carbs=item.carbs,
        fat=item.fat,
        fiber=item.fiber,
        sodium=item.sodium,
        sugar=item.sugar,
        saturated_fat=item.saturated_fat,
        food_id=item.food_id,            # FK → foods (None se estimado)
        data_source=item.data_source,    # "taco", "openfoodfacts", "ai_estimated"
    ))

await db.commit()
```

### Estrutura das tabelas

**`meals`**

| Coluna | Tipo | Descrição |
|---|---|---|
| `id` | PK | |
| `user_id` | FK → users | |
| `meal_type` | ENUM | breakfast, lunch, dinner, snack, etc. |
| `date` | DATE | Data da refeição (indexada) |
| `source` | ENUM | manual |
| `name` | TEXT | Nome opcional |
| `notes` | TEXT | Observações |
| `created_at` | TIMESTAMP | Automático |

**`meal_items`**

| Coluna | Tipo | Descrição |
|---|---|---|
| `id` | PK | |
| `meal_id` | FK → meals | Cascade delete |
| `food_name` | VARCHAR(255) | Nome do alimento |
| `quantity` | FLOAT | Quantidade na porção |
| `unit` | VARCHAR(50) | Unidade (padrão: "g") |
| `calories` | FLOAT | Calorias totais da porção |
| `protein` | FLOAT | Proteínas (g) |
| `carbs` | FLOAT | Carboidratos (g) |
| `fat` | FLOAT | Gorduras (g) |
| `fiber` | FLOAT | Fibras (g) |
| `sodium` | FLOAT | Sódio (mg) |
| `sugar` | FLOAT | Açúcares (g) |
| `saturated_fat` | FLOAT | Gordura saturada (g) |
| `food_id` | FK → foods | Nulo se estimado pela IA |
| `data_source` | VARCHAR | "taco", "openfoodfacts" ou "ai_estimated" |

---

## Banco Nutricional

A tabela `foods` alimenta o lookup em [4]:

| Fonte | Registros | Descrição |
|---|---|---|
| **TACO** | ~307 | Tabela Brasileira de Composição de Alimentos — valores de laboratório, alta confiabilidade, boost 1.40× |
| **Open Food Facts** | ~19.500 | Produtos industrializados brasileiros com código de barras — valores de fabricantes |

---

## Cliente de IA — `GeminiClient`

**`services/ai/gemini_client.py`**

| Tipo | Modelo | Cache |
|---|---|---|
| Texto | `models/gemini-2.5-flash` | Redis 7 dias (SHA-256) para insights; sem cache para análise de refeição |
| Visão | `models/gemini-2.5-flash` | Sem cache |

Retry em 429: espera 15s → 30s → 60s → 120s (4 tentativas total).

---

## Arquivos-chave

| Arquivo | Responsabilidade |
|---|---|
| `services/ai/context_builder.py` | Monta contexto personalizado do usuário |
| `services/ai/food_lookup.py` | Busca fuzzy via pg_trgm + sanity check |
| `services/ai/meal_parser.py` | Pipeline dois estágios para texto |
| `services/ai/vision_parser.py` | Pipeline dois estágios para fotos |
| `services/ai/gemini_client.py` | Cliente Gemini 2.5 Flash com cache Redis e retry |
| `services/ai/utils.py` | `correct_calories`, `extract_json_from_ai_response` |
| `services/meal_service.py` | CRUD de refeições e resumo diário |
| `services/push_service.py` | Envio de notificações Web Push VAPID |
| `api/v1/ai.py` | Endpoints `/analyze-meal` e `/analyze-photo` |
| `api/v1/meals.py` | Endpoints CRUD `/meals` |
| `api/v1/push.py` | Endpoints de subscription Web Push |
| `models/food.py` | Tabela `foods` — banco nutricional unificado |
| `models/meal_item.py` | Tabela `meal_items` com food_id e data_source |
