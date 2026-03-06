from celery import Celery

from src.config import settings

app = Celery(
    "it_guru",
    broker=settings.celery_broker_url,
    backend=settings.celery_broker_url,
    include=["src.payments.tasks"],
)
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_pool="solo",
)
