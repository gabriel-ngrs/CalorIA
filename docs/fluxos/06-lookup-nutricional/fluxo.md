# Fluxo de Lookup Nutricional

## Visao Geral

O sistema possui um banco de alimentos com dados nutricionais de duas fontes: TACO (oficial brasileira) e Open Food Facts. A busca usa similaridade fuzzy via `pg_trgm` do PostgreSQL.

---

## 1. Pipeline de Busca

1. Recebe `food_name` (ex: "frango grelhado")
2. **Normalizacao:** remove acentos, converte para minusculas
3. **Geracao de n-gramas:** para queries com multiplas palavras, gera bigramas a 4-gramas. Para palavra unica, tambem gera 1-gramas
4. **Query SQL por candidato:**
   - Usa operador `%>>` (similaridade por palavras do pg_trgm)
   - Ou `similarity() >= 0.18` como fallback
   - Indice GIN em `search_text` garante < 20ms
   - Limite de 20 resultados por candidato
5. **Boost por fonte:**
   - TACO: score × 1.40 (dados de laboratorio, alta confiabilidade)
   - Open Food Facts: score × 1.00 (valores de fabricantes)
6. **Deduplicacao e ordenacao** por score final
7. Retorna top matches como `FoodMatch`

---

## 2. Exemplo Pratico

```
Entrada: "arroz branco cozido"
Normalizado: "arroz branco cozido"

N-gramas:
  "arroz", "branco", "cozido",
  "arroz branco", "branco cozido",
  "arroz branco cozido"

Resultados (antes do boost):
  1. "Arroz, integral, cozido" (TACO)    → 0.72
  2. "Arroz, tipo 1, cozido"  (TACO)    → 0.68
  3. "Arroz branco"           (OFF)      → 0.65

Apos boost:
  1. "Arroz, integral, cozido" (TACO)    → 0.72 × 1.40 = 1.008
  2. "Arroz, tipo 1, cozido"  (TACO)    → 0.68 × 1.40 = 0.952
  3. "Arroz branco"           (OFF)      → 0.65 × 1.00 = 0.650
```

---

## 3. Uso nos Parsers

O lookup e usado no **estagio 2** de ambos os parsers:

- **MealParser:** busca cada alimento identificado pela IA no banco. Se encontra, escala macros. Se nao, manda para fallback da IA.
- **VisionParser:** mesmo fluxo. Ao encontrar no banco, incrementa confidence em +0.1.

---

## 4. Banco de Alimentos

| Fonte | Registros | Qualidade | Boost |
|-------|-----------|-----------|-------|
| **TACO** | ~307 | Alta — valores de laboratorio | 1.40× |
| **Open Food Facts** | ~19.500 | Media — valores de fabricantes | 1.00× |

**Campos por 100g:** calories, protein, carbs, fat, fiber, sodium (opcional), sugar (opcional), saturated_fat (opcional)

---

## Arquivos-chave

| Arquivo | Responsabilidade |
|---------|------------------|
| `services/ai/food_lookup.py` | Busca fuzzy no banco de alimentos |
| `models/food.py` | Modelo SQLAlchemy da tabela `foods` |
