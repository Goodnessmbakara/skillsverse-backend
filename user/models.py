from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models


class CustomUserManager(BaseUserManager):
    """Manager for handling Sui-based authentication"""

    def create_user(self, wallet_address, **extra_fields):
        """Create a user using only their wallet address"""
        if not wallet_address:
            raise ValueError("Users must have a wallet address")

        user = self.model(wallet_address=wallet_address, **extra_fields)
        user.save(using=self._db)
        return user

    def create_superuser(self, wallet_address, **extra_fields):
        """Create a superuser"""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(wallet_address, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """Custom user model using Sui wallet for authentication"""

    wallet_address = models.CharField(max_length=100, unique=True)
    username = models.CharField(max_length=150, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = "wallet_address"  # Users log in with wallet address
    REQUIRED_FIELDS = []  # No email/password needed

    def __str__(self):
        return self.wallet_address


class Skill(models.Model):
    """Model representing a professional skill"""

    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name


class Experience(models.Model):
    """Model representing work experience"""

    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    current = models.BooleanField(default=False)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.title} at {self.company}"


class JobPreference(models.Model):
    """Model representing job preferences"""

    desired_role = models.CharField(max_length=255, blank=True)
    desired_industry = models.CharField(max_length=255, blank=True)
    location_preference = models.CharField(max_length=255, blank=True)
    remote_preference = models.CharField(
        max_length=100,
        choices=[
            ("no", "No remote work"),
            ("hybrid", "Hybrid remote"),
            ("full", "Fully remote"),
            ("any", "Any arrangement"),
        ],
        default="any",
    )
    salary_expectation = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Preferences for {self.desired_role}"


class UserProfile(models.Model):
    """Extended user profile for job matching"""

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    skills = models.ManyToManyField(Skill)
    experience = models.ManyToManyField(Experience)
    preferences = models.OneToOneField(
        JobPreference, on_delete=models.CASCADE, null=True, blank=True
    )
    sui_wallet_address = models.CharField(max_length=255, blank=True)
    profile_picture = models.ImageField(
        upload_to="profile_pictures/", blank=True, null=True
    )

    def __str__(self):
        return f"{self.user.username}'s profile"

