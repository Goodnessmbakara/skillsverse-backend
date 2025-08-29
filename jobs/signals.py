from django_celery_beat.models import PeriodicTask, IntervalSchedule
from django.db import OperationalError
import json

def setup_job_fetch_task():
    try:
        schedule, _ = IntervalSchedule.objects.get_or_create(
            every=30,  # Every 30 minutes
            period=IntervalSchedule.MINUTES,
        )

        PeriodicTask.objects.get_or_create(
            interval=schedule,
            name='Fetch jobs from external APIs',
            task='jobs.tasks.fetch_jobs_task',
            defaults={'args': json.dumps([])},
        )
    except OperationalError:
        # Database tables don't exist yet, skip setup
        pass
