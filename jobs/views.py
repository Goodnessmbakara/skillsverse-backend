from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.status import HTTP_201_CREATED, HTTP_200_OK, HTTP_500_INTERNAL_SERVER_ERROR
from .models import Job
from .serializers import JobSerializer, JobRecommendationSerializer
#from .walrus_client import walrus_client

class StandardResultsPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100

class JobListView(generics.ListAPIView):
    serializer_class = JobSerializer
    pagination_class = StandardResultsPagination
    queryset = Job.objects.all().order_by('-created_at')
    
    def get_queryset(self):
        return self.queryset.select_related('created_by')

class RecommendedJobListView(generics.ListAPIView):
    serializer_class = JobRecommendationSerializer
    pagination_class = StandardResultsPagination
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return JobRecommendation.objects.filter(
            cv__created_by=self.request.user
        ).select_related('job', 'job__created_by').prefetch_related('job__skills').order_by('-created_at')

class JobCreateView(generics.CreateAPIView):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Ensure only organizations can create jobs
        user = self.request.user
        if not user.is_organization:
            return Response({"error": "Only organizations can create jobs."}, status=403)

        serializer.save(created_by=user)
        return Response(serializer.data, status=HTTP_201_CREATED)

class JobUpdateView(generics.UpdateAPIView):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_update(self, serializer):
        user = self.request.user
        job = self.get_object()

        # Ensure only the job creator can update the job
        if job.created_by != user:
            return Response({"error": "You are not authorized to update this job."}, status=403)

        # Check if job status is being updated to 'completed'
        # if self.request.data.get('status') == 'completed':
        #     try:
        #         walrus_client.release_funds(job.walrus_lock_id)
        #     except Exception as e:
        #         return Response({"error": f"Failed to release funds: {str(e)}"}, status=HTTP_500_INTERNAL_SERVER_ERROR)

        serializer.save()
        return Response(serializer.data, status=HTTP_200_OK)
