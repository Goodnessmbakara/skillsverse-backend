# core/matching/engine.py

import numpy as np
from typing import List, Dict, Any
from django.conf import settings
from django.db.models import Q
from redis_om import HashModel

from user.models import UserProfile
from job.models import JobListing
from matching.models import Match

from redisvl.index import SearchIndex
from walrus import Database

# Initialize Redis with Walrus
db = Database(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD,
    db=0,
)


vector_store = SearchIndex.from_existing(
    name="job_profiles", redis_url=settings.REDIS_URL
)

class JobMatchingEngine:
    """Core engine for matching jobs to user profiles using AI"""

    def __init__(self):
        self.embedding_model = tusky.TextEmbedding(model_name="all-MiniLM-L6-v2")
        self.cache = db.cache()

    def create_job_embedding(self, job: JobListing) -> np.ndarray:
        """Create embedding vector for a job listing"""
        # Combine relevant job details for embedding
        job_text = f"{job.title} {job.description} {' '.join([skill.name for skill in job.required_skills.all()])}"

        # Generate embedding
        return self.embedding_model.embed(job_text)

    def create_profile_embedding(self, profile: UserProfile) -> np.ndarray:
        """Create embedding vector for a user profile"""
        # Combine relevant profile details for embedding
        skills = " ".join([skill.name for skill in profile.skills.all()])
        experience = " ".join(
            [f"{exp.title} {exp.description}" for exp in profile.experience.all()]
        )
        preferences = f"{profile.preferences.desired_role} {profile.preferences.desired_industry} {profile.preferences.location_preference}"

        profile_text = f"{skills} {experience} {preferences}"

        # Generate embedding
        return self.embedding_model.embed(profile_text)

    def store_job_embedding(self, job_id: int, embedding: np.ndarray) -> None:
        """Store job embedding in vector database"""
        vector_store.add(f"job:{job_id}", embedding)

    def store_profile_embedding(self, profile_id: int, embedding: np.ndarray) -> None:
        """Store profile embedding in vector database"""
        vector_store.add(f"profile:{profile_id}", embedding)

    def match_profile_to_jobs(
        self, profile_id: int, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Find jobs that match a user profile"""
        # Check if we have cached results (refreshed daily)
        cache_key = f"matches:profile:{profile_id}"
        cached_matches = self.cache.get(cache_key)

        if cached_matches:
            return cached_matches

        # Get profile embedding
        profile_vector = vector_store.get(f"profile:{profile_id}")
        if profile_vector is None:
            # If profile embedding doesn't exist, create and store it
            profile = UserProfile.objects.get(id=profile_id)
            profile_vector = self.create_profile_embedding(profile)
            self.store_profile_embedding(profile_id, profile_vector)

        # Find similar job listings
        matches = vector_store.search(profile_vector, k=limit, prefix="job:")

        # Format matches with job details and scores
        results = []
        for job_key, score in matches:
            job_id = int(job_key.split(":")[1])
            job = JobListing.objects.get(id=job_id)

            # Create or update match record
            Match.objects.update_or_create(
                user_profile_id=profile_id,
                job_listing_id=job_id,
                defaults={"match_score": float(score)},
            )

            results.append(
                {
                    "job_id": job_id,
                    "title": job.title,
                    "company": job.company.name,
                    "location": job.location,
                    "match_score": float(score),
                    "url": job.url,
                }
            )

        # Cache results for 24 hours
        self.cache.set(cache_key, results, ex=86400)

        return results

    def match_job_to_profiles(
        self, job_id: int, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Find profiles that match a job listing"""
        # Get job embedding
        job_vector = vector_store.get(f"job:{job_id}")
        if job_vector is None:
            # If job embedding doesn't exist, create and store it
            job = JobListing.objects.get(id=job_id)
            job_vector = self.create_job_embedding(job)
            self.store_job_embedding(job_id, job_vector)

        # Find similar profiles
        matches = vector_store.search(job_vector, k=limit, prefix="profile:")

        # Format matches with profile details and scores
        results = []
        for profile_key, score in matches:
            profile_id = int(profile_key.split(":")[1])
            profile = UserProfile.objects.get(id=profile_id)

            # Create or update match record
            Match.objects.update_or_create(
                user_profile_id=profile_id,
                job_listing_id=job_id,
                defaults={"match_score": float(score)},
            )

            results.append(
                {
                    "profile_id": profile_id,
                    "user": profile.user.get_full_name(),
                    "match_score": float(score),
                }
            )

        return results

    def rebuild_all_embeddings(self):
        """Rebuild all embeddings for jobs and profiles"""
        # Process all job listings
        for job in JobListing.objects.all():
            embedding = self.create_job_embedding(job)
            self.store_job_embedding(job.id, embedding)

        # Process all user profiles
        for profile in UserProfile.objects.all():
            embedding = self.create_profile_embedding(profile)
            self.store_profile_embedding(profile.id, embedding)


# Singleton instance
matching_engine = JobMatchingEngine()
