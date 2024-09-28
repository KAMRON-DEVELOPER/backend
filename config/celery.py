import os
from celery import Celery


# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# create a new celery app instance and run with 'celery -A config worker -l INFO'
# uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --reload
app = Celery("config")

# load the Celery configuration from Django settings
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
