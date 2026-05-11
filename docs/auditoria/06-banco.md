# Frente F — Banco

**Plano:** ver `plano.md` § Frente F.

## Achados desta frente

- AUD-030 (🟡 média) — falta índice composto `(user_id, date)` em `meals` (e nos 3 logs diários `weight_logs`/`mood_logs`/`hydration_logs`); dashboard filtra pelas duas colunas
- AUD-031 (🟡 média) — falta índice em `notifications.read` (idealmente parcial `WHERE NOT read`); endpoint `unread-count` é polled pelo header
- AUD-032 (🟢 baixa) — `foods.name` tem 2 índices redundantes (`ix_foods_name` non-unique + `taco_foods_name_key` UNIQUE legado); UNIQUE pode bloquear seeds futuros do Open Food Facts
- AUD-033 (🟡 média) — migração `adiciona_dessert_mealtype.py` tem `downgrade()` apenas `pass` — `alembic downgrade -1` não desfaz a adição do enum value
- AUD-034 (🟢 baixa) — enum `MealSource` mantém `TELEGRAM`/`WHATSAPP` mortos no schema (não usados em código nem dados)
- AUD-035 (🟡 média) — pool sizing × processos × `max_connections=100` pode saturar em escala (estimativa 60-150 conn em pico vs 100 do Postgres); PgBouncer resolve estruturalmente
- AUD-036 (🟢 baixa) — event listener loga TODA query como `INFO` (sem gate por env) — 5-10k linhas/min em escala

(referencia também AUD-029 que cobre `ai_conversations.updated_at` — gerado na FASE 6 PASSO 6.5)

## F.1 Inventário de índices

Comando: `SELECT schemaname, tablename, indexname, indexdef FROM pg_indexes WHERE schemaname='public' ORDER BY tablename, indexname`. Artefato: `artefatos/F1-indexes.txt`.

### Resumo (35 índices não-pkey)

| Tabela | Índices presentes | Faltando (vs queries reais) |
|---|---|---|
| `ai_conversations` | `external_chat_id`, `user_id` | `updated_at` (AUD-029) |
| `foods` | `category`, `external_id`, `name`, `name UNIQUE`, `search_text gin_trgm_ops` | — (mas `name` está duplicado, AUD-032) |
| `hydration_logs` | `date`, `user_id` | `(user_id, date)` composto (AUD-030) |
| `meal_items` | `food_id`, `meal_id` | — (joins simples cobertos) |
| `meals` | `date`, `user_id` | `(user_id, date)` composto (AUD-030) |
| `mood_logs` | `date`, `user_id` | `(user_id, date)` composto (AUD-030) |
| `notifications` | `user_id` | `(user_id, read)` ou parcial `WHERE NOT read` (AUD-031) |
| `push_subscriptions` | `endpoint UNIQUE`, `user_id` | — |
| `reminders` | `user_id` | — (`active`/`time` candidatos para volume futuro; ver § E.3) |
| `user_profiles` | `user_id UNIQUE` | — |
| `users` | `email UNIQUE` | — |
| `weight_logs` | `date`, `user_id` | `(user_id, date)` composto (AUD-030) |

### Padrão observado

O modelo SQLAlchemy gera **índices separados** para cada coluna FK ou de filtro, mas **nunca compostos**. Para 4 tabelas (`meals`, `weight_logs`, `mood_logs`, `hydration_logs`) o padrão de query é o mesmo: `WHERE user_id = :u AND date OP :d`. Postgres usa o índice `user_id` e filtra por `date` no heap — funciona, mas com volume real (vários meses de logs por usuário) o filtro percorre todas as linhas do usuário a cada query do dashboard. Composto `(user_id, date)` resolve com 1 lookup direto.

### Caso especial: `notifications`

Sem índice em `read`, a query `WHERE user_id = :u AND read = false` (badge polling) puxa **todas** as notificações do usuário no heap e filtra. Para usuários com histórico longo (centenas de notificações lidas), o custo cresce linearmente. Índice **parcial** `WHERE NOT read` cobre a query exata e gasta muito menos espaço (idealmente < 5% da tabela).

### Caso especial: `foods.name` duplicado

`foods` tem **dois** índices na mesma coluna `name`:
- `ix_foods_name` — `CREATE INDEX` (não-único)
- `taco_foods_name_key` — `CREATE UNIQUE INDEX` (legado da era em que a tabela se chamava `taco_foods`)

O UNIQUE é incorreto pós-unificação TACO + Open Food Facts (OFF pode ter "Arroz branco" de marcas diferentes — duplicatas legítimas) e pode bloquear seeds futuros. O non-unique é redundante. Ver AUD-032.

### Não-achados (verificados)

- `meal_items(meal_id, food_id)` composto — sugerido no plano § F.1, mas os dois índices simples já cobrem os usos reais (`JOIN ON meal_id = m.id` é single-column; `food_id` agregado é independente). Composto não acrescenta.
- `reminders(active)` — workers fazem `WHERE active = true` por minuto, mas a tabela é pequena hoje e Postgres prefere Seq Scan corretamente. Latente para volume futuro; ataque via reescrita da query (AUD à criar quando o problema aparecer ou cobertura combinada com AUD-008).

