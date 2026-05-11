# Frente F — Banco

**Plano:** ver `plano.md` § Frente F.

## Achados desta frente

- AUD-030 (🟡 média) — falta índice composto `(user_id, date)` em `meals` (e nos 3 logs diários `weight_logs`/`mood_logs`/`hydration_logs`); dashboard filtra pelas duas colunas
- AUD-031 (🟡 média) — falta índice em `notifications.read` (idealmente parcial `WHERE NOT read`); endpoint `unread-count` é polled pelo header
- AUD-032 (🟢 baixa) — `foods.name` tem 2 índices redundantes (`ix_foods_name` non-unique + `taco_foods_name_key` UNIQUE legado); UNIQUE pode bloquear seeds futuros do Open Food Facts

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

## Notas e contexto

(seções F.2-F.5 serão preenchidas nos PASSOS 7.3-7.5)
