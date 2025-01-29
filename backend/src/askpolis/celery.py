import celery_typed_tasks
from celery import Celery

from askpolis.logging import configure_logging, get_logger

configure_logging()

logger = get_logger(__name__)
logger.info("Starting Celery worker...")

app = Celery("askpolis", task_cls=celery_typed_tasks.TypedTask)
app.conf.update(worker_hijack_root_logger=False)
app.conf.beat_schedule = {
    "crawl-bundestag-from-abgeordnetenwatch": {"task": "crawl_bundestag_from_abgeordnetenwatch", "schedule": 3600},
}
app.autodiscover_tasks(packages=["askpolis.crawler"])
