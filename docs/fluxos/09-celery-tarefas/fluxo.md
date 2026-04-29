# Fluxo de Celery — Tarefas em Background

## Visao Geral

O Celery processa tarefas assincronas e agendadas. Usa Redis como broker e backend. Timezone: America/Sao_Paulo.

---

## 1. Configuracao

- **Broker:** Redis
- **Backend:** Redis
- **Serializer:** JSON
- **Max retries:** 3
- **Prefetch multiplier:** 1 (1 task por vez por worker)

---

## 2. Schedule Completo

| Task | Frequencia | Horario | Descricao |
|------|-----------|---------|-----------|
| `dispatch_due_reminders` | A cada 60s | Continuo | Verifica e dispara lembretes devidos |
| `send_daily_summaries` | Diario | 22:00 | Gera insight diario via IA + push |
| `send_weekly_reports` | Semanal | Domingo 20:00 | Gera relatorio semanal via IA + push |
| `send_hydration_reminders` | 7×/dia | 8h, 10h, 12h, 14h, 16h, 18h, 20h | Lembrete de agua se abaixo da meta |
| `cleanup_old_conversations` | Diario | 03:00 | Remove historico de IA > 90 dias |
| `recalculate_tdee` | Mensal | 1o do mes, 04:00 | Recalcula TDEE baseado no peso recente |

---

## 3. Resumo Diario (22h)

1. Celery Beat dispara `send_daily_summaries`
2. Busca todos os usuarios ativos
3. Para cada usuario:
   - Cria `InsightsGenerator`
   - Chama `daily_insight(user_id, today)` → Gemini gera feedback
   - Cria `Notification` no banco
   - Envia web push para todas as subscriptions
   - Deleta subscriptions expiradas

---

## 4. Relatorio Semanal (Domingo 20h)

Mesmo fluxo que o resumo diario, mas:
- Usa `weekly_insight()` em vez de `daily_insight()`
- Gera analise semanal com consistencia e tendencias

---

## 5. Lembrete de Hidratacao

Dispara 7 vezes por dia (8h-20h, horas pares):

1. Busca usuarios ativos
2. Para cada usuario: busca consumo de agua do dia
3. Se nao atingiu meta: cria notificacao + web push
4. Se atingiu: pula

---

## 6. Limpeza de Conversas (03h)

1. Busca registros em `ai_conversations` com mais de 90 dias
2. Deleta registros antigos
3. Loga quantidade removida

---

## 7. Recalculo de TDEE (1o do mes, 04h)

1. Busca usuarios ativos com perfil
2. Para cada: busca peso mais recente
3. Calcula BMR (Mifflin-St Jeor) × fator de atividade
4. Atualiza `profiles.tdee_calculated`

---

## Arquivos-chave

| Arquivo | Responsabilidade |
|---------|------------------|
| `workers/celery_app.py` | Configuracao do Celery e beat schedule |
| `workers/tasks/reminders.py` | `dispatch_due_reminders` |
| `workers/tasks/reports.py` | `send_daily_summaries`, `send_weekly_reports` |
| `workers/tasks/maintenance.py` | `cleanup_old_conversations`, `recalculate_tdee` |
| `workers/tasks/hydration.py` | `send_hydration_reminders` |
