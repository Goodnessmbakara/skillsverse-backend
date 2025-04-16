# jobs/tasks.py
from celery import shared_task
from .job_fetcher import fetch_jobs_task


import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings

# Celery imports
from celery import shared_task, group
from celery.result import ResultSet

# Django models
from jobs.models import CV, JobRecommendation
from django.db.models import Q

# Imported services
from jobs.services.cv_parser import CVParser
print("I have gotten the CVPrser", CVParser)
from ./services.job_recommender import JobRecommender

# Logging setup
logger = logging.getLogger(__name__)

class CVProcessingManager:
    """
    Manages CV processing and job recommendation at scale
    """
    def __init__(self):
        self.cv_parser = CVParser()
        self.job_recommender = JobRecommender()
    
    def process_unprocessed_cvs(self, batch_size=100):
        """
        Process CVs in batches with scalability in mind
        
        Args:
            batch_size (int): Number of CVs to process in one batch
        
        Returns:
            dict: Processing statistics
        """
        # Find unprocessed CVs
        
        unprocessed_cvs = CV.objects.filter(
            Q(is_parsed=False) | 
            Q(parsed_at__isnull=True)
        ).order_by('created_at')[:batch_size]
        
        # Prepare batch processing
        cv_processing_tasks = []
        
        for cv in unprocessed_cvs:
            # Create async task for each CV
            task = self.process_single_cv.delay(cv.id)
            cv_processing_tasks.append(task)
        
        # Wait for all tasks to complete
        results = ResultSet(cv_processing_tasks)
        results.join()
        
        # Compile processing statistics
        stats = {
            'total_cvs_processed': len(unprocessed_cvs),
            'successful_parsing': 0,
            'failed_parsing': 0
        }
        
        for task_result in results:
            if task_result:
                stats['successful_parsing'] += 1
            else:
                stats['failed_parsing'] += 1
        
        return stats
    
    @shared_task(bind=True, max_retries=3)
    def process_single_cv(self, cv_id):
        """
        Process a single CV for parsing and job recommendations
        
        Args:
            cv_id (int): ID of the CV to process
        
        Returns:
            bool: Processing success status
        """
        try:
            # Retrieve CV
            cv = CV.objects.get(id=cv_id)
            
            # Prevent reprocessing
            if cv.is_parsed:
                logger.info(f"CV {cv_id} already parsed. Skipping.")
                return False
            
            # Parse CV
            parsing_success = self.cv_parser.parse_cv(cv_id)
            
            if parsing_success:
                # Update CV status
                cv.is_parsed = True
                cv.parsed_at = timezone.now()
                cv.save()
                
                # Generate job recommendations
                recommendations = self.job_recommender.recommend_jobs_for_cv(cv_id)
                
                logger.info(f"Processed CV {cv_id}: {len(recommendations)} job recommendations generated")
                return True
            else:
                logger.error(f"Failed to parse CV {cv_id}")
                return False
        
        except Exception as e:
            logger.error(f"Error processing CV {cv_id}: {str(e)}")
            # Retry mechanism
            self.process_single_cv.retry(exc=e)
            return False


# Periodic Task Configuration for Celery
@shared_task
def scheduled_cv_processing():
    """
    Scheduled task to process CVs periodically
    """
    processing_manager = CVProcessingManager()
    stats = processing_manager.process_unprocessed_cvs()
    
    # Optional: Send admin notification or log results
    if stats['failed_parsing'] > 0:
        # Send alert or log to monitoring system
        logger.warning(f"CV Processing Alert: {stats['failed_parsing']} CVs failed processing")


# Scalability Optimizations for Large Datasets
class ScalabilityOptimizer:
    """
    Additional strategies for handling large-scale CV and job recommendation processing
    """
    @staticmethod
    def optimize_job_recommendations(max_recommendations=10):
        """
        Limit and optimize job recommendations
        """
        # Prune old or low-scoring recommendations
        JobRecommendation.objects.filter(
            match_score__lt=30  # Remove low-scoring recommendations
        ).delete()
        
        # Limit recommendations per CV
        for cv in CV.objects.all():
            recommendations = JobRecommendation.objects.filter(cv=cv)
            if recommendations.count() > max_recommendations:
                # Keep top N recommendations
                to_delete = recommendations.order_by('match_score')[:recommendations.count() - max_recommendations]
                to_delete.delete()
    

@shared_task
def fetch_jobs_tasks():
    return fetch_jobs_task()
 

