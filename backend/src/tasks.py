from celery import Celery

app = Celery('tasks')
app.conf.beat_schedule = {
    'print-add-every-2-seconds': {
        'task': 'tasks.print_add',
        'schedule': 2.0,
        'args': (4, 6)
    },
}


@app.task
def add(x, y):
    return x + y


@app.task
def print_add(x, y):
    print(add(x, y))
