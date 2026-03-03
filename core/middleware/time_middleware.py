import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class TimeMiddleware(BaseHTTPMiddleware):
    """
    Class responsible for measuring and logging the processing time of HTTP requests.

    This middleware calculates the time taken to process each request and adds it to the response headers.
    Detailed logging is handled by LoggerMiddleware.

    Class Args:
        None
    """

    async def dispatch(self, request, call_next) -> Response:
        """
        Public asynchronous method responsible for measuring request processing time.

        This method measures the processing time and adds it as a response header.
        The detailed logging with endpoint info is handled by LoggerMiddleware.

        Args:
            request (Request): The incoming HTTP request.
            call_next: The next middleware or route handler in the pipeline.

        Returns:
            Response: The processed response with timing header.

        Raises:
            Exception: If an error occurs while processing the request, it is propagated.
        """
        start_time = time.time()
        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000

            # Añadir tiempo de procesamiento como header para debugging
            response.headers["X-Process-Time"] = f"{process_time:.2f}ms"

            return response
        except Exception as e:
            # Solo propagar la excepción, el logging detallado lo hace LoggerMiddleware
            raise
