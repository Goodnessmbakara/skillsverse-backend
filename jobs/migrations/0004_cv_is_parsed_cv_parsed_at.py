# Generated by Django 5.1.7 on 2025-03-31 18:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0003_cv_skill_cvcontactinfo_cveducation_cvworkexperience_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='cv',
            name='is_parsed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='cv',
            name='parsed_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
