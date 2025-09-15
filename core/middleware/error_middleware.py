from datetime import datetime

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from core.exceptions.base_exception import BasedException
from core.handlers.exception_handler import ExceptionHandler
from schemas.response_models import ErrorResponse
from utils.logger_util import LoggerUtil
from http import HTTPStatus

log = LoggerUtil()

class ErrorMiddleware(BaseHTTPMiddleware):
    """
    Custom middleware to catch unhandled exceptions, log, and format as JSON.
    Inspired by MAAS: Acts as a fallback after specific handlers.
    """
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            log.error(f"Unhandled exception: {type(exc).__name__}, Detail: {str(exc)}, URL: {request.url}", exc_info=True)
            # Chain if cause exists
            cause = exc.__cause__ or exc
            return JSONResponse(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
                content=f"Internal server error: {str(cause)}",
            )

