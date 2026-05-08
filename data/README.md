# data/

Dados do banco nutricional do CalorIA.

## Estrutura

```
data/
├── raw/          Arquivos brutos, fonte original (arquivos grandes não versionados)
├── interim/      Extrações e exportações antes da normalização
├── processed/    Dados limpos e prontos para importar
└── db/           Dumps PostgreSQL para restaurar em produção
```

## Arquivos principais

| Arquivo | Descrição |
|---|---|
| `processed/foods_master.csv` | 48.544 alimentos unificados (OFF + TACO + USDA + FatSecret + brasileiros brutos) |
| `db/foods_dump.dump` | pg_dump da tabela foods (20.641 alimentos com nutrientes completos) |
| `interim/off_brazil_raw.csv` | 32.438 produtos brasileiros extraídos do OFF sem filtro de qualidade |
| `interim/foods_unified.csv` | Export direto do banco antes da normalização |
| `raw/openfoodfacts-products.jsonl.gz` | Dump completo do OFF (~12GB) — **não versionado** |

## Como restaurar o banco em produção

```bash
# Copia o dump para o container
docker cp data/db/foods_dump.dump caloria_postgres:/tmp/

# Restaura
docker exec caloria_postgres pg_restore -U caloria -d caloria_db \
  --data-only --table=foods /tmp/foods_dump.dump

# Corrige a sequência de IDs
docker exec caloria_postgres psql -U caloria -d caloria_db \
  -c "SELECT setval(pg_get_serial_sequence('foods', 'id'), MAX(id)) FROM foods;"
```

## Como regenerar o foods_master.csv

```bash
# 1. Extrair brasileiros do dump OFF (precisa do arquivo raw de 12GB)
cd backend
python scripts/extract_off_brazil.py \
  --file ../data/raw/openfoodfacts-products.jsonl.gz \
  --output ../data/interim/off_brazil_raw.csv

# 2. Exportar banco atual
docker exec caloria_postgres psql -U caloria -d caloria_db \
  -c "\COPY foods TO '/tmp/foods.csv' WITH CSV HEADER"

# 3. Mesclar (ver scripts/normalize_foods.py após Fase 1)
```
