from rest_framework import generics
from rest_framework.views import APIView
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from user.models import UserProfile
from walrus import Database

from .models import JobListing
from .serializers import JobListingSerializer, UserProfileSerializer


db = Database(host="localhost", port=6379, db=0)


class MatchJobs(APIView):
    def post(self, request):
        profile = request.data.get("profile")  # e.g., {"skills": "Python, Django"}
        jobs = JobListing.objects.all()
        job_texts = [job.requirements for job in jobs]

        vectorizer = TfidfVectorizer()
        job_vectors = vectorizer.fit_transform(job_texts)
        profile_vector = vectorizer.transform([profile["skills"]])
        similarities = cosine_similarity(profile_vector, job_vectors).flatten()

        matches = sorted(zip(jobs, similarities), key=lambda x: x[1], reverse=True)[:5]
        return Response(
            [
                {"job": JobListingSerializer(job).data, "score": float(score)}
                for job, score in matches
            ]
        )


class UserProfileList(generics.ListCreateAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer


class JobListingList(generics.ListCreateAPIView):
    queryset = JobListing.objects.all()
    serializer_class = JobListingSerializer

    def get(self, request, *args, **kwargs):
        cache = db.cache()
        cached_jobs = cache.get("job_listings")
        if cached_jobs:
            return Response(cached_jobs)
        else:
            serializer = self.get_serializer(self.get_queryset(), many=True)
            cache.set("job_listings", serializer.data, timeout=3600)  # Cache for 1 hour
            return Response(serializer.data)
