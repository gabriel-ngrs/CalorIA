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

## Notas e contexto

(texto livre conforme aprendizagens surgem)
