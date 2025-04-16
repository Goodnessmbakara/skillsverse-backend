#!/bin/bash
set -e

# Make database migrations
echo "Making database migrations..."
python manage.py makemigrations --noinput

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Execute command passed to docker run
exec "$@"