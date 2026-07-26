# Fluxo de Lookup Nutricional

## Visao Geral

O sistema possui um banco de alimentos com dados nutricionais de varias fontes. A busca usa similaridade fuzzy via `pg_trgm` do PostgreSQL, com comparacao **insensivel a acento nos dois lados**.

---

## 1. Pipeline de Busca

1. Recebe `food_name` (ex: "frango grelhado"), ja limpo de preparo irrelevante
2. **Normalizacao:** remove acentos, converte para minusculas
3. **Geracao de n-gramas:** para queries com multiplas palavras, gera bigramas a 4-gramas. Para palavra unica, tambem gera 1-gramas.
   N-gramas que **comecam ou terminam em stopword** sao descartados — um fragmento como "do leite" nao denota alimento e produzia casamento espurio (a consulta "manteiga derivado do leite" casava com o alimento `Leite`, 26,8 kcal/100g).
4. **Uma unica query SQL para todos os n-gramas** (`unnest` + `LATERAL`), em vez de uma query por candidato:
   - Predicados `%>>` (strict_word_similarity) e `%` (similarity), **ambos indexaveis**
   - Indice GIN de expressao `ix_foods_search_unaccent_trgm` sobre `caloria_unaccent(search_text)`
   - Piso de candidato: `pg_trgm.similarity_threshold = 0.40`
   - Limite de 20 resultados por n-grama; melhor score por alimento e agregado com `max()`
5. **Boost por fonte:** TACO score × 1.40; demais × 1.00
6. **Ordenacao** por score final; aceite no pipeline exige score ≥ 0.65
7. Retorna top matches como `FoodMatch`

### Por que `unaccent` nos dois lados

A normalizacao removia acento **so da consulta**, enquanto `search_text` mantinha. Resultado:
`similarity('feijao carioca cozido', 'feijão carioca cozido')` = **0,75** em vez de 1,00.
Isso atingia 43% das linhas `taco` (98 de 228) — exatamente os basicos brasileiros
(Feijao, Oleo, Macarrao, Pao, Acucar, Limao, Maca).

Medicao do impacto (conjunto rotulado de 40 consultas): **F1 0,776 → 0,857**.

### Por que o predicado mudou

O `WHERE` usava `similarity(...) >= :min`, que **nao e indexavel**: o planner caia em
Seq Scan sobre 42 mil linhas — 238 ms por n-grama medidos com `EXPLAIN ANALYZE`.
Com `%>>` / `%` o planner usa BitmapOr sobre o indice GIN. Latencia medida do lookup
completo: **44 ms**.

---

## 2. Exemplo Pratico

```
Entrada: "arroz branco cozido"
Normalizado: "arroz branco cozido"

N-gramas (sem os de borda com stopword):
  "arroz branco", "branco cozido", "arroz branco cozido"

Uma query so, com unnest dos 3 termos.
Score = max(similarity) por alimento, depois boost por fonte.
Aceite: score >= 0.65
```

---

## 3. Uso nos Parsers

O lookup e usado no **estagio 2** de ambos os parsers:

- **MealParser:** para cada alimento identificado, a porcao e primeiro normalizada
  para gramas (ver `docs/fluxos/05-analise-ia`), depois o alimento e buscado no banco.
  A consulta vai **limpa**: `preparation` so entra quando informa algo real —
  `"azeite nao aplicavel"` pontuava 0,6364 (abaixo do limiar) enquanto `"azeite"` pontua 1,00.
- **VisionParser:** mesmo lookup. Ao encontrar no banco, incrementa confidence em +0.1.

---

## 4. Banco de Alimentos

Contagem real (2026-07-26):

| Fonte | Registros | Qualidade | Boost |
|-------|-----------|-----------|-------|
| `ai_estimated` | 23.398 | **Baixa — estimativa da propria IA**, gerada por `scripts/enrich_foods.py` | 1.00× |
| `openfoodfacts` | 18.195 | Media — valores de fabricantes, colaborativo | 1.00× |
| `usda` | 247 | Alta — base oficial americana | 1.00× |
| `taco` | 228 | **Alta — tabela brasileira curada**, inclui pratos montados | 1.40× |
| `fatsecret` | 35 | Media | 1.00× |

**A fonte `taco` deste projeto nao e a TACO crua.** Sao 228 linhas curadas que incluem
pratos montados (`Feijoada completa`, `Lasanha de carne ao forno`, `Strogonoff de carne`,
`Bife a parmegiana`, `Escondidinho de carne seca`, `Hot dog completo`, 3 pizzas, fast food).
Isso e o que permite resolver um prato composto sem decompo-lo em ingredientes.

**Risco conhecido e aceito:** as 23.398 linhas `ai_estimated` competem com a fonte curada
e, por terem nomes curtos, frequentemente vencem em `similarity` — `'banana'` casa com
uma linha `Banana` de 420 kcal/100g. Higienizar esse conjunto e trabalho de dados,
registrado como melhoria propria. Ver
`.codeflow/decisions/2026-07-26-limiares-lookup-nutricional.md` para por que exclui-las
por parametro mede pior.

**Campos por 100g:** calories, protein, carbs, fat, fiber, sodium (opcional), sugar (opcional), saturated_fat (opcional)

---

## 5. Limiares — todos medidos, nenhum por intuicao

| Parametro | Valor | Justificativa |
|---|---|---|
| `_MIN_SIMILARITY` (piso de candidato) | 0.40 | Nenhum candidato abaixo pode ser aceito: `0.65 / 1.40 = 0.464` |
| `_LOOKUP_MIN_SCORE` (aceite) | 0.65 | Melhor precisao sem perder o plato de recall |
| `_SOURCE_BOOST['taco']` | 1.40 | Boost 2.50 tem F1 melhor (0,889) mas aceita match de similaridade bruta 0,43 e produz `'ovo cozido'` → `'Chuchu cozido'` (19 kcal/100g) |

Reproduzir a medicao:

    docker compose -f docker-compose.dev.yml exec -T backend python scripts/eval_food_lookup.py

---

## Arquivos-chave

| Arquivo | Responsabilidade |
|---------|------------------|
| `services/ai/food_lookup.py` | Busca fuzzy no banco de alimentos |
| `models/food.py` | Modelo SQLAlchemy da tabela `foods` |
| `scripts/eval_food_lookup.py` | Harness de medicao de estrategias e limiares |
| `alembic/versions/20260726_d0e1f2a3b4c5_portions_e_unaccent.py` | Extensao `unaccent`, funcao `caloria_unaccent` e indice GIN de expressao |
