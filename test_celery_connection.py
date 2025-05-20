import os
import django
import redis
import logging
from decouple import config

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

# Import Celery app after Django setup
from backend.celery import app
from APIs.tasks import test_celery, send_verification_email

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_redis_connection():
    """Test Redis connection directly"""
    try:
        # Try connecting to Redis
        r = redis.Redis(host='127.0.0.1', port=6379, db=0)
        response = r.ping()
        logger.info(f"Redis connection test: {'Success' if response else 'Failed'}")
        return True
    except Exception as e:
        logger.error(f"Redis connection error: {str(e)}")
        return False

def test_celery_connection():
    """Test Celery connection and task execution"""
    try:
        # Send task to queue using the existing app
        result = test_celery.delay()
        logger.info(f"Task ID: {result.id}")
        
        # Wait for result
        task_result = result.get(timeout=10)
        logger.info(f"Task result: {task_result}")
        return True
    except Exception as e:
        logger.error(f"Celery connection error: {str(e)}")
        return False

def test_email_config():
    """Test email configuration from .env"""
    try:
        email_user = config("EMAIL_HOST_USER", default=None)
        email_password = config("EMAIL_HOST_PASSWORD", default=None)
        
        logger.info(f"Email configuration check:")
        logger.info(f"EMAIL_HOST_USER: {'Set' if email_user else 'Not set'}")
        logger.info(f"EMAIL_HOST_PASSWORD: {'Set' if email_password else 'Not set'}")
        
        if not email_user or not email_password:
            logger.error("Email configuration is missing")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Error checking email config: {str(e)}")
        return False

def test_email_task():
    """Test email sending task directly"""
    try:
        # Get email config
        email_user = config("EMAIL_HOST_USER")
        test_email = email_user  # Send to the same email for testing
        test_key = "123456"
        
        logger.info(f"Testing email task with:")
        logger.info(f"From: {email_user}")
        logger.info(f"To: {test_email}")
        
        # Send task
        result = send_verification_email.delay(test_email, test_key)
        logger.info(f"Email task ID: {result.id}")
        
        # Wait for result
        task_result = result.get(timeout=30)
        logger.info(f"Email task result: {task_result}")
        return True
    except Exception as e:
        logger.error(f"Email task error: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting connection tests...")
    
    # Test Redis
    logger.info("\nTesting Redis connection...")
    redis_success = test_redis_connection()
    
    # Test Celery
    logger.info("\nTesting Celery connection...")
    celery_success = test_celery_connection()
    
    # Test Email Config
    logger.info("\nTesting Email configuration...")
    email_config_success = test_email_config()
    
    # Test Email Task
    logger.info("\nTesting Email task...")
    email_success = test_email_task()
    
    # Print summary
    logger.info("\nTest Summary:")
    logger.info(f"Redis Connection: {'Success' if redis_success else 'Failed'}")
    logger.info(f"Celery Connection: {'Success' if celery_success else 'Failed'}")
    logger.info(f"Email Configuration: {'Success' if email_config_success else 'Failed'}")
    logger.info(f"Email Task: {'Success' if email_success else 'Failed'}") 