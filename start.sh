#!/bin/bash
echo "Starting Gunicorn..."
exec gunicorn backend.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 60
