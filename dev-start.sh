#!/bin/bash

# Remove stale celerybeat files if they exist
rm -f celerybeat-schedule celerybeat-schedule.db celerybeat.pid

# Start Celery worker in the background
celery -A backend worker -l info --concurrency=2 &

# Start Celery beat in the background
celery -A backend beat -l info &

# Start Django with Gunicorn with hot reload enabled
# gunicorn backend.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 2
gunicorn backend.wsgi:application --bind 0.0.0.0:3000 --workers 2 --threads 2 --reload
