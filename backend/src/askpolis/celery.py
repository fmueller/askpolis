import celery_typed_tasks
from celery import Celery

from askpolis.logging import get_logger

logger = get_logger(__name__)
logger.info("Starting Celery worker...")

app = Celery("askpolis", task_cls=celery_typed_tasks.TypedTask)
app.conf.update(worker_hijack_root_logger=False)

app.conf.beat_schedule = {
    "fetch-data/bundestag-from-abgeordnetenwatch": {"task": "fetch_bundestag_from_abgeordnetenwatch", "schedule": 3600},
    "cleanup/outdated-data-of-data-fetchers": {"task": "cleanup_outdated_data", "schedule": 1800},
    "transform-data/core-data-models": {"task": "transform_fetched_data_to_core_models", "schedule": 1800},
    "transform-data/read-parse-election-programs": {
        "task": "read_and_parse_election_programs_to_documents",
        "schedule": 1800,
    },
    "qa/answer_stale_questions_task": {"task": "answer_stale_questions_task", "schedule": 1800},
}

app.autodiscover_tasks(packages=["askpolis.core", "askpolis.data_fetcher", "askpolis.qa", "askpolis.search"])
