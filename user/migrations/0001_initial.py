# Generated by Django 5.1.7 on 2025-03-08 08:40

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="Experience",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=255)),
                ("company", models.CharField(max_length=255)),
                ("location", models.CharField(blank=True, max_length=255)),
                ("start_date", models.DateField()),
                ("end_date", models.DateField(blank=True, null=True)),
                ("current", models.BooleanField(default=False)),
                ("description", models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name="JobPreference",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("desired_role", models.CharField(blank=True, max_length=255)),
                ("desired_industry", models.CharField(blank=True, max_length=255)),
                ("location_preference", models.CharField(blank=True, max_length=255)),
                (
                    "remote_preference",
                    models.CharField(
                        choices=[
                            ("no", "No remote work"),
                            ("hybrid", "Hybrid remote"),
                            ("full", "Fully remote"),
                            ("any", "Any arrangement"),
                        ],
                        default="any",
                        max_length=100,
                    ),
                ),
                ("salary_expectation", models.CharField(blank=True, max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name="Skill",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100, unique=True)),
                ("category", models.CharField(blank=True, max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name="CustomUser",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="last login"
                    ),
                ),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                ("wallet_address", models.CharField(max_length=100, unique=True)),
                ("username", models.CharField(blank=True, max_length=150, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("is_staff", models.BooleanField(default=False)),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("bio", models.TextField(blank=True)),
                ("sui_wallet_address", models.CharField(blank=True, max_length=255)),
                (
                    "profile_picture",
                    models.ImageField(
                        blank=True, null=True, upload_to="profile_pictures/"
                    ),
                ),
                ("experience", models.ManyToManyField(to="user.experience")),
                (
                    "preferences",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="user.jobpreference",
                    ),
                ),
                ("skills", models.ManyToManyField(to="user.skill")),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
