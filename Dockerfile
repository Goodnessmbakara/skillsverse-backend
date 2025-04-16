FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libjpeg-dev \
    libpq-dev \
    libxml2-dev \
    libxslt-dev \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /app

# First install non-conflicting packages 
COPY requirements-base.txt .
RUN pip install --no-cache-dir -r requirements-base.txt

# Install packages requiring numpy < 2 with specific numpy version
COPY requirements-numpy1.txt .
RUN pip install --no-cache-dir numpy==1.26.4 && \
    pip install --no-cache-dir -r requirements-numpy1.txt

# Install packages requiring numpy >= 2 with updated numpy
COPY requirements-numpy2.txt .
RUN pip install --no-cache-dir numpy==2.2.4 --force-reinstall && \
    pip install --no-cache-dir -r requirements-numpy2.txt

# Copy project files
COPY . .

# Expose ports
EXPOSE 8000

# Set entrypoint
RUN pwd
ENTRYPOINT ["./skillsverse_backend/docker-entrypoint.sh"]

# Default command
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]