#!/bin/bash

# Start Django with Gunicorn
python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec gunicorn backend.wsgi:application --bind 0.0.0.0:${PORT:-8000}
