FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
        gettext \
        libldap2-dev \
        libsasl2-dev \
        libssl-dev \
        netcat-openbsd && \
    which msguniq || { echo "msguniq not found, installing additional packages"; \
        apt-get install -y gettext-base gettext-tools; \
        which msguniq || echo "WARNING: msguniq still not found"; } && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

# Install Python dependencies
COPY requirements.txt .
RUN pip --default-timeout=600 install --no-cache-dir -r requirements.txt

# Create directories for static and media files
RUN mkdir -p /app/static /app/media

# Function to read secrets
RUN echo 'function read_secret() { cat "$1"; }' >> /root/.bashrc

# Create a health check endpoint script
RUN mkdir -p /app/helpdesk_app/core/management/commands && \
    echo 'from django.core.management.base import BaseCommand\n\
from django.http import JsonResponse\n\
from django.urls import path\n\
\n\
def health_check(request):\n\
    return JsonResponse({"status": "ok"})\n\
\n\
class Command(BaseCommand):\n\
    help = "Add health check URL to URLs"\n\
\n\
    def handle(self, *args, **options):\n\
        from django.urls import include, path\n\
        from django.conf import settings\n\
        settings.ROOT_URLCONF = "helpdesk.urls"\n\
        from helpdesk import urls\n\
        urls.urlpatterns += [path("health/", health_check, name="health_check")]\n\
        self.stdout.write(self.style.SUCCESS("Added health check URL"))\n\
' > /app/helpdesk_app/core/management/commands/add_health_check.py

ENV PYTHONPATH=/app

# Default command
CMD ["python", "helpdesk_app/manage.py", "runserver", "0.0.0.0:8000"]