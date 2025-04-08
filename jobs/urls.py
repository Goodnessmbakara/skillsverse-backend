from django.urls import path
from .views import JobCreateView, JobUpdateView, JobListView, RecommendedJobListView

urlpatterns = [
    path('create/', JobCreateView.as_view(), name='job-create'),
    path('<int:pk>/update/', JobUpdateView.as_view(), name='job-update'),
    path('', JobListView.as_view(), name='job-list'),
    path('recommended/', RecommendedJobListView.as_view(), name='recommended-jobs'),
]
