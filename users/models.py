from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import models
from django.conf import settings
import secrets

class UserManager(BaseUserManager):
    def create_user(self, wallet_address, **extra_fields):
        if not wallet_address:
            raise ValueError('The Wallet Address is required')
        user = self.model(wallet_address=wallet_address, **extra_fields)
        user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, wallet_address, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(wallet_address, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    USER_TYPES = (
        ('job_seeker', 'Job Seeker'),
        ('organization', 'Organization'),
    )

    user_type = models.CharField(max_length=20, choices=USER_TYPES)
    github_url = models.URLField(blank=True, null=True)
    behance_url = models.URLField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    wallet_address = models.CharField(max_length=100, unique=True)
    nonce = models.CharField(max_length=100, default=secrets.token_hex(16))
    last_nonce_refresh = models.DateTimeField(auto_now_add=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'wallet_address'
    REQUIRED_FIELDS = []

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_groups',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions',
        blank=True
    )

    def __str__(self):
        return self.wallet_address

    @property
    def is_organization(self):
        return self.user_type == 'organization'

    @property
    def is_job_seeker(self):
        return self.user_type == 'job_seeker'

    def check_wallet(self, wallet_address):
        return self.wallet_address == wallet_address
    
    def generate_new_nonce(self):
        self.nonce = secrets.token_hex(16)
        self.save()
        return self.nonce


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    email = models.EmailField(blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    skills = models.TextField(blank=True, null=True)  # Store comma-separated skills

    def __str__(self):
        return f"Profile of {self.user}"

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()