# CalorIA — Fluxo Completo: da Mensagem ao Banco

Este documento descreve, de forma objetiva e didática, o caminho percorrido desde a mensagem do usuário até a persistência da refeição no banco de dados.

---

## Visão Geral

```
Usuário (WhatsApp / Telegram / Web)
        │
        ▼
  [1] Recepção da mensagem
        │
        ▼
  [2] Contexto do usuário
        │
        ▼
  [3] Lookup nutricional (pg_trgm)
        │
        ▼
  [4] Análise de IA (Groq / Llama)
        │
        ▼
  [5] Pós-processamento
        │
        ▼
  [6] Confirmação (bots)
        │
        ▼
  [7] Persistência no banco (PostgreSQL)
```

---

## [1] Recepção da Mensagem

### WhatsApp (via Evolution API)

O Evolution API é um serviço self-hosted que gerencia a sessão WhatsApp. Quando o usuário envia uma mensagem, ele faz um `POST` para o backend:

```
POST /webhook/whatsapp
```

**`bots/whatsapp/webhook.py`** recebe o payload e roteia:
- Mensagem de texto → `handle_text_message(number, text)`
- Imagem → faz download da mídia, então `handle_image_message(number, image_bytes)`
- Mensagens do próprio bot e grupos são ignoradas.

Se o texto for `"sim"` ou `"não"`, é verificado se há uma refeição pendente de confirmação no Redis antes de prosseguir para análise.

### Telegram

**`bots/telegram/bot.py`** usa polling (python-telegram-bot). O handler principal fica em `handlers/registration.py` e usa um `ConversationHandler` com três estados:

- **ANALYZING**: recebe texto ou foto, chama a IA.
- **CONFIRMING**: exibe botões ✅ Confirmar / ✏️ Corrigir / ❌ Cancelar.
- **EDITING**: permite corrigir itens antes de confirmar.

### API Web (Dashboard)

O frontend chama diretamente:

```
POST /api/v1/ai/analyze-meal    — análise por texto
POST /api/v1/ai/analyze-photo   — análise por foto
POST /api/v1/meals              — persistência da refeição
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

Esse contexto é injetado no prompt da IA para que ela calibre as porções com base no histórico real do usuário.

---

## [3] Lookup Nutricional (pg_trgm)

**`services/ai/taco_lookup.py`** → `find_foods_in_text(text, db)`

Antes de chamar a IA (no caso de texto), o sistema faz uma busca fuzzy no banco nutricional usando o índice trigrama do PostgreSQL.

### Como funciona

**a) Normalização**
```
"Frango Grelhado com Batata" → "frango grelhado com batata"
```
Remove acentos e converte para minúsculas.

**b) Extração de candidatos (n-gramas)**

Para queries com múltiplas palavras, gera bigramas a 4-gramas:
```
"frango grelhado" → "frango grelhado com", "grelhado com batata",
                    "frango grelhado com batata", etc.
```
Para queries de uma única palavra, também gera 1-gramas.

**c) Query SQL por candidato**
```sql
SELECT id, name, calories_100g, protein_100g, carbs_100g, fat_100g, fiber_100g,
       similarity(search_text, :q) AS score
FROM taco_foods
WHERE search_text %>> :q OR similarity(search_text, :q) >= 0.18
ORDER BY score DESC
LIMIT 20
```

- `%>>` é o operador de similaridade por palavras do pg_trgm.
- O índice GIN em `search_text` garante latência < 20ms mesmo com 20k registros.

**d) Boost por fonte**

O banco contém dados de duas origens com qualidades diferentes:

| Fonte | Descrição | Boost |
|---|---|---|
| `taco` | Tabela TACO — base oficial brasileira, valores de laboratório | **1.40×** |
| `openfoodfacts` | Open Food Facts — 19k produtos, valores de fabricantes | 1.00× |

O boost garante que os dados da TACO sempre prevalecem sobre o OFF quando o mesmo alimento existe nas duas fontes.

**e) Resultado**

Lista de até 20 `TacoMatch` ordenados por score boosted. Usada de duas formas:
- **meal_parser**: injetada no prompt como valores exatos antes da chamada à IA.
- **vision_parser**: usada depois da IA para substituir estimativas visuais por valores do banco.

---

## [4] Análise de IA

### 4a. Análise de texto — `MealParser`

**`services/ai/meal_parser.py`** → `MealParser(client).parse(description, user_context, db)`

O prompt enviado à IA tem três camadas:

```
[System Prompt]
Você é um nutricionista brasileiro. Regras: retorne APENAS JSON, calcule
macros para a porção total, diferencie método de preparo, use banco
nutricional quando disponível, etc.

[User Message]
=== CONTEXTO DO USUÁRIO ===
Meta: 2000 kcal | Consumido hoje: 500 kcal
Suas porções habituais: arroz branco cozido ~180g (~230 kcal)...

