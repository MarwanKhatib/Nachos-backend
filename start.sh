#!/bin/bash

set -e  # Exit on error

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn..."
exec gunicorn backend.wsgi:application --bind 0.0.0.0:$PORT
