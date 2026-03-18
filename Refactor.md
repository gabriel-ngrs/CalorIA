# Plano de Refatoração — Banco de Alimentos e Pipeline de IA

## Contexto

O pipeline de análise de refeições atual tem dois problemas estruturais: a IA é responsável tanto por identificar alimentos quanto por estimar macros (frágil e inconsistente), e o link entre um `MealItem` e o registro em `taco_foods` é perdido logo após a análise — `food_name` fica como texto livre sem FK. Além disso, a tabela `taco_foods` é pequena (~200 itens hardcoded) e falta rastreabilidade de origem dos dados nutricionais.

**Objetivo:** separar responsabilidades (IA identifica, banco fornece valores), expandir o banco de alimentos para ~10k+ itens (TACO completo + Open Food Facts BR + USDA Foundation), adicionar micronutrientes essenciais (sódio, açúcar, gordura saturada), e rastrear a origem de cada valor nutricional salvo.

---

## Arquitetura Nova vs Atual

```
ATUAL:
  texto/foto → IA (identifica + estima macros) → meal_items (sem FK)

NOVO:
  texto/foto → IA (só identifica: nome + qtd + preparo)
             → lookup em foods (pg_trgm, score ≥ 0.65) → valores do banco + food_id
             → fallback se miss: IA estima macros → data_source="ai_estimated"
             → meal_items (com food_id + data_source)
```

---

## Sequência de Execução

### GRUPO 1 — Schema do banco
**Commit:** `refactor(db): renomeia taco_foods para foods e adiciona micronutrientes`

**Arquivo a criar:** `backend/alembic/versions/20260318_XXXX_foods_refactor.py`

```python
# upgrade():
op.rename_table("taco_foods", "foods")
op.execute("ALTER INDEX ix_taco_foods_search_trgm RENAME TO ix_foods_search_trgm")
op.execute("ALTER INDEX ix_taco_foods_external_id RENAME TO ix_foods_external_id")
op.execute("ALTER INDEX IF EXISTS ix_taco_foods_name RENAME TO ix_foods_name")
op.execute("ALTER INDEX IF EXISTS ix_taco_foods_category RENAME TO ix_foods_category")
op.add_column("foods", sa.Column("sodium_100g",        sa.Float, nullable=True))
op.add_column("foods", sa.Column("sugar_100g",         sa.Float, nullable=True))
op.add_column("foods", sa.Column("saturated_fat_100g", sa.Float, nullable=True))

# downgrade(): reverso — renomear índices de volta, drop columns, rename_table
```

---

**Commit:** `refactor(db): adiciona food_id, data_source e micronutrientes em meal_items`

**Arquivo a criar:** `backend/alembic/versions/20260318_YYYY_meal_items_food_ref.py`

```python
# upgrade():
op.add_column("meal_items", sa.Column("food_id", sa.Integer, nullable=True))
op.create_foreign_key("fk_meal_items_food_id", "meal_items", "foods",
                       ["food_id"], ["id"], ondelete="SET NULL")
op.create_index("ix_meal_items_food_id", "meal_items", ["food_id"])
op.add_column("meal_items", sa.Column("data_source", sa.String(20), nullable=True))
op.add_column("meal_items", sa.Column("sodium",        sa.Float, nullable=True))
op.add_column("meal_items", sa.Column("sugar",         sa.Float, nullable=True))
op.add_column("meal_items", sa.Column("saturated_fat", sa.Float, nullable=True))
```

---

### GRUPO 2 — Modelos Python
**Commit:** `refactor(models): substitui TacoFood por Food e expande MealItem`

**Arquivo a criar:** `backend/app/models/food.py`
- Copiar `taco_food.py`, renomear classe `TacoFood` → `Food`, `__tablename__ = "foods"`
- Adicionar campos:
  ```python
  sodium_100g:        Mapped[float | None] = mapped_column(Float, nullable=True)
  sugar_100g:         Mapped[float | None] = mapped_column(Float, nullable=True)
  saturated_fat_100g: Mapped[float | None] = mapped_column(Float, nullable=True)
  ```
- Método `format_for_prompt()` permanece idêntico

**Arquivo a criar (stub temporário):** `backend/app/models/taco_food.py`
```python
from app.models.food import Food as TacoFood  # alias de compatibilidade
__all__ = ["TacoFood"]
```

