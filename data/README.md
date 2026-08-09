# data/

Dados do banco nutricional do CalorIA.

## Estrutura

```
data/
├── raw/          Fontes originais
├── processed/    Dados prontos para uso
└── db/           Dumps PostgreSQL para restaurar em produção
```

## Arquivos

### raw/
| Arquivo | Descrição |
|---|---|
| `Alimentos Brasileiros com Dados da TBCA.csv` | Base TACO/TBCA com alimentos brasileiros e nutrientes reais |

### processed/
| Arquivo | Descrição |
|---|---|
| `alimentos_final.csv` | **42.103 alimentos** — resultado final do pipeline, prontos para importar |
| `alimentos_pendentes.csv` | 546 alimentos sem nutrientes — para enriquecer futuramente |

### db/
| Arquivo | Descrição |
|---|---|
| `dump_alimentos.dump` | pg_dump da tabela `foods` com 42.103 alimentos |

## Como restaurar o banco em produção

```bash
# Copia o dump para o container
docker cp data/db/dump_alimentos.dump caloria_postgres:/tmp/

# Limpa a tabela e restaura
docker exec caloria_postgres psql -U caloria -d caloria_db -c "TRUNCATE TABLE foods RESTART IDENTITY CASCADE;"
docker exec caloria_postgres pg_restore -U caloria -d caloria_db \
  --data-only --table=foods /tmp/dump_alimentos.dump

# Corrige a sequência de IDs
docker exec caloria_postgres psql -U caloria -d caloria_db \
  -c "SELECT setval(pg_get_serial_sequence('foods', 'id'), MAX(id)) FROM foods;"
```

## Como regenerar o pipeline do zero

Requer o dump OFF (~12GB) baixado em `raw/openfoodfacts-products.jsonl.gz`.

```bash
cd backend

# Fase 0 — extrair produtos brasileiros do OFF
python scripts/extract_off_brazil.py \
  --file ../data/raw/openfoodfacts-products.jsonl.gz \
  --output ../data/interim/off_brasil_bruto.csv

# Fase 1 — normalizar e separar completos/incompletos
python scripts/normalize_foods.py

# Fase 2 — traduzir nomes para português
python scripts/translate_foods.py

# Fase 3 — estimar nutrientes via IA (Groq)
python scripts/enrich_foods.py
python scripts/enrich_foods.py --resume  # retoma se interrompido
```

## Origem dos dados

| Fonte | Registros | Descrição |
|---|---|---|
| Open Food Facts | ~19k | Produtos com nutrientes reais (internacionais e brasileiros) |
| AI estimado (Groq) | ~23k | Nutrientes estimados por Llama 3 para alimentos sem dados |
| USDA FoodData | 247 | Base americana de alimentos básicos |
| TACO | 228 | Tabela brasileira de composição de alimentos |
| FatSecret | 35 | Complemento de produtos |
