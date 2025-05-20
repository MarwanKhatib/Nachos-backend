#!/bin/bash

# Start Celery worker in the background
celery -A backend worker -l info --concurrency=1 &

# Start Celery beat in the background
celery -A backend beat -l info &

# Start Django server
python manage.py runserver 127.0.0.1:8000