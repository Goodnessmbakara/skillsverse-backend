import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "skillsverse_backend.settings")
app = Celery("skillsverse_backend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'fetch-jobs-every-hour': {
        'task': 'jobs.tasks.fetch_jobs_task',
        'schedule': crontab(minute=0, hour='*/1'),  # Every hour
    },
}