## F.1.1 Validação por EXPLAIN ANALYZE

Comando: 5 queries representativas via `docker exec caloria_postgres psql -c "EXPLAIN ANALYZE ..."`. Artefato: `artefatos/F2-explain.txt`.

> **Caveat de timing**: o DB de dev tem `meals/meal_items/notifications/reminders/users/weight_logs` **vazias** e `foods` com 42.103 linhas (seed TACO + parcial OFF). `actual time` é trivialmente baixo nas tabelas vazias, mas o **plano** (Seq Scan vs Index Scan vs Bitmap Heap Scan + Filter) é representativo: o planner usa `pg_class.reltuples` e `pg_statistic` com estimativas independentes do volume real; o esqueleto da execução não muda com mais dados.

### Resultados

| # | Query | Plano | Confirma |
|---|---|---|---|
| Q1 | `meals m JOIN meal_items mi ON ... WHERE m.user_id=1 AND m.date=CURRENT_DATE` | `Index Scan ix_meals_user_id` + `Filter: (date=CURRENT_DATE)` + Nested Loop em `ix_meal_items_meal_id` | AUD-030 — composto `(user_id, date)` removeria o `Filter` |
| Q2 | dashboard semanal (`m.date BETWEEN ... AND m.user_id=1` + GROUP BY) | **`Index Scan ix_meals_date` + `Filter: (user_id=1)`** — planner escolheu o outro índice! | AUD-030 — composto resolve ambos os caminhos |
| Q3 | `SELECT COUNT(*) FROM notifications WHERE user_id=1 AND read=false` | `Bitmap Index Scan ix_notifications_user_id` + `Filter: (NOT read)` | AUD-031 |
| Q4 | `SELECT * FROM reminders WHERE active = true` | `Seq Scan + Filter: active` (estimativa 335 rows com tabela vazia → planner usa selectivity default) | já registrado como latente em § F.1 |
| Q5 | food lookup `WHERE search_text %>> 'arroz integral' ORDER BY similarity(...) DESC LIMIT 5` | `Bitmap Heap Scan ix_foods_search_trgm` (517 páginas, 1109 candidatos) + Top-N heapsort + Limit | **valida AUD-016** — só `%>>` (sem OR) leva 19ms; com OR + similarity, vai para 585ms |
| Q6 | `weight_logs WHERE user_id=1 ORDER BY date DESC LIMIT 30` | `Bitmap Heap Scan ix_weight_logs_user_id` + Sort em memória | AUD-030 — composto `(user_id, date DESC)` evitaria o sort |

### Insights além das tabelas

**Q2 — escolha de índice depende da seletividade.** Com `BETWEEN 7 dias` o planner julgou que filtrar por data é mais seletivo que filtrar por usuário (faz sentido com poucos usuários, inverte com muitos). Sem composto, **qualquer dos dois caminhos faz heap filter** — o composto `(user_id, date)` resolve uniforme, independentemente da escolha do planner.

**Q5 — performance hoje (já com fix do AUD-016).** A query medida usa apenas `%>>` (sem o OR `similarity() >= 0.18` que AUD-016 sinaliza como vilão). Mesmo assim, retorna **1166 candidatos brutos** que são ordenados em Top-N heapsort de 5 — custo dominado por 517 page reads + sort. Otimização adicional (fora deste passo): usar operador KNN `ORDER BY search_text <-> 'q' LIMIT N` que aproveita o GIN para retorno ordenado direto, evitando o sort em memória. Ganho estimado: 5-10ms → 1-2ms por chamada. Combinar com batch (AUD-006) chegaria a ~10ms para uma refeição inteira.

**Q4 — Seq Scan é uma escolha correta hoje** (tabela 0 rows, mesmo com selectivity default de 335 rows estimadas o Seq Scan sai ~16). O risco está no acoplamento futuro: a query do worker (`SELECT * FROM reminders WHERE active = true`) puxa todos os ativos por minuto e filtra hora/minuto em Python. Para 1.000 lembretes ativos isso é 1000 rows/minuto trafegando do DB para a app. Reescrever a query para `WHERE active AND time = make_time(:h, :m, 0)` permitiria índice composto `(active, time)` — fora de escopo desta auditoria, mas anotado.

## F.2 Migrações Alembic — reversibilidade

Comando: extração do corpo de `def downgrade()` em cada `backend/alembic/versions/*.py` via Python regex. Artefato: `artefatos/F3-downgrade.txt`.

### Estado das 10 migrações

