from rest_framework import serializers
from .models import JobListing
from user.models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = "__all__"


class JobListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobListing
        fields = "__all__"
