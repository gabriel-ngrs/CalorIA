from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "caloria",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.workers.tasks.reminders",
        "app.workers.tasks.reports",
        "app.workers.tasks.maintenance",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # Tentativas e backoff
    task_max_retries=3,
    task_default_retry_delay=60,
)

# ─── Celery Beat — tarefas periódicas ─────────────────────────────────────────

celery_app.conf.beat_schedule = {
    # Verificar lembretes a cada minuto
    "check-reminders": {
        "task": "app.workers.tasks.reminders.dispatch_due_reminders",
        "schedule": 60.0,  # a cada 60 segundos
    },
    # Resumo diário às 22h
    "daily-summary-22h": {
        "task": "app.workers.tasks.reports.send_daily_summaries",
        "schedule": crontab(hour=22, minute=0),
    },
    # Relatório semanal — domingo às 20h
    "weekly-report-sunday": {
        "task": "app.workers.tasks.reports.send_weekly_reports",
        "schedule": crontab(hour=20, minute=0, day_of_week=0),  # 0 = domingo
    },
    # Lembrete de hidratação — a cada 2 horas entre 8h e 20h
    "hydration-reminder": {
        "task": "app.workers.tasks.reminders.send_hydration_reminders",
        "schedule": crontab(hour="8,10,12,14,16,18,20", minute=0),
    },
    # Limpeza de conversas antigas — todo dia às 3h
    "cleanup-conversations": {
        "task": "app.workers.tasks.maintenance.cleanup_old_conversations",
        "schedule": crontab(hour=3, minute=0),
    },
}
