from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from django.shortcuts import get_object_or_404
from django.db.models import F, Q

from apps.users.models import UserProfile
from apps.jobs.models import JobListing
from apps.matching.models import Match
from apps.matching.serializers import (
    MatchSerializer,
    JobMatchSerializer,
    ProfileMatchSerializer,
)
from core.matching.engine import matching_engine
from core.jobs.fetcher import job_fetcher


class MatchViewSet(viewsets.ModelViewSet):
    """
    API endpoint for job-user matches
    """

    queryset = Match.objects.all()
    serializer_class = MatchSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter matches to only show those relevant to requesting user"""
        user = self.request.user
        if user.is_staff:
            return Match.objects.all()
        return Match.objects.filter(user_profile__user=user)

    @action(detail=False, methods=["get"])
    def my_matches(self, request):
        """Get matches for the current user's profile"""
        try:
            profile = request.user.userprofile
        except UserProfile.DoesNotExist:
            return Response(
                {"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Trigger matching algorithm
        matches = matching_engine.match_profile_to_jobs(profile.id)

        return Response(matches)

    @action(detail=False, methods=["post"])
    def refresh_matches(self, request):
        """
        Refresh matches by fetching new jobs and recalculating matches
        """
        query = request.data.get("query", "")
        location = request.data.get("location", "")

        # Fetch fresh job listings
        new_job_ids = job_fetcher.fetch_all_jobs(query, location)

        try:
            profile = request.user.userprofile
            # If new jobs were found, recalculate matches
            if new_job_ids:
                matches = matching_engine.match_profile_to_jobs(profile.id)
                return Response(
                    {
                        "message": f"Found {len(new_job_ids)} new jobs and refreshed matches",
                        "matches": matches,
                    }
                )
            else:
                # Just return current matches
                matches = matching_engine.match_profile_to_jobs(profile.id)
                return Response(
                    {
                        "message": "No new jobs found, using existing matches",
                        "matches": matches,
                    }
                )

        except UserProfile.DoesNotExist:
            return Response(
                {"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND
            )


class JobMatchingViewSet(viewsets.ViewSet):
    """
    API endpoint for job-specific matching operations
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @action(detail=True, methods=["get"])
    def matching_profiles(self, request, pk=None):
        """Get profiles that match a specific job"""
        job = get_object_or_404(JobListing, pk=pk)

        # Only staff or job owner can see matching profiles
        if not request.user.is_staff:
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        matches = matching_engine.match_job_to_profiles(job.id)
        return Response(matches)

    @action(detail=False, methods=["post"])
    def find_matches(self, request):
        """
        Find matches based on a job description without creating a job
        Useful for employers to test potential candidates before posting
        """
        job_data = {
            "title": request.data.get("title", ""),
            "description": request.data.get("description", ""),
            "skills": request.data.get("skills", []),
        }

        # Create a temporary job object
        temp_job = JobListing(
            title=job_data["title"],
            description=job_data["description"],
        )

        # Generate embedding without saving to database
        embedding = matching_engine.create_job_embedding(temp_job)

        # Search for matching profiles
        matches = vector_store.search(embedding, k=20, prefix="profile:")

        # Format matches with profile details and scores
        results = []
        for profile_key, score in matches:
            profile_id = int(profile_key.split(":")[1])
            try:
                profile = UserProfile.objects.get(id=profile_id)
                results.append(
                    {
                        "profile_id": profile_id,
                        "user": profile.user.get_full_name(),
                        "match_score": float(score),
                    }
                )
            except UserProfile.DoesNotExist:
                continue

        return Response(results)


# API Routes (to be added to urls.py)
# router.register(r'matches', MatchViewSet)
# router.register(r'job-matching', JobMatchingViewSet, basename='job-matching')
