import logging
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from celery import shared_task
from walrus import Database

from user.models import UserProfile
from job.models import JobListing
from matching.engine import matching_engine
from job.fetcher import job_fetcher

logger = logging.getLogger(__name__)

# Initialize Redis with Walrus for distributed locks
db = Database(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD,
    db=0,
)


@shared_task
def refresh_job_listings():
    """Fetch new jobs from all sources and update database"""
    # Use a distributed lock to prevent concurrent execution
    with db.lock("refresh_job_listings", 3600):
        logger.info("Starting job refresh task")

        # Fetch new jobs from all sources
        try:
            new_job_ids = job_fetcher.fetch_all_jobs()
            logger.info(f"Found {len(new_job_ids)} new jobs")
            return len(new_job_ids)
        except Exception as e:
            logger.error(f"Error in job refresh task: {str(e)}")
            raise


@shared_task
def update_all_embeddings():
    """Rebuild all embeddings for jobs and profiles"""
    with db.lock("update_embeddings", 7200):
        logger.info("Starting embedding update task")

        try:
            matching_engine.rebuild_all_embeddings()
            logger.info("Successfully updated all embeddings")
            return True
        except Exception as e:
            logger.error(f"Error updating embeddings: {str(e)}")
            raise


@shared_task
def match_all_users():
    """Match all users to jobs and cache results"""
    with db.lock("match_all_users", 3600):
        logger.info("Starting batch matching for all users")

        try:
            # Process all user profiles
            processed = 0
            for profile in UserProfile.objects.all():
                # Match user to jobs and cache results
                matches = matching_engine.match_profile_to_jobs(profile.id)
                processed += 1

            logger.info(f"Successfully matched {processed} users to jobs")
            return processed
        except Exception as e:
            logger.error(f"Error in batch matching: {str(e)}")
            raise


@shared_task
def remove_old_jobs():
    """Remove old job listings (older than 30 days by default)"""
    with db.lock("remove_old_jobs", 1800):
        try:
            cutoff_date = timezone.now() - timedelta(days=settings.JOB_EXPIRY_DAYS)
            old_jobs = JobListing.objects.filter(date_posted__lt=cutoff_date)
            count = old_jobs.count()

            # Delete the jobs
            old_jobs.delete()

            logger.info(f"Removed {count} expired job listings")
            return count
        except Exception as e:
            logger.error(f"Error removing old jobs: {str(e)}")
            raise


# Schedule configuration (to be added to settings.py)
"""
CELERY_BEAT_SCHEDULE = {
    'refresh_job_listings': {
        'task': 'core.tasks.refresh_job_listings',
        'schedule': timedelta(hours=6),
    },
    'update_all_embeddings': {
        'task': 'core.tasks.update_all_embeddings',
        'schedule': timedelta(days=7),
    },
    'match_all_users': {
        'task': 'core.tasks.match_all_users',
        'schedule': timedelta(days=1),
    },
    'remove_old_jobs': {
        'task': 'core.tasks.remove_old_jobs',
        'schedule': timedelta(days=1),
    },
}
"""
