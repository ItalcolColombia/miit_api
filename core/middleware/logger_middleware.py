# /src/core/middleware/logger_middleware.py

import time
from http import HTTPStatus

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse

from utils.logger_util import LoggerUtil

log = LoggerUtil()


class LoggerMiddleware(BaseHTTPMiddleware):
    """
    Class responsible for handling request logging middleware.

    This middleware logs all incoming requests, including details such as the client host,
    HTTP method, request URL, status code, and response time.

    If an error occurs during request processing, the middleware logs the error details.

    Class Args:
        None
    """

    async def dispatch(self, request, call_next) -> Response:
        """
        Public asynchronous method responsible for logging HTTP requests and responses.

        This method logs the details of each request, including the processing time and status code.
        If an error occurs, it logs the error message before raising the exception.

        Args:
            request (Request): The incoming HTTP request.
            call_next: The next middleware or route handler in the pipeline.

        Returns:
            Response: The processed response after logging.

        Raises:
            Exception: If an error occurs while processing the request.
        """

        start_time = time.time()
        host = request.client.host if request.client else "unknown"
        method = request.method
        url = str(request.url)

        log.info(f"Incoming Request: {host} - {method} {url} HTTP/1.1")

        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000
            status_code = response.status_code
            status_name = HTTPStatus(status_code).phrase

            log_message = f"{host} - {method} {url} HTTP/1.1 {status_code} {status_name} - {process_time:.2f}ms"

            if status_code >= 400:
                log.error(log_message)
            else:
                log.info(log_message)

            return response


        except Exception as e:
            import traceback
            tb = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            log.error(f"Middleware caught exception: {type(e).__name__}: {str(e)}\n{tb}")
            raise