=== BANCO NUTRICIONAL (USE ESTES VALORES — NÃO ESTIME) ===
Arroz branco cozido: 128 kcal | prot 2.5g | carb 28.1g | gord 0.2g (por 100g)
Frango peito grelhado: 163 kcal | prot 28.6g | carb 0.0g | gord 4.8g (por 100g)

Descrição: 200g de arroz com frango grelhado
```

A IA retorna um array JSON:
```json
[
  {"food_name": "arroz branco cozido", "quantity": 200, "unit": "g",
   "calories": 256, "protein": 5.0, "carbs": 56.2, "fat": 0.4, "confidence": 0.95},
  {"food_name": "frango peito grelhado", "quantity": 130, "unit": "g",
   "calories": 212, "protein": 37.2, "carbs": 0.0, "fat": 6.2, "confidence": 0.90}
]
```

### 4b. Análise de foto — `VisionParser`

**`services/ai/vision_parser.py`** → `VisionParser(client).parse_base64(image_base64, db=db)`

O fluxo é diferente:

1. A foto é enviada diretamente para o modelo de visão (Llama 4 Scout via Groq).
2. O system prompt inclui **referências visuais de calibração**:
   - Tamanhos de pratos brasileiros (26-28cm)
   - Espessura de proteínas (bife fino ~1cm → 80-100g)
   - Recipientes comuns (tigela 300ml, copo 200ml)
3. A IA estima os alimentos visíveis e as porções em gramas.
4. **Após** a resposta da IA, o sistema enriquece com o banco (veja seção 5).

### 4c. Cliente de IA — `GeminiClient`

**`services/ai/gemini_client.py`**

| Tipo | Modelo | Cache |
|---|---|---|
| Texto | `llama-3.3-70b-versatile` (Groq) | Redis 7 dias (SHA256 do prompt) |
| Visão | `meta-llama/llama-4-scout-17b-16e-instruct` (Groq) | Sem cache |

Texto de análise de refeição sempre é chamado com `use_cache=False` — cada refeição é única.

---

## [5] Pós-processamento

### Correção de calorias (Atwater)

Após a resposta da IA (em ambos os parsers):

```python
def _correct_calories(items):
    for item in items:
        expected = item.protein * 4 + item.carbs * 4 + item.fat * 9
        # Se divergência > 10%, substitui pelo valor calculado
        if abs(item.calories - expected) / expected > 0.10:
            item.calories = round(expected, 1)
```

### Enriquecimento por banco (vision_parser)

Para cada item identificado pela IA na foto:

```python
if item.unit in ("g", "gramas", "gr"):
    matches = await find_foods_in_text(item.food_name, db)
    if matches and matches[0].score >= 0.50:
        food = matches[0].food
        factor = item.quantity / 100.0
        item.calories = round(food.calories_100g * factor, 1)
        item.protein  = round(food.protein_100g  * factor, 2)
        # ... demais macros
        item.confidence = min(item.confidence + 0.1, 1.0)
```

Se o banco reconhece "frango grelhado" com score ≥ 0.50 e a IA estimou 200g, os macros são recalculados com precisão: `valor_100g × (200/100)`.

### Flag de baixa confiança

Se qualquer item tiver `confidence < 0.6`, `MealAnalysisResponse.low_confidence = True`. Os bots usam isso para alertar o usuário de que a análise pode ser imprecisa.

---

## [6] Confirmação (bots)

### WhatsApp

O resultado da análise **não é salvo imediatamente**. É armazenado no Redis por 5 minutos:

```
Redis key: wa_pending:{number}
TTL: 300s
Value: JSON dos itens analisados
```

O bot envia a mensagem de confirmação:
```
📊 Refeição analisada

• arroz branco cozido — 200g
• frango peito grelhado — 130g

🔥 468 kcal | 🥩 42.2g prot | 🍞 56.2g carb | 🧈 6.6g gord

Está correto? Responda sim ou não.
```

Quando o usuário responde "sim", os dados são recuperados do Redis e persistidos.

### Telegram

Usa botões inline (ConversationHandler):
- **✅ Confirmar** → persiste
- **✏️ Corrigir** → solicita edição por texto
- **❌ Cancelar** → descarta

---

## [7] Persistência no Banco

**`services/meal_service.py`** → `MealService.create_meal(user_id, data)`

```python
# 1. Cria o registro da refeição
meal = Meal(
    user_id=user_id,
    meal_type=data.meal_type,   # breakfast, lunch, dinner, snack...
    date=data.date,
    source=data.source,          # telegram, whatsapp, manual
    name=data.name,
    notes=data.notes,
)
db.add(meal)
await db.flush()  # obtém o ID sem commitar

