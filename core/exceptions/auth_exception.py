# /src/core/exceptions/login_exception.py

from fastapi import status

from core.exceptions.base_exception import BaseException


class InvalidCredentialsException(BaseException):
    """
    Class responsible for handling exceptions related to invalid user credentials.

    This exception is raised when a user is not found in the database or provides
    incorrect login credentials.

    Class Attributes:
        None

    Instance Attributes:
        message (str): The error message describing the authentication failure.
        status_code (int): The HTTP status code associated with the exception (default: 404 Not Found).
    """

    def __init__(
        self, message: str, status_code: int = status.HTTP_404_NOT_FOUND
    ):
        """
        Constructor method for InvalidCredentialsException.

        Initializes the exception with a message and an optional status code.

        Args:
            message (str): The error message describing the exception.
            status_code (int, optional): The HTTP status code to return (default: 404 Not Found).
        """

        super().__init__(message, status_code)


class ErrorTokenException(BaseException):
    """
    Class responsible for handling exceptions related to token errors.

    This exception is raised when a token is invalid, malformed, or fails validation.

    Class Args:
        message (str): The error message describing the token error.
        status_code (int): The HTTP status code associated with the exception (default: 400 Bad Request).
    """

    def __init__(
        self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST
    ):
        """
        Constructor method for ErrorTokenException.

        Initializes the exception with a message and an optional status code.

        Args:
            message (str): The error message describing the exception.
            status_code (int, optional): The HTTP status code to return (default: 400 Bad Request).
        """

        super().__init__(message, status_code)