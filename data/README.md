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

Os dois arquivos grandes (8,7 MB somados) **não são versionados** — eles são
publicados como asset da [release `v0.7.0`][release]. Baixe-os antes de restaurar
o banco:

```bash
gh release download v0.7.0 -p dump_alimentos.dump -D data/db
gh release download v0.7.0 -p alimentos_final.csv -D data/processed
```

[release]: https://github.com/gabriel-ngrs/CalorIA/releases/tag/v0.7.0

### raw/
| Arquivo | Descrição | Versionado |
|---|---|---|
| `Alimentos Brasileiros com Dados da TBCA.csv` | Base TACO/TBCA com alimentos brasileiros e nutrientes reais | sim |

### processed/
| Arquivo | Descrição | Versionado |
|---|---|---|
| `alimentos_final.csv` | **42.103 linhas** — resultado final do pipeline, prontas para importar | não (asset da release) |
| `alimentos_pendentes.csv` | 546 alimentos sem nutrientes — para enriquecer futuramente | sim |

### db/
| Arquivo | Descrição | Versionado |
|---|---|---|
| `dump_alimentos.dump` | pg_dump da tabela `foods` com as 42.103 linhas | não (asset da release) |

## Como restaurar o banco em produção

```bash
# Copia o dump para o container (baixe-o da release antes, ver acima)
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

Contagem por `source` em `alimentos_final.csv` (as mesmas linhas do dump):

| Fonte | Registros | Nutrientes | Descrição |
|---|---|---|---|
| Open Food Facts | 18.195 | medidos | Produtos com nutrientes reais (internacionais e brasileiros) |
| AI estimado (Groq) | 23.398 | estimados | Estimativa da IA para alimentos sem dados na fonte |
| USDA FoodData | 247 | medidos | Base americana de alimentos básicos |
| TACO | 228 | medidos | Tabela brasileira de composição de alimentos |
| FatSecret | 35 | medidos | Complemento de produtos |
| **Total** | **42.103** | | |

### Por que a documentação fala em ~19.500 e aqui em 42.103

A tabela acima é a única contagem medida — ela vem de um `Counter` sobre a coluna
`source` deste CSV. Dela saem os dois números que importam:

- **42.103** linhas importadas para a tabela `foods`, no total.
- **18.705** delas têm **nutrientes medidos na fonte** (18.195 Open Food Facts +
  247 USDA + 228 TACO + 35 FatSecret). As outras **23.398** carregam estimativa da
  IA, marcada como `ai_estimated`.

O `CLAUDE.md` e o `docs/architecture.md` descrevem a tabela como "TACO (~307) +
Open Food Facts (~19.500 alimentos)". **Esses dois números não conferem com a
medição** e são arredondamento antigo, anterior a esta contagem: o Open Food Facts
isolado tem 18.195 linhas (~1.300 a menos que os "~19.500") e a TACO tem 228
(~79 a menos que os "~307"). A frase também não menciona USDA, FatSecret nem o
estrato `ai_estimated`, que é o maior de todos.

Em caso de dúvida, vale esta página: ela é a que se mede contra o arquivo.

A distinção não é cosmética: o lookup nutricional **exclui as 23.398 linhas
`ai_estimated`**, e foi essa exclusão que derrubou o erro calórico médio de 16,7%
para 4,1% — ver a seção de decisões técnicas do `README.md` e a
[decision de 2026-07-26](../.codeflow/decisions/2026-07-26-limiares-lookup-nutricional.md).
