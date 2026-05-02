"""Celery application for backend background jobs."""

import os

from celery import Celery


def _redis_url(default_db: int = 0) -> str:
    redis_url = os.getenv("CELERY_BROKER_URL") or os.getenv("REDIS_URL")
    return redis_url or f"redis://localhost:6379/{default_db}"


celery_app = Celery(
    "ml_automation",
    broker=_redis_url(0),
    backend=os.getenv("CELERY_RESULT_BACKEND") or _redis_url(0),
)

celery_app.conf.update(
    broker_connection_retry_on_startup=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
)
