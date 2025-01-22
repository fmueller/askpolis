import logging
from typing import Any

import celery_typed_tasks
from celery import Celery
from celery.signals import worker_process_init
from opentelemetry.instrumentation.logging import LoggingInstrumentor

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.info("Starting Celery worker...")


@worker_process_init.connect(weak=False)
def init_celery_tracing(*args: Any, **kwargs: Any) -> None:
    # because the default celery instrumentor is removing all loggers
    # we need to re-enable the logging instrumentor
    logging.basicConfig(level=logging.INFO)
    LoggingInstrumentor().instrument(set_logging_format=True)


app = Celery("askpolis", task_cls=celery_typed_tasks.TypedTask)
app.conf.update(worker_hijack_root_logger=False)
app.conf.beat_schedule = {
    "crawl-bundestag-from-abgeordnetenwatch": {"task": "crawl_bundestag_from_abgeordnetenwatch", "schedule": 3600},
}
app.autodiscover_tasks(packages=["askpolis.crawler"])
