# Generated by Django 5.1.7 on 2025-03-31 18:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_userprofile'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='nonce',
            field=models.CharField(default='416d8ecc85218c079f314b88187fe423', max_length=100),
        ),
    ]
