# Fluxo de Lembretes e Notificacoes

## Visao Geral

O sistema de lembretes permite ao usuario configurar notificacoes recorrentes (refeicao, agua, peso, etc.). As notificacoes sao entregues via Web Push e armazenadas como notificacoes in-app.

---

## 1. Criacao de Lembrete

**Via Dashboard:**
1. Usuario configura lembrete na UI
2. Frontend chama `POST /api/v1/reminders` com tipo, horario, dias da semana, canal
3. Backend insere em `reminders`

**Via batch:**
- `POST /api/v1/reminders/batch` aceita lista de lembretes

---

## 2. Disparo de Lembretes (Celery Beat)

A cada 60 segundos, `dispatch_due_reminders` executa:

1. Busca todos os lembretes ativos de usuarios ativos
2. Para cada lembrete, verifica:
   - `hora == agora.hora`?
   - `minuto == agora.minuto`?
   - `dia_semana_atual in dias_configurados`?
3. Se match:
   - Cria `Notification` no banco (in-app)
   - Busca todas as `PushSubscription` do usuario
   - Para cada subscription: envia web push via `pywebpush`
   - Se subscription retorna 410 Gone: marca para delecao

---

## 3. Web Push — Inscricao

1. Frontend verifica suporte (`serviceWorker` + `PushManager`)
2. Registra Service Worker (`/sw.js`)
3. Usuario clica "Ativar notificacoes"
4. Browser pede permissao: `Notification.requestPermission()`
5. Frontend busca chave VAPID: `GET /api/v1/push/vapid-public-key`
6. Inscreve no push manager: `pushManager.subscribe({applicationServerKey})`
7. Extrai `endpoint`, `p256dh`, `auth`
8. Envia para backend: `POST /api/v1/push/subscribe`
9. Backend armazena em `push_subscriptions`

---

## 4. Web Push — Recebimento

1. Backend (Celery) chama `pywebpush.send()` com endpoint e payload
2. Push service entrega ao browser
3. Service Worker recebe evento `push`
4. Exibe notificacao nativa
5. Usuario clica → evento `notificationclick` → abre `/dashboard`

---

## 5. Notificacoes In-App

Fontes de notificacao:
- Lembretes configurados
- Resumo diario (22h)
- Relatorio semanal (domingo 20h)
- Lembrete de hidratacao

Endpoints:
- `GET /api/v1/notifications` — listar
- `GET /api/v1/notifications/unread-count` — contagem
- `PATCH /api/v1/notifications/{id}/read` — marcar como lida
- `POST /api/v1/notifications/read-all` — marcar todas como lidas

---

## 6. Tipos de Lembrete

| Tipo | Descricao | Exemplo |
|------|-----------|---------|
| `breakfast` | Cafe da manha | 07:30 |
| `lunch` | Almoco | 12:00 |
| `dinner` | Jantar | 19:00 |
| `snack` | Lanche | 15:00 |
| `water` | Hidratacao | A cada 2h |
| `weight` | Pesar | 08:00 (seg/qua/sex) |
| `custom` | Personalizado | Qualquer horario |

---

## Arquivos-chave

| Arquivo | Responsabilidade |
|---------|------------------|
| `services/reminder_service.py` | CRUD de lembretes |
| `workers/tasks/reminders.py` | Task `dispatch_due_reminders` |
| `services/push_service.py` | Envio de web push (pywebpush) |
| `api/v1/reminders.py` | Endpoints de lembretes |
| `api/v1/push.py` | Endpoints VAPID e subscription |
| `models/reminder.py` | Modelo Reminder |
| `models/push_subscription.py` | Modelo PushSubscription |
| `models/notification.py` | Modelo Notification |
| `frontend/lib/hooks/usePushNotifications.ts` | Hook de inscricao push |
| `frontend/public/sw.js` | Service Worker |