**Arquivo a modificar:** `backend/app/models/meal_item.py`
- Adicionar após `raw_input`:
  ```python
  food_id:       Mapped[int | None] = mapped_column(Integer, ForeignKey("foods.id", ondelete="SET NULL"), nullable=True, index=True)
  data_source:   Mapped[str | None] = mapped_column(String(20), nullable=True)
  sodium:        Mapped[float | None] = mapped_column(Float, nullable=True)
  sugar:         Mapped[float | None] = mapped_column(Float, nullable=True)
  saturated_fat: Mapped[float | None] = mapped_column(Float, nullable=True)
  ```

**Arquivo a modificar:** `backend/app/models/__init__.py`
- Adicionar `from app.models.food import Food` e incluir `"Food"` em `__all__`

---

### GRUPO 3 — Schemas Pydantic
**Commit:** `refactor(schemas): adiciona food_id, data_source e micronutrientes`

**Arquivo a modificar:** `backend/app/schemas/ai.py` — classe `ParsedFoodItem`:
```python
sodium:        float | None = None
sugar:         float | None = None
saturated_fat: float | None = None
data_source:   str | None = None
food_id:       int | None = None
```

**Arquivo a modificar:** `backend/app/schemas/meal.py` — classes `MealItemCreate` e `MealItemResponse`:
```python
food_id:       int | None = None
data_source:   str | None = None
sodium:        float | None = None
sugar:         float | None = None
saturated_fat: float | None = None
```

---

### GRUPO 4 — Serviço de lookup
**Commit:** `refactor(services): extrai food_lookup com suporte a food_id e threshold configuravel`

**Arquivo a criar:** `backend/app/services/ai/food_lookup.py`
- Copiar lógica de `taco_lookup.py`
- Renomear: `TacoMatch` → `FoodMatch`, adicionar campo `food_id: int`
- Atualizar SQL: `FROM taco_foods` → `FROM foods`; adicionar `sodium_100g, sugar_100g, saturated_fat_100g` no SELECT
- Renomear: `format_taco_context` → `format_food_context`
- **Nova função:**
  ```python
  async def lookup_food(food_name: str, db: AsyncSession, min_score: float = 0.65) -> FoodMatch | None:
      """Retorna o melhor match para um alimento. None se score < min_score."""
      matches = await find_foods_in_text(food_name, db)
      if not matches or matches[0].score < min_score:
          return None
      return matches[0]
  ```

**Arquivo a modificar (stub):** `backend/app/services/ai/taco_lookup.py`
```python
from app.services.ai.food_lookup import (
    FoodMatch as TacoMatch, find_foods_in_text,
    format_food_context as format_taco_context, lookup_food,
)
__all__ = ["TacoMatch", "find_foods_in_text", "format_taco_context", "lookup_food"]
```

---

### GRUPO 5 — Pipeline de IA (dois estágios)
**Commit:** `refactor(ai): refatora meal_parser para pipeline dois estagios identificacao e lookup`

**Arquivo a modificar:** `backend/app/services/ai/meal_parser.py`

1. **Novo `_SYSTEM_PROMPT`** — IA retorna apenas identificação, SEM macros:
   ```json
   [{"food_name": "arroz branco cozido", "quantity": 200, "unit": "g", "preparation": "cozido", "confidence": 0.9}]
   ```

2. **Nova classe interna `IdentifiedFood`** (não exposta na API):
   ```python
   class IdentifiedFood(BaseModel):
       food_name: str; quantity: float; unit: str = "g"
       preparation: str | None = None; confidence: float = 0.8
   ```

3. **Novo método `_lookup_and_fill(items, db)`:**
   - Para cada item: `lookup_food(f"{food_name} {preparation}", db)`
   - Se match (score ≥ 0.65): calcula macros via `quantidade/100 × valores_100g`, preenche `food_id` e `data_source=food.source`
   - Se miss: chama `_estimate_macros_batch` para os itens sem match (uma única chamada IA agrupada)

4. **Método `_estimate_macros_batch(items)`** — fallback único agrupado, aplica `_correct_calories`, seta `data_source="ai_estimated"`, `food_id=None`

5. **`parse()` refatorado:**
   ```python
   identified = await self._identify_foods(description, user_context)
   items = await self._lookup_and_fill(identified, db) if db else await self._estimate_all(identified)
   ```

