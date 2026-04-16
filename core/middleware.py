"""core/middleware.py"""
import logging
import time

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    """Logs all incoming requests with timing information."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        duration = round((time.time() - start_time) * 1000, 2)

        logger.info(
            '%s %s %s %dms',
            request.method,
            request.path,
            response.status_code,
            duration,
        )
        return response