| # | Arquivo | LOC downgrade | Reversível |
|---|---|---|---|
| 1 | `20260224_..._schema_inicial.py` | 24 | ✅ drop completo das tabelas/índices |
| 2 | `20260305_a1b2c3d4e5f6_novos_campos_e_categorias.py` | 3 | ✅ drop colunas + DROP TYPE goaltype |
| 3 | `20260305_b2c3d4e5f6a1_corrige_case_enums.py` | 4 | ✅ rename de volta dos enum values |
| 4 | `20260305_d4e5f6a1b2c3_taco_foods.py` | 3 | ✅ drop indexes + table |
| 5 | **`20260306_e5f6a1b2c3d4_adiciona_dessert_mealtype.py`** | 1 (`pass`) | ❌ **AUD-033** |
| 6 | `20260309_f1a2b3c4d5e6_taco_pgtrgm_source.py` | 5 | ✅ drop colunas + index |
| 7 | `20260315_a1b2c3d4e5f6_web_push_notifications.py` | 25 | ✅ drop 2 tables + types + cols |
| 8 | `20260318_c4d5e6f7a8b9_foods_refactor.py` | 8 | ✅ drop cols + rename indexes/table |
| 9 | `20260318_d5e6f7a8b9c0_meal_items_food_ref.py` | 7 | ✅ drop cols + FK |
| 10 | `20260320_e6f7a8b9c0d1_fix_search_text_taco.py` | 11 | ⚠️ partial revert documentado |

### Outras verificações (do plano)

- **`pg_trgm` extension:** `CREATE EXTENSION IF NOT EXISTS pg_trgm` em `20260309_f1a2b3c4d5e6_taco_pgtrgm_source.py:20`. ✅ presente.
- **Enum `MealSource`:** ainda tem `TELEGRAM`/`WHATSAPP` no model E no DB (`pg_enum`). Nenhum uso em código. **AUD-034**.
- **Enum `MealType`:** valor `dessert` adicionado em #5; outros valores stable.

### Dead schema vs limitação técnica

A justificativa do `pass` em #5 ("PostgreSQL não permite remover valores de enum sem recriar o tipo") é **parcialmente verdadeira** — recriar o tipo é a solução documentada e funciona. O AUD-033 propõe o padrão correto. AUD-034 (limpeza do `MealSource`) usa o mesmo padrão e serve como teste do esforço necessário.

## F.3 Pool sizing e conexões

Comando: `cat backend/app/core/database.py` (`pool_size=10, max_overflow=20, pool_pre_ping=True`) + `grep --workers backend/Dockerfile` (`--workers 2`) + `psql -c "SHOW max_connections"` (`100`) + leitura de `docker-compose.yml`.

### Estado atual

| Parâmetro | Valor | Fonte |
|---|---|---|
| `pool_size` | 10 | `database.py:21` |
| `max_overflow` | 20 | `database.py:22` |
| `pool_pre_ping` | True | `database.py:20` |
| `expire_on_commit` | False | `database.py:60` (correto para async) |
| Uvicorn workers (prod) | 2 | `backend/Dockerfile:55` |
| Uvicorn workers (dev) | 1 | `docker-compose.dev.yml:59` (`--reload`) |
| Celery workers | 1 master + N children | `docker-compose.yml` |
| Celery beat | 1 process | `docker-compose.yml` |
| Postgres `max_connections` | 100 | `SHOW max_connections` |
| Postgres `shared_buffers` | 128 MB | `SHOW shared_buffers` (default) |

### Aritmética de saturação

Cada processo Python carrega `app.core.database` ao importar, criando seu próprio `engine` e portanto seu próprio pool (até 30 conn — 10 size + 20 overflow).

| Cenário | uvicorn | celery worker | celery beat | Total |
|---|---|---|---|---|
| Atual mínimo | 2×30=60 | 1×30=30 | 1×30=30 | **120** |
| Celery com `concurrency=4` | 60 | 4×30=120 | 30 | **210** |
| Cenário escala (4 uvicorn) | 4×30=120 | 4×30=120 | 30 | **270** |

Postgres `max_connections=100` — **qualquer cenário acima passa do teto**. Hoje não acontece (1 usuário, baixíssima carga), mas é arquitetural: aumentar workers vai estourar.

Mitigação padrão da indústria: **PgBouncer** entre app e DB. Multiplexa N conn de app em M < N conn reais de DB (modo `transaction`). Permite manter pool generoso por processo sem estourar o DB. Ver AUD-035.

### Logging de cada query

`event.listens_for(engine.sync_engine, "after_cursor_execute")` chama `db_logger.info(f"[DB] {ms:7.1f}ms | {first_line}{flag}")` **em cada query** (linhas 39-52). Sem gate de env. Quick win: trocar `info` por `debug` e manter `warning` quando `ms > 100`. Ver AUD-036.

### Não-achados (verificados)

- **`pool_pre_ping=True`** — bom (valida conn antes de usar, evita "stale connection"); overhead trivial.
- **`expire_on_commit=False`** — correto para `AsyncSession` (refresh explícito necessário, padrão FastAPI).
- **Auditoria do plano § F.4 ("todos services seguem padrão `await db.refresh()`")** — não foi tema deste passo; ficaria como item separado se quiser cobertura completa (não criado como achado por ora — sem evidência de bug funcional).

## Notas e contexto

(seção F.5 será preenchida no PASSO 7.5)
