# Frente A — Arquitetura

**Plano:** ver `plano.md` § Frente A.

## Achados desta frente

- AUD-001 (🟡 média) — `backend/app/api/v1/push.py` faz queries SQL diretamente no router (sem camada de service)

## A.1 Separação de camadas

Comando: `rg -n "(select|insert|update|delete)\(" backend/app/api/v1/`. Artefato: `artefatos/A1-queries-em-routers.txt`.

Após filtrar falsos positivos (`@router.delete(...)` é decorator HTTP, não SQL; `ReminderService(...).delete(...)` é método de service), restam **6 violações reais**, todas em `backend/app/api/v1/push.py`:

| Endpoint | Linha | Operação SQL inline |
|---|---|---|
| `POST /push/subscribe` | 80–101 | `select(PushSubscription)` + upsert manual + `db.commit()` |
| `DELETE /push/unsubscribe` | 112–118 | `delete(PushSubscription).where(...)` + `db.commit()` |
| `GET /notifications` | 134–139 | `select(Notification)...order_by().limit()` |
| `GET /notifications/unread-count` | 151–157 | `select(func.count(...))` |
| `PATCH /notifications/{id}/read` | 170–184 | `select` + mutação + `db.commit()` + `db.refresh()` |
| `POST /notifications/read-all` | 195–199 | `update(Notification)...values(read=True)` |

Demais routers (`meals.py`, `reminders.py`, etc.) delegam para services — `push.py` é o único outlier.

## A.2 Filtragem por user_id

Comando: ver `artefatos/A2-user-id-coverage.txt` (508 linhas brutas) + análise endpoint-a-endpoint via script Python (`re.finditer` para extrair blocos de cada `@router.*`).

**Endpoints (47 totais)**

Apenas 4 não usam `Depends(get_current_user_id)` — todos públicos por design:

| Endpoint | Justificativa |
|---|---|
| `POST /auth/register` | Cria usuário; ainda não existe sessão |
| `POST /auth/login` | Autentica por email/senha |
| `POST /auth/refresh` | Usa refresh token, não JWT |
| `GET /push/vapid-public-key` | Chave pública para clientes; sem dado pessoal |

Os outros 43 endpoints injetam `user_id` e o aplicam em queries/services. Nenhum suspeito.

**Queries em services / workers (sem `user_id` direto)**

| Query | Local | Filtra por user_id? | Justificativa |
|---|---|---|---|
| `select(Meal).where(Meal.id == meal.id)` | `meal_service.py:67` | ❌ direto, ✅ indireto | Refresh após `create_meal()`; `meal` recém-criado é do usuário; só re-hidrata com `selectinload(items)` |
| `select(User)` (lookup) | `user_service.py:19/26/58` | N/A | Próprio `User`; lookup de auth (id/email) |
| `select(UserProfile).where(...)` | `profile_service.py:17` | ✅ | filtra `user_id` |
| `select(User).where(User.is_active.is_(True))` | `workers/.../*.py` | N/A | Tarefa batch/scheduler, itera todos os usuários ativos por design; queries-filhas usam `user.id` da iteração |
| `select(PushSubscription).where(user_id==user.id)` | `workers/tasks/reminders.py`, `reports.py` | ✅ | escopo por usuário iterado |
| `select(WeightLog).where(user_id==user.id)` | `workers/tasks/maintenance.py:88` | ✅ | escopo por usuário iterado |

Todas as queries de `log_service.py`, `meal_service.py` (exceto refresh acima), `reminder_service.py`, `pattern_analyzer.py` e `context_builder.py` filtram explicitamente por `user_id`. Nenhuma violação encontrada.

## A.3 Cascades e ForeignKeys

Comando: `rg -n "relationship\(|ForeignKey\(" backend/app/models/`. Artefato: `artefatos/A3-relacionamentos.txt`.

| Pai → Filho | FK `ondelete=` | ORM `cascade=` | Coerência |
|---|---|---|---|
| User → UserProfile | `CASCADE` | `all, delete-orphan` (uselist=False) | ✅ posse |
| User → Meal | `CASCADE` | `all, delete-orphan` | ✅ posse |
| User → WeightLog | `CASCADE` | `all, delete-orphan` | ✅ posse |
| User → HydrationLog | `CASCADE` | `all, delete-orphan` | ✅ posse |
| User → MoodLog | `CASCADE` | `all, delete-orphan` | ✅ posse |
| User → Reminder | `CASCADE` | `all, delete-orphan` | ✅ posse |
| User → AIConversation | `CASCADE` | `all, delete-orphan` | ✅ posse |
| User → PushSubscription | `CASCADE` | `all, delete-orphan` | ✅ posse |
| User → Notification | `CASCADE` | `all, delete-orphan` | ✅ posse |
| Meal → MealItem | `CASCADE` | `all, delete-orphan` | ✅ posse (item é parte da refeição) |
| MealItem → Food | `SET NULL` (`nullable=True`) | (sem ORM relationship) | ✅ referencial — apaga `Food` mantém histórico do `MealItem` como snapshot |

Observações:
- Padrão consistente em **todos** os relacionamentos: ORM `cascade` + DB `ondelete` espelhados, evitando órfãos no DB caso alguém apague via SQL puro.
- `MealItem.food_id` referencia `foods.id` mas **não** define `relationship("Food", ...)` — intencional (o `MealItem` carrega snapshot denormalizado de `food_name`/`calories`/`protein`/etc., para preservar o registro mesmo se o `Food` for removido).
- `UserProfile.user_id` tem `unique=True` (1:1).

Nenhum achado.

## Notas e contexto

(texto livre conforme aprendizagens surgem)
