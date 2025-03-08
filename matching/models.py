# matching/models.py
from walrus import Model, IntegerField, TextField, FloatField
from skillsverse_backend.walrus_db import db


class Match(Model):
    """Match model for storing job-profile matches in Redis"""

    __database__ = db  # Connect to Redis database

    user_profile_id = IntegerField(index=True)  # ForeignKey equivalent
    job_listing_id = IntegerField(index=True)  # ForeignKey equivalent
    match_score = FloatField()  # Store similarity score
    matched_at = TextField(default="")  # Timestamp (optional)

    def __str__(self):
        return f"Match(User: {self.user_profile_id}, Job: {self.job_listing_id}, Score: {self.match_score})"
