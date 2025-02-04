import celery_typed_tasks
from celery import Celery

from askpolis.logging import configure_logging, get_logger

configure_logging()

logger = get_logger(__name__)
logger.info("Starting Celery worker...")

app = Celery("askpolis", task_cls=celery_typed_tasks.TypedTask)
app.conf.update(worker_hijack_root_logger=False)
app.conf.beat_schedule = {
    "fetch-data/bundestag-from-abgeordnetenwatch": {"task": "fetch_bundestag_from_abgeordnetenwatch", "schedule": 3600},
    "cleanup/outdated-data-of-data-fetchers": {"task": "cleanup_outdated_data", "schedule": 1800},
}
app.autodiscover_tasks(packages=["askpolis.data_fetcher"])
