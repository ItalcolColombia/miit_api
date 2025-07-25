# src/core/exceptions/base/base_exception_handler.py

from http import HTTPStatus

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


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
        request: Request, exc: HTTPException
    ) -> JSONResponse | None:
        """
        Static asynchronous method responsible for handling generic HTTP exceptions.

        This method intercepts `HTTPException` errors raised in FastAPI and returns
        a structured JSON response with relevant status codes and messages.

        Args:
            request (Request): The incoming HTTP request that triggered the exception.
            exc (HTTPException): The exception instance containing status and detail.

        Returns:
            JSONResponse | None: A JSON response containing the error details.
        """

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status_code": str(exc.status_code),
                "status_name": HTTPStatus(exc.status_code).phrase,
                "message": exc.detail,
            },
        )

    @staticmethod
    async def json_decode_error_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse | None:
        """
        Static asynchronous method responsible for handling JSON decoding errors.

        This method intercepts `RequestValidationError` caused by invalid JSON format
        in the request body and returns a structured JSON response.

        Args:
            request (Request): The incoming HTTP request that triggered the exception.
            exc (RequestValidationError): The exception instance containing validation errors.

        Returns:
            JSONResponse | None: A JSON response containing the error details.
        """

        for error in exc.errors():
            if error["type"] == "json_invalid":
                status_code = status.HTTP_400_BAD_REQUEST
                return JSONResponse(
                    status_code=status_code,
                    content={
                        "status_code": str(status_code),
                        "status_name": HTTPStatus(status_code).phrase,
                        "message": "Invalid JSON format. Ensure the request body is correctly formatted.",
                    },
                )
        # Si no es del tipo invalid json se asume que es error de validación
        return await ExceptionHandler.validation_error_handler(request, exc)

    @staticmethod
    async def validation_error_handler(
            request: Request,
            exc: RequestValidationError,
    ) -> JSONResponse | None:
        """
               Static asynchronous method responsible for handling validation errors in the request body.

               This method intercepts `RequestValidationError` caused by missing fields,
               type errors, or constraints in the request data, and returns a structured JSON response
               detailing the validation issues for each field.

               Args:
                   request (Request): The incoming HTTP request that triggered the exception.
                   exc (RequestValidationError): The exception instance containing validation errors.

               Returns:
                   JSONResponse | None: A JSON response containing the error details.
        """
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

        error_messages = []
        for error in exc.errors():
            field = error["loc"][-1]
            message = error["msg"]
            error_messages.append(f"{field.capitalize()}: {message}")

        return JSONResponse(
            status_code=status_code,
            content={
                "status_code": str(status_code),
                "status_name": HTTPStatus(status_code).phrase,
                "message": "Error de validación",
                "details": error_messages
            },
        )