6. **Remover `_TACO_TABLE`** estático (já era legado)

---

**Commit:** `refactor(ai): refatora vision_parser para pipeline dois estagios e remove tabela estatica`

**Arquivo a modificar:** `backend/app/services/ai/vision_parser.py`
- Remover `_enrich_with_db()` — substituída por `_lookup_and_fill` de `food_lookup.py`
- Remover constante `_ENRICH_MIN_SCORE = 0.50` (threshold global agora é 0.65)
- System prompt: pedir identificação + preparo, sem macros (mesmo padrão do text parser)
- `parse_base64()`: mesmo padrão de dois estágios do `meal_parser`
- `_correct_calories` mover para `utils.py` se ainda não estiver lá (usada no fallback IA)

---

### GRUPO 6 — Verificação da persistência
**Commit:** `refactor(services): verifica persistencia de food_id e data_source em meal_items`

**Arquivo a verificar:** `backend/app/services/meal_service.py`
- O método `create_meal` usa `MealItem(**item_data.model_dump())` — funciona automaticamente com os novos campos nullable
- Confirmar que nenhum campo novo está sendo descartado antes do `model_dump()`
- Nenhuma mudança estrutural esperada — apenas verificação e possível ajuste mínimo

---

### GRUPO 7 — Scripts de ingestão de dados
**Commit:** `feat(scripts): expande seed TACO com tabela completa 4a edicao e micronutrientes`

**Arquivo a modificar:** `backend/scripts/seed_taco.py`
- Atualizar import: `from app.models.food import Food`
- Expandir `TACO_DATA` para os ~597 alimentos da TACO 4ª edição (UNICAMP/MS), incluindo:
  - Bebidas alcoólicas e não-alcoólicas (parcial hoje)
  - Preparações mistas (feijoada, moqueca, cozidos)
  - Nozes, sementes, oleaginosas
  - Molhos e condimentos
  - Sopas e caldos
  - Alimentos infantis
- Todos os itens com `sodium_100g`, `sugar_100g`, `saturated_fat_100g` onde TACO fornece
- Usar `ON CONFLICT (name) DO UPDATE SET ...` para permitir atualização

---

**Commit:** `feat(scripts): adiciona sodium, sugar e saturated_fat na importacao Open Food Facts`

**Arquivo a modificar:** `backend/scripts/import_off.py`
- Atualizar import: `from app.models.food import Food`
- Extrair micronutrientes da resposta OFF:
  ```python
  sodium        = float(nutriments.get("sodium_100g") or 0)
  sugar         = float(nutriments.get("sugars_100g") or 0)
  saturated_fat = float(nutriments.get("saturated-fat_100g") or 0)
  ```
- Validação adicional: `sodium > 10` indica dado corrompido (sódio em g > 10g/100g é fisicamente impossível)
- Atualizar INSERT para incluir os três novos campos

---

**Commit:** `feat(scripts): adiciona importador USDA FoodData Central Foundation Foods`

**Arquivo a criar:** `backend/scripts/import_usda.py`
- API: `GET https://api.nal.usda.gov/fdc/v1/foods/list?dataType=Foundation&pageSize=200&api_key=KEY`
- Chave gratuita em: https://fdc.nal.usda.gov/api-guide.html
- Mapeamento de nutrientes:
  ```python
  _NUTRIENT_MAP = {
      "Energy": "calories",
      "Protein": "protein",
      "Carbohydrate, by difference": "carbs",
      "Total lipid (fat)": "fat",
      "Fiber, total dietary": "fiber",
      "Sodium, Na": "sodium",          # mg → dividir por 1000 para g
      "Sugars, total including NLEA": "sugar",
      "Fatty acids, total saturated": "saturated_fat",
  }
  ```
- Nomes em inglês → manter como alias; gerar `name` em português via dicionário de mapeamento (sem IA)
- `source="usda"`, `external_id=str(fdcId)`
- Paginação com retry + backoff, `--dry-run`, `--limit`, `--start-page`
- INSERT `ON CONFLICT (name) DO NOTHING`
- Foco: Foundation Foods (~2.200 alimentos inteiros com dados analíticos de alta qualidade)

---

### GRUPO 8 — Frontend
**Commit:** `feat(frontend): adiciona micronutrientes e rastreabilidade nos tipos de refeicao`

