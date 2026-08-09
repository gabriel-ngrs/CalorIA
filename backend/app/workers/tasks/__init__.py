"""Tarefas Celery.

Importar `celery_app` aqui garante que o app **configurado** seja o current do
processo antes de qualquer task ser referenciada.

As tasks são declaradas com `@shared_task`, que só se liga ao app configurado se
esse app já for o default do processo. O processo da API (`uvicorn app.main:app`)
nunca importava `app.workers.celery_app` — importava apenas a task, por
`app.api.v1.auth` — então o `.delay()` do "esqueci minha senha" caía num app
Celery default sem broker e levantava exceção, devolvendo HTTP 500.
"""

from app.workers.celery_app import celery_app

__all__ = ["celery_app"]