# 2. Cria os itens individuais
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
| `source` | ENUM | telegram, whatsapp, manual |
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
| `protein` | FLOAT | Proteínas totais (g) |
| `carbs` | FLOAT | Carboidratos totais (g) |
| `fat` | FLOAT | Gorduras totais (g) |
| `fiber` | FLOAT | Fibras totais (g) |

---

## Exemplo completo: "200g arroz com frango grelhado" via WhatsApp

```
Usuário → WhatsApp → Evolution API → POST /webhook/whatsapp
                                              │
                                    webhook.py roteia para
                                    handle_text_message()
                                              │
                                    ┌─────────▼──────────┐
                                    │ Busca usuário por  │
                                    │ número no banco    │
                                    └─────────┬──────────┘
                                              │
                                    ┌─────────▼──────────────────────────────┐
                                    │ build_meal_context()                   │
                                    │ → Meta: 2000 kcal                      │
                                    │ → Consumido hoje: 500 kcal             │
                                    │ → Porção habitual de arroz: ~180g      │
                                    └─────────┬──────────────────────────────┘
                                              │
                                    ┌─────────▼──────────────────────────────┐
                                    │ find_foods_in_text() via pg_trgm       │
                                    │ → Arroz branco cozido  score=0.95 TACO │
                                    │ → Frango peito grelhado score=0.91 TACO│
                                    └─────────┬──────────────────────────────┘
                                              │
                                    ┌─────────▼──────────────────────────────┐
                                    │ MealParser.parse()                     │
                                    │ → Prompt: contexto + TACO + descrição  │
                                    │ → Groq API (Llama 70B)                 │
                                    │ → JSON: arroz 200g, frango 130g        │
                                    └─────────┬──────────────────────────────┘
                                              │
                                    ┌─────────▼──────────────────────────────┐
                                    │ _correct_calories()                    │
                                    │ → Valida protein×4 + carbs×4 + fat×9  │
                                    └─────────┬──────────────────────────────┘
                                              │
                                    ┌─────────▼──────────────────────────────┐
                                    │ Redis: wa_pending:{number} = JSON      │
                                    │ TTL: 300s                              │
                                    └─────────┬──────────────────────────────┘
                                              │
                              Mensagem ao usuário: "468 kcal — confirmar?"
                                              │
                                    Usuário responde "sim"
                                              │
                                    ┌─────────▼──────────────────────────────┐
                                    │ _confirm_pending_meal()                │
                                    │ → Lê Redis, monta MealCreate           │
                                    │ → MealService.create_meal()            │
                                    └─────────┬──────────────────────────────┘
                                              │
                                    ┌─────────▼──────────────────────────────┐
                                    │ PostgreSQL                             │
                                    │ INSERT INTO meals (...)                │
                                    │ INSERT INTO meal_items (...) × 2       │
                                    │ COMMIT                                 │
                                    └────────────────────────────────────────┘
                                              │
                              "✅ Refeição salva! (468 kcal)"
```

---

## Banco Nutricional

O banco de dados nutricional (`taco_foods`) alimenta o lookup em [3] e o enriquecimento em [5]:

| Fonte | Registros | Descrição |
|---|---|---|
| **TACO** | 307 | Tabela Brasileira de Composição de Alimentos — valores de laboratório, alta confiabilidade |
| **Open Food Facts** | ~19.500 | Produtos industrializados brasileiros com código de barras — valores de fabricantes |

Dados TACO recebem boost de **1.40×** no score de busca para sempre prevalecerem sobre OFF quando ambos têm o mesmo alimento.

---

## Arquivos-chave

| Arquivo | Responsabilidade |
|---|---|
| `bots/whatsapp/webhook.py` | Recebe webhook da Evolution API, roteia eventos |
| `bots/whatsapp/handlers.py` | Processa texto/foto, gerencia confirmação via Redis |
| `bots/telegram/handlers/registration.py` | ConversationHandler para refeições no Telegram |
| `services/ai/context_builder.py` | Monta contexto personalizado do usuário |
| `services/ai/taco_lookup.py` | Busca fuzzy via pg_trgm no banco nutricional |
| `services/ai/meal_parser.py` | Analisa texto com IA + contexto TACO |
| `services/ai/vision_parser.py` | Analisa foto com IA + enriquecimento pós-análise |
| `services/ai/gemini_client.py` | Cliente Groq com cache Redis e retry exponencial |
| `services/meal_service.py` | CRUD de refeições e resumo diário |
| `api/v1/ai.py` | Endpoints `/analyze-meal` e `/analyze-photo` |
| `api/v1/meals.py` | Endpoints CRUD `/meals` |
| `models/meal.py` | Tabela `meals` (SQLAlchemy) |
| `models/meal_item.py` | Tabela `meal_items` (SQLAlchemy) |
