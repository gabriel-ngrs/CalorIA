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

## Notas e contexto

(seções F.2-F.5 serão preenchidas nos PASSOS 7.2-7.5)
