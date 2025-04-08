import requests
from django.db import IntegrityError
from django.utils.text import slugify
from django.utils.crypto import get_random_string
from .models import Job
from datetime import datetime
from django.contrib.auth import get_user_model

User = get_user_model()


def get_or_create_system_user():
    """Ensure a system user exists to assign external jobs."""
    system_wallet = "external_system_wallet"

    user, _ = User.objects.get_or_create(
        wallet_address=system_wallet,
        defaults={
            "user_type": "organization",
            "is_active": True,
            "is_staff": True,
        },
    )
    return user


def fetch_external_jobs():
    external_apis = [
        "https://remoteok.io/api",
        "https://www.arbeitnow.com/api/job-board-api",
    ]

    all_jobs = []
    for api_url in external_apis:
        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Handle different API response structures
            if api_url == "https://remoteok.io/api" and isinstance(data, list) and len(data) > 0:
                # RemoteOK API sometimes has a meta object at index 0
                if isinstance(data[0], dict) and data[0].get("0", "") == "API Documentation":
                    data = data[1:]  # Skip the first meta object
                all_jobs.extend(data)
            elif api_url == "https://www.arbeitnow.com/api/job-board-api" and isinstance(data, dict):
                if "data" in data and isinstance(data["data"], list):
                    all_jobs.extend(data["data"])
                elif "jobs" in data and isinstance(data["jobs"], list):
                    all_jobs.extend(data["jobs"])

        except requests.RequestException as e:
            print(f"Failed to fetch jobs from {api_url}: {e}")
        except ValueError as e:
            print(f"Failed to parse JSON from {api_url}: {e}")

    return all_jobs


def generate_unique_slug(title):
    """Generate a unique slug from the job title."""
    if not title or title == "Untitled":
        title = "job-posting-" + get_random_string(8)
    
    base_slug = slugify(title)
    unique_slug = base_slug
    
    counter = 1
    while Job.objects.filter(slug=unique_slug).exists():
        unique_slug = f"{base_slug}-{counter}"
        counter += 1
        
    return unique_slug


def map_job_data(job):
    """Map external API fields to the Job model accounting for different API formats."""
    # Handle different APIs with various field names
    title = job.get("title", job.get("position", job.get("name", "Untitled")))
    company = job.get("company", job.get("company_name", "Unknown"))
    description = job.get("description", job.get("body", ""))
    location = job.get("location", job.get("region", "Remote"))
    url = job.get("url", job.get("link", job.get("apply_url", "")))
    
    # Tags handling
    tags = []
    if isinstance(job.get("tags"), list):
        tags = job.get("tags")
    elif isinstance(job.get("keywords"), list):
        tags = job.get("keywords")
    elif isinstance(job.get("tags"), str):
        tags = [tag.strip() for tag in job.get("tags").split(",")]
    
    return Job(
        title=title,
        description=description,
        company_name=company,
        location=location,
        external_link=url,
        company_logo=job.get("company_logo", job.get("logo", "")),
        slug=generate_unique_slug(title),
        tags=tags,
        responsibilities=job.get("responsibilities", []),
        qualifications=job.get("qualifications", []),
        employment_type=job.get("employment_type", job.get("job_type", "Full-time")),
        source=job.get("source", "external"),
        epoch=job.get("epoch", int(datetime.now().timestamp())),
        created_by=get_or_create_system_user(),
        lock_amount=0.00,
        status="open",
    )


def save_jobs_to_db(job_list):
    """Save jobs in bulk, avoiding duplicates."""
    # Ensure all jobs are valid dictionaries
    job_list = [job for job in job_list if isinstance(job, dict)]
    
    # Fetch existing job URLs and titles to check for duplicates
    existing_job_urls = set(Job.objects.values_list("external_link", flat=True))
    existing_job_titles_and_companies = set(
        Job.objects.values_list("title", "company_name")
    )
    
    new_jobs = []
    for job in job_list:
        # Skip jobs with empty titles
        if not job.get("title") and not job.get("position") and not job.get("name"):
            continue
            
        mapped_job = map_job_data(job)
        
        # Check if job already exists by URL or title+company combination
        url_exists = mapped_job.external_link and mapped_job.external_link in existing_job_urls
        title_company_exists = (mapped_job.title, mapped_job.company_name) in existing_job_titles_and_companies
        
        if not url_exists and not title_company_exists:
            new_jobs.append(mapped_job)
            # Update our sets to avoid duplicates within this batch
            if mapped_job.external_link:
                existing_job_urls.add(mapped_job.external_link)
            existing_job_titles_and_companies.add((mapped_job.title, mapped_job.company_name))
    
    saved_count = 0
    if new_jobs:
        try:
            Job.objects.bulk_create(new_jobs)
            saved_count = len(new_jobs)
            print(f"Successfully saved {saved_count} new jobs.")
        except IntegrityError as e:
            # Fall back to individual creation if bulk fails
            print(f"Bulk create failed, trying individual creation: {e}")
            saved_count = 0
            for job in new_jobs:
                try:
                    job.save()
                    saved_count += 1
                except IntegrityError:
                    pass
            print(f"Successfully saved {saved_count} new jobs individually.")
    else:
        print("No new jobs to save.")
    
    return saved_count


def fetch_jobs_task():
    """Task to fetch and store jobs from external APIs."""
    jobs = fetch_external_jobs()

    if not jobs:
        print("No jobs fetched from external APIs.")
        return "No jobs fetched."

    saved_count = save_jobs_to_db(jobs)
    return f"Successfully saved {saved_count} new jobs."