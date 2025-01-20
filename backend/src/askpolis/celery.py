import celery_typed_tasks
from celery import Celery

app = Celery("askpolis", task_cls=celery_typed_tasks.TypedTask)
app.conf.beat_schedule = {
    "crawl-bundestag-from-abgeordnetenwatch": {"task": "crawl_bundestag_from_abgeordnetenwatch", "schedule": 3600},
}
app.autodiscover_tasks(packages=["askpolis.crawler"])
