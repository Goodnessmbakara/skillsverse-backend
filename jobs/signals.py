from django_celery_beat.models import PeriodicTask, IntervalSchedule
import json

def setup_job_fetch_task():
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
