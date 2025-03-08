# core/jobs/fetcher.py

import requests
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.jobs.models import JobListing, Company, Skill
from core.matching.engine import matching_engine

logger = logging.getLogger(__name__)


class JobFetcher:
    """
    Service for fetching jobs from multiple external APIs
    and storing them in the database
    """

    def __init__(self):
        self.apis = {
            "indeed": self._fetch_indeed_jobs,
            "linkedin": self._fetch_linkedin_jobs,
            "glassdoor": self._fetch_glassdoor_jobs,
            "google_jobs": self._fetch_google_jobs,
            "ziprecruiter": self._fetch_ziprecruiter_jobs,
            "careerbuilder": self._fetch_careerbuilder_jobs,
            "adzuna": self._fetch_adzuna_jobs,
            "careerjet": self._fetch_careerjet_jobs,
        }
        self.headers = {
            "User-Agent": "YourJobPlatform/1.0",
            "Content-Type": "application/json",
        }

    def fetch_all_jobs(self, query: str = None, location: str = None):
        """Fetch jobs from all configured APIs"""
        results = []

        for api_name, fetch_func in self.apis.items():
            try:
                logger.info(f"Fetching jobs from {api_name}")
                api_results = fetch_func(query, location)
                results.extend(api_results)
                logger.info(f"Found {len(api_results)} jobs from {api_name}")
            except Exception as e:
                logger.error(f"Error fetching from {api_name}: {str(e)}")

        return self._process_job_results(results)

    def fetch_jobs_by_source(
        self, source: str, query: str = None, location: str = None
    ):
        """Fetch jobs from a specific source"""
        if source not in self.apis:
            raise ValueError(f"Unknown job source: {source}")

        results = self.apis[source](query, location)
        return self._process_job_results(results)

    def _process_job_results(self, job_data: List[Dict[str, Any]]):
        """Process and store job data, returning new job IDs"""
        new_job_ids = []

        with transaction.atomic():
            for job in job_data:
                # Skip jobs without required fields
                if not all(k in job for k in ["title", "company", "url"]):
                    continue

                # Create or get company
                company, _ = Company.objects.get_or_create(
                    name=job["company"],
                    defaults={"website": job.get("company_url", "")},
                )

                # Create or update job listing
                job_obj, created = JobListing.objects.update_or_create(
                    url=job["url"],
                    defaults={
                        "title": job["title"],
                        "company": company,
                        "description": job.get("description", ""),
                        "location": job.get("location", ""),
                        "salary_range": job.get("salary", ""),
                        "job_type": job.get("job_type", ""),
                        "source": job.get("source", ""),
                        "date_posted": job.get("date_posted", timezone.now()),
                        "external_id": job.get("id", ""),
                    },
                )

                # Process skills if available
                if "skills" in job and job["skills"]:
                    for skill_name in job["skills"]:
                        skill, _ = Skill.objects.get_or_create(name=skill_name.strip())
                        job_obj.required_skills.add(skill)

                # Create embedding for new jobs
                if created:
                    new_job_ids.append(job_obj.id)
                    embedding = matching_engine.create_job_embedding(job_obj)
                    matching_engine.store_job_embedding(job_obj.id, embedding)

        return new_job_ids

    # API-specific fetching methods
    def _fetch_indeed_jobs(
        self, query: str = None, location: str = None
    ) -> List[Dict[str, Any]]:
        """Fetch jobs from Indeed API"""
        url = "https://api.indeed.com/ads/apisearch"
        params = {
            "publisher": settings.INDEED_API_KEY,
            "format": "json",
            "v": "2",
            "limit": 25,
            "q": query or "",
            "l": location or "",
        }

        response = requests.get(url, params=params, headers=self.headers)
        response.raise_for_status()

        data = response.json()
        results = []

        for job in data.get("results", []):
            results.append(
                {
                    "title": job.get("jobtitle", ""),
                    "company": job.get("company", ""),
                    "description": job.get("snippet", ""),
                    "location": job.get("formattedLocation", ""),
                    "url": job.get("url", ""),
                    "date_posted": datetime.fromtimestamp(int(job.get("date", 0))),
                    "source": "indeed",
                    "id": job.get("jobkey", ""),
                }
            )

        return results

    def _fetch_linkedin_jobs(
        self, query: str = None, location: str = None
    ) -> List[Dict[str, Any]]:
        """Fetch jobs from LinkedIn API"""
        url = "https://api.linkedin.com/v2/jobs"
        headers = {
            **self.headers,
            "Authorization": f"Bearer {settings.LINKEDIN_API_TOKEN}",
        }
        params = {
            "keywords": query or "",
            "location": location or "",
        }

        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()

        data = response.json()
        results = []

        for job in data.get("elements", []):
            results.append(
                {
                    "title": job.get("title", {}).get("text", ""),
                    "company": job.get("companyDetails", {})
                    .get("company", {})
                    .get("name", ""),
                    "description": job.get("description", {}).get("text", ""),
                    "location": job.get("locationName", ""),
                    "url": f"https://www.linkedin.com/jobs/view/{job.get('entityUrn', '').split(':')[-1]}",
                    "source": "linkedin",
                    "id": job.get("entityUrn", "").split(":")[-1],
                }
            )

        return results

    # Add similar methods for the other job sources
    def _fetch_glassdoor_jobs(
        self, query: str = None, location: str = None
    ) -> List[Dict[str, Any]]:
        """Fetch jobs from Glassdoor API"""
        # Implementation similar to other methods
        url = "https://api.glassdoor.com/api/v1/jobs"
        # ... implementation details
        return []

    def _fetch_google_jobs(
        self, query: str = None, location: str = None
    ) -> List[Dict[str, Any]]:
        """Fetch jobs from Google Jobs API via SerpAPI"""
        url = "https://serpapi.com/search"
        params = {
            "engine": "google_jobs",
            "q": query or "jobs",
            "location": location or "",
            "api_key": settings.SERPAPI_API_KEY,
        }

        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        results = []

        for job in data.get("jobs_results", []):
            results.append(
                {
                    "title": job.get("title", ""),
                    "company": job.get("company_name", ""),
                    "description": job.get("description", ""),
                    "location": job.get("location", ""),
                    "url": job.get("apply_link", {}).get("link", ""),
                    "source": "google_jobs",
                    "id": job.get("job_id", ""),
                    "salary": job.get("salary", ""),
                    "date_posted": job.get("posted_at", ""),
                }
            )

        return results

    # Implement the remaining API methods similarly
    def _fetch_ziprecruiter_jobs(
        self, query: str = None, location: str = None
    ) -> List[Dict[str, Any]]:
        return []

    def _fetch_careerbuilder_jobs(
        self, query: str = None, location: str = None
    ) -> List[Dict[str, Any]]:
        return []

    def _fetch_adzuna_jobs(
        self, query: str = None, location: str = None
    ) -> List[Dict[str, Any]]:
        return []

    def _fetch_careerjet_jobs(
        self, query: str = None, location: str = None
    ) -> List[Dict[str, Any]]:
        return []


# Singleton instance
job_fetcher = JobFetcher()
