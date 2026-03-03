# /src/core/middleware/logger_middleware.py

import time
from http import HTTPStatus
from urllib.parse import urlparse

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

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

        # Extraer información detallada de la URL
        parsed_url = urlparse(url)
        endpoint = parsed_url.path
        query_params = parsed_url.query

        # Obtener headers relevantes
        user_agent = request.headers.get("user-agent", "N/A")
        content_type = request.headers.get("content-type", "N/A")

        # Log de entrada más descriptivo
        log_entry = f"[REQUEST] {method} {endpoint}"
        if query_params:
            log_entry += f"?{query_params}"
        log_entry += f" | IP: {host} | Content-Type: {content_type}"

        log.info(log_entry)

        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000
            status_code = response.status_code
            status_name = HTTPStatus(status_code).phrase

            # Log de respuesta más descriptivo
            log_message = f"[RESPONSE] {method} {endpoint} | Status: {status_code} {status_name} | Time: {process_time:.2f}ms | IP: {host}"

            if status_code >= 500:
                log.error(log_message)
            elif status_code >= 400:
                log.warning(log_message)
            else:
                log.info(log_message)

            return response


        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            import traceback
            tb = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            log.error(f"[EXCEPTION] {method} {endpoint} | Time: {process_time:.2f}ms | Error: {type(e).__name__}: {str(e)}")
            log.error(f"[TRACEBACK]\n{tb}")
            raise