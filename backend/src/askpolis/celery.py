import celery_typed_tasks
from celery import Celery

app = Celery("askpolis", task_cls=celery_typed_tasks.TypedTask)
app.conf.beat_schedule = {
    "crawl-abgeordnetenwatch": {"task": "crawl_bundestag_election_programs_from_abgeordnetenwatch", "schedule": 3600},
}
app.autodiscover_tasks(packages=["askpolis.crawler"])
