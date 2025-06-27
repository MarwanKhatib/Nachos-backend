import logging
import json

logger = logging.getLogger(__name__)

class RequestLoggerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user_id = request.user.id if request.user.is_authenticated else "anonymous"
        logger.info(f"Request started: User ID: {user_id}, Path: {request.path}")

        response = None
        try:
            response = self.get_response(request)
        except Exception as e:
            logger.error(f"Request failed with exception: User ID: {user_id}, Path: {request.path}, Error: {e}", exc_info=True)
            raise # Re-raise the exception after logging

        status_message = "succeeded" if 200 <= response.status_code < 300 else "failed"
        log_message = f"Request finished: User ID: {user_id}, Path: {request.path}, Status: {response.status_code} ({status_message})"

        if status_message == "failed":
            try:
                # Attempt to log response content for failed requests
                if hasattr(response, 'content') and response.content:
                    content = response.content.decode('utf-8')
                    # Try to parse as JSON for better readability
                    try:
                        json_content = json.loads(content)
                        log_message += f", Response: {json.dumps(json_content)}"
                    except json.JSONDecodeError:
                        log_message += f", Response: {content}"
            except Exception as e:
                logger.warning(f"Could not decode response content for logging: {e}")

        logger.info(log_message)

        return response
