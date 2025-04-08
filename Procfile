web: python manage.py runserver
worker: celery -A skillsverse_backend worker --loglevel=info --logfile=logs/celery.log
beat: celery -A skillsverse_backend beat --scheduler django_celery_beat.schedulers:DatabaseScheduler --loglevel=info --logfile=logs/celery_beat.log
