#!/bin/bash
echo "Starting Gunicorn..."
exec gunicorn backend.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --worker-class gevent --timeout 120 --reload