**Arquivo a modificar:** `frontend/types/index.ts`

```typescript
// MealItem — campos novos
sodium: number | null;
sugar: number | null;
saturated_fat: number | null;
food_id: number | null;
data_source: string | null; // "taco" | "openfoodfacts" | "usda" | "ai_estimated" | null

// MealItemCreate — campos opcionais
sodium?: number | null;
sugar?: number | null;
saturated_fat?: number | null;
food_id?: number | null;
data_source?: string | null;

// ParsedFoodItem — campos novos
sodium: number | null;
sugar: number | null;
saturated_fat: number | null;
food_id: number | null;
data_source: string | null;
```

Nenhuma mudança em `useMeals.ts` necessária — os novos campos são opcionais/nullable.

---

### GRUPO 9 — Limpeza
**Commit:** `chore: remove aliases de compatibilidade taco_food e taco_lookup`

- Deletar `backend/app/models/taco_food.py`
- Deletar `backend/app/services/ai/taco_lookup.py`
- Atualizar `backend/app/models/__init__.py`: remover `TacoFood`
- Verificar que nenhum import de `taco_food` ou `taco_lookup` permanece no codebase

---

## Dependências (ordem obrigatória)

```
migração (GRUPO 1)
    ↓
modelos Python (GRUPO 2)
    ↓
schemas Pydantic (GRUPO 3)
    ↓
food_lookup.py (GRUPO 4)
    ↓
meal_parser + vision_parser (GRUPO 5)
    ↓
meal_service verificação (GRUPO 6)    scripts de dados (GRUPO 7) ← paralelo ao GRUPO 5+
    ↓                                          ↓
frontend tipos (GRUPO 8)              (independente)
    ↓
limpeza de stubs (GRUPO 9)
```

---

## Verificação End-to-End

```bash
# 1. Migração
alembic upgrade head
# psql: \d foods → colunas sodium_100g, sugar_100g, saturated_fat_100g
# psql: \d meal_items → colunas food_id, data_source, sodium, sugar, saturated_fat

# 2. Seed expandido
python scripts/seed_taco.py
# SELECT count(*) FROM foods WHERE source='taco'; → ~597

# 3. Import USDA (dry-run)
python scripts/import_usda.py --api-key DEMO_KEY --limit 50 --dry-run

# 4. Análise de refeição com alimento conhecido (deve usar banco)
# POST /api/v1/ai/analyze-meal {"description": "200g de arroz branco cozido"}
# → items[0].data_source = "taco", items[0].food_id != null

# 5. Análise com alimento desconhecido (deve usar fallback IA)
# POST /api/v1/ai/analyze-meal {"description": "pastel de frango com catupiry"}
# → items[0].data_source = "ai_estimated", items[0].food_id = null

# 6. Salvar refeição e verificar persistência de food_id
# POST /api/v1/meals {...}
# psql: SELECT food_id, data_source FROM meal_items ORDER BY id DESC LIMIT 5;

# 7. Testes automatizados
cd backend && pytest
cd frontend && npm run lint
```

---

## Notas de Decisão

- **`_correct_calories`** só é aplicado no fallback `ai_estimated` — valores do banco são autoritativos
- **Dados históricos** em `meal_items` ficarão com `food_id=NULL` e `data_source=NULL` — correto e esperado
- **`format_food_context`** se torna obsoleta no pipeline principal mas é mantida para debug/logging
- **`food.source`** vs **`meal_item.data_source`**: `food.source` = origem do registro no banco; `meal_item.data_source` = origem dos valores nutricionais no item (quando há match: igual ao `food.source`; quando fallback: `"ai_estimated"`)
- **USDA requer chave de API** gratuita — documentar no `.env.example` como `USDA_API_KEY`

---

## Status

- [ ] GRUPO 1 — Migrações do banco
- [ ] GRUPO 2 — Modelos Python
- [ ] GRUPO 3 — Schemas Pydantic
- [ ] GRUPO 4 — Serviço food_lookup
- [ ] GRUPO 5 — Pipeline de IA (meal_parser + vision_parser)
- [ ] GRUPO 6 — Verificação meal_service
- [ ] GRUPO 7 — Scripts de ingestão (seed_taco, import_off, import_usda)
- [ ] GRUPO 8 — Frontend types
- [ ] GRUPO 9 — Limpeza de stubs
