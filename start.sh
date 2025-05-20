#!/bin/bash

# Start Celery worker in the background
celery -A backend worker -l info --concurrency=2 &

# Start Celery beat in the background
celery -A backend beat -l info &

# Start Django with Gunicorn
gunicorn backend.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 2