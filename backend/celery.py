import os
from celery import Celery
from celery.signals import worker_ready
import logging

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# Configure logging
logger = logging.getLogger('celery')

app = Celery('backend')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

@worker_ready.connect
def at_start(sender, **kwargs):
    """Log when worker is ready"""
    logger.info('Celery worker is ready!')

@app.task(bind=True)
def debug_task(self):
    """Test task to verify Celery is working"""
    logger.info(f'Request: {self.request!r}')
    return 'Celery is working!' 