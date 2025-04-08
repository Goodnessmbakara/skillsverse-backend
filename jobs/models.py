from django.db import models
from django.utils.text import slugify
from django.utils.crypto import get_random_string
import uuid
import os
from django.conf import settings

def cv_upload_path(instance, filename):
    """Generate file path for uploaded CVs"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('uploaded_cvs', filename)

class Skill(models.Model):
    """Skill model for the comprehensive skills database"""
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50)
    
    def __str__(self):
        return self.name
        
class Job(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    title = models.CharField(max_length=255)                      # Job title
    description = models.TextField()                               # Detailed job description
    company_name = models.CharField(max_length=255)                # Company offering the job
    location = models.CharField(max_length=255, blank=True, null=True)  # Job location (optional)
    salary_min = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)  # Minimum salary (optional)
    salary_max = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)  # Maximum salary (optional)
    external_link = models.URLField(blank=True, null=True)         # For external applications
    company_logo = models.URLField(blank=True, null=True)          # URL to the company's logo (optional)
    slug = models.SlugField(max_length=255, unique=True, blank=True)  # Auto-generated slug
    tags = models.JSONField(default=list)                          # List of keywords related to the job
    responsibilities = models.JSONField(default=list)              # List of job responsibilities
    qualifications = models.JSONField(default=list)                # Required skills and qualifications
    employment_type = models.CharField(max_length=50, blank=True, null=True)  # e.g., full-time, part-time (optional)
    source = models.CharField(max_length=100, blank=True, null=True) # Source of the job posting (e.g., "RemoteOK")
    epoch = models.BigIntegerField(blank=True, null=True)          # Unix timestamp for job posting (optional)

    created_by = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='jobs') # Creator of the job
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')  # Job status

    created_at = models.DateTimeField(auto_now_add=True)           # Timestamp when job is created
    updated_at = models.DateTimeField(auto_now=True)               # Timestamp when job is updated

    lock_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)  # Amount locked on blockchain
    walrus_lock_id = models.CharField(max_length=255, blank=True, null=True)  # Reference to Walrus lock

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            unique_slug = base_slug
            count = 1
            while Job.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{get_random_string(6)}"
            self.slug = unique_slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class JobActivity(models.Model):
    ACTIVITY_CHOICES = [
        ('applied', 'Applied'),
        ('saved', 'Saved'),
        ('viewed', 'Viewed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="activities")
    job = models.ForeignKey('jobs.Job', on_delete=models.CASCADE, related_name="activities")
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'job', 'activity_type')

    def __str__(self):
        return f"{self.user} {self.activity_type} {self.job}"

class CV(models.Model):
    """CV model to store uploaded CVs and their parsed data"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    file = models.FileField(upload_to=cv_upload_path)
    original_filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_parsed= models.BooleanField(default=False)
    parsed_at = models.DateTimeField(auto_now_add=True, null=True)
    
    # Parsed data (stored as JSON)
    parsed_data = models.JSONField(null=True, blank=True)
    
    # Extracted information
    extracted_skills = models.ManyToManyField(Skill, blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return self.original_filename
    
    def get_file_extension(self):
        """Get the file extension of the CV"""
        return os.path.splitext(self.file.name)[1].lower()

class CVEducation(models.Model):
    """Education details extracted from a CV"""
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='education')
    institution = models.CharField(max_length=255)
    degree = models.CharField(max_length=255, null=True, blank=True)
    years = models.CharField(max_length=100, null=True, blank=True)
    
    def __str__(self):
        return f"{self.institution} - {self.degree}"

class CVWorkExperience(models.Model):
    """Work experience details extracted from a CV"""
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='work_experience')
    company = models.CharField(max_length=255)
    title = models.CharField(max_length=255, null=True, blank=True)
    duration = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.title} at {self.company}"

class CVContactInfo(models.Model):
    """Contact information extracted from a CV"""
    cv = models.OneToOneField(CV, on_delete=models.CASCADE, related_name='contact_info')
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    
    def __str__(self):
        return f"Contact info for {self.cv.original_filename}"

class JobRecommendation(models.Model):
    """Job recommendations for a CV"""
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='recommendations')
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    match_score = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True, null=True)           # Timestamp when job is created

    
    class Meta:
        ordering = ['-match_score']
    
    def __str__(self):
        return f"{self.job.title} - {self.match_score}% match"