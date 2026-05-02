"""Celery tasks for model training."""

import logging
from typing import Any

from celery.signals import task_failure, task_revoked

from backend.api.celery_app import celery_app

logger = logging.getLogger(__name__)

MODEL_TRAINING_TASK = "backend.model_training.run"


def _job_id_from_request(request: Any) -> str | None:
    args = getattr(request, "args", None) or []
    return str(args[0]) if args else None


@celery_app.task(name=MODEL_TRAINING_TASK, bind=True)
def run_model_training(self, job_id: str):
    from backend.api.routers.model import _run_training_job, _update_job

    _update_job(job_id, celery_task_id=self.request.id)
    _run_training_job(job_id)


@task_revoked.connect
def mark_training_task_revoked(sender=None, request=None, terminated=None, signum=None, expired=None, **kwargs):
    if getattr(sender, "name", None) != MODEL_TRAINING_TASK:
        return

    job_id = _job_id_from_request(request)
    if not job_id:
        return

    from backend.api.routers.model import _finish_training_job

    reason = "Training task was revoked"
    if terminated:
        reason = f"Training task was terminated with signal {signum or 'unknown'}"
    if expired:
        reason = "Training task expired"

    logger.info("Model training task revoked: job_id=%s reason=%s", job_id, reason)
    _finish_training_job(job_id, status="stopped", error=None)


@task_failure.connect
def mark_training_task_failed(sender=None, task_id=None, exception=None, args=None, **kwargs):
    if getattr(sender, "name", None) != MODEL_TRAINING_TASK:
        return

    job_id = str(args[0]) if args else None
    if not job_id:
        return

    from backend.api.routers.model import _finish_training_job

    logger.exception("Model training task failed outside job handler: job_id=%s task_id=%s", job_id, task_id)
    _finish_training_job(job_id, status="failed", error=str(exception) if exception else "Training task failed")
