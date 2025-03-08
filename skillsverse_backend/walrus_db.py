# core/walrus_db.py
from walrus import Database
from django.conf import settings

# Initialize Redis connection using Walrus
db = Database(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    password=settings.REDIS_PASSWORD,
)
