from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "skillsverse_backend.settings")

app = Celery("skillsverse_backend")

# Load task modules from all registered Django app configs
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in each app
app.autodiscover_tasks()
