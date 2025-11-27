from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from core.exceptions.base_exception import BasedException
from utils.logger_util import LoggerUtil
from utils.response_util import ResponseUtil

log = LoggerUtil()

response_json = ResponseUtil.json_response

class ExceptionHandler:
    """
    Class responsible for handling application-wide exceptions.

    This class provides static methods to handle different types of HTTP exceptions
    and request validation errors in a structured manner.

    Class Args:
        None
    """

    @staticmethod
    async def http_exception_handler(
        request: Request,  exc: StarletteHTTPException
    ) -> JSONResponse:
        """
        Static asynchronous method responsible for handling generic HTTP exceptions.

        This method intercepts `HTTPException` errors raised in FastAPI and returns
        a structured JSON response with relevant status codes and messages. Therefore,
        if the exception is a 404 error, it provides a custom message indicating
        that the requested resource was not found.

        Args:
            request (Request): The incoming HTTP request that triggered the exception.
            exc (HTTPException): The exception instance containing status and detail.

        Returns:
            JSONResponse: A JSON response containing the error details.
        """

        headers = getattr(exc, "headers", None)
        log.error(f"Excepción HTTP capturada: {exc.detail}, Código: {exc.status_code}, Tipo: {type(exc).__name__}")

        if exc.status_code == status.HTTP_404_NOT_FOUND:
            return response_json(
                status_code=status.HTTP_404_NOT_FOUND,
                message= "El endpoint solicitado no exite o la URL es incorrecta",
                headers=headers,
            )

        # Otros HTTPException se devuelven tal cual o personalizados
        return response_json(
            status_code=exc.status_code,
            message="El endpoint solicitado no exite o la URL es incorrecta",
            data=exc.detail,
            headers=headers,
        )

    @staticmethod
    async def based_exception_handler(request: Request, exc: BasedException) -> JSONResponse:
        log.error(f"Excepción no controlada: {type(exc).__name__}, Status: {exc.status_code}, Detail: {exc.detail}, URL: {request.url}")
        headers = getattr(exc, "headers", None)

        return response_json(
            status_code=exc.status_code,
            message="El endpoint solicitado no exite o la URL es incorrecta",
            data=exc.detail,
            headers=headers,
        )

    @staticmethod
    async def json_decode_error_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        """
        Static asynchronous method responsible for handling JSON decoding errors.

        This method intercepts `RequestValidationError` caused by invalid JSON format
        in the request body and returns a structured JSON response.

        Args:
            request (Request): The incoming HTTP request that triggered the exception.
            exc (RequestValidationError): The exception instance containing validation errors.

        Returns:
            JSONResponse: A JSON response containing the error details.
        """

        if any(err["type"] == "json_invalid" for err in exc.errors()):
            return response_json(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="La petición tiene un formato JSON invalido.",
            )

        # Si no es del tipo invalid json se asume que es error de validación
        return await ExceptionHandler.validation_error_handler(request, exc)

    @staticmethod
    async def validation_error_handler(
            request: Request,
            exc: RequestValidationError,
    ) -> JSONResponse:
        """
               Static asynchronous method responsible for handling validation errors in the request body.

               This method intercepts `RequestValidationError` caused by missing fields,
               type errors, or constraints in the request data, and returns a structured JSON response
               detailing the validation issues for each field.

               Args:
                   request (Request): The incoming HTTP request that triggered the exception.
                   exc (RequestValidationError): The exception instance containing validation errors.

               Returns:
                   JSONResponse: A JSON response containing the error details.
        """
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

        error_messages = []
        for error in exc.errors():
            field = error["loc"][-1]
            message = error["msg"]
            error_messages.append(f"{field.capitalize()}: {message}")
        log.error(f"Errores de validación: {error_messages}")

        return response_json(
            status_code=status_code,
            message= "Error de validación",
            data= error_messages,
        )