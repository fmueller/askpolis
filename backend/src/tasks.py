import celery_typed_tasks
from celery import Celery

app = Celery('tasks', task_cls=celery_typed_tasks.TypedTask)
app.conf.beat_schedule = {
    'print-add-every-2-seconds': {
        'task': 'tasks.print_add',
        'schedule': 2.0,
        'args': (4, 6)
    },
}


@app.task
def add(x: int, y: int) -> int:
    return x + y


@app.task
def print_add(x: int, y: int) -> None:
    print(add(x, y))
