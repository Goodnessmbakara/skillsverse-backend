from django.urls import path
from .views import UserProfileList, JobListingList

urlpatterns = [
    path("profiles/", UserProfileList.as_view(), name="user-profiles"),
    path("jobs/", JobListingList.as_view(), name="job-listings"),
]

