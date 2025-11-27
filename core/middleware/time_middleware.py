import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from utils.logger_util import LoggerUtil

log = LoggerUtil()

class TimeMiddleware(BaseHTTPMiddleware):
    """
    Class responsible for measuring and logging the processing time of HTTP requests.

    This middleware calculates the time taken to process each request and logs it.
    If an error occurs during request processing, it logs the error details and propagates
    the exception to be handled by global exception handlers.

    Class Args:
        None
    """

    async def dispatch(self, request, call_next) -> Response:
        """
        Public asynchronous method responsible for measuring and logging request processing time.

        This method logs the processing time of each request. If an error occurs, it logs the error
        message and traceback before propagating the exception.

        Args:
            request (Request): The incoming HTTP request.
            call_next: The next middleware or route handler in the pipeline.

        Returns:
            Response: The processed response after logging.

        Raises:
            Exception: If an error occurs while processing the request, it is propagated.
        """
        start_time = time.time()
        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000
            log.info(f"Request processed in {process_time:.2f}ms")
            return response
        except Exception as e:
            import traceback
            tb = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            log.error(f"Error processing request: {type(e).__name__}: {str(e)}\n{tb}")
            raise  # Propagate the exception to be handled by global exception handlers