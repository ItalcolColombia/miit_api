# /src/core/exceptions/login_exception.py

from fastapi import status
from pycparser.c_ast import Default

from core.exceptions.base_exception import BasedException


class InvalidCredentialsException(BasedException):
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
        self, message: str, status_code: int = status.HTTP_401_UNAUTHORIZED
    ):
        """
        Constructor method for InvalidCredentialsException.

        Initializes the exception with a message and an optional status code.

        Args:
            message (str): The error message describing the exception.
            status_code (int, optional): The HTTP status code to return (default: 404 Not Found).
            :rtype: object
        """

        super().__init__(message, status_code)

class InvalidTokenCredentialsException(BasedException):
    """
    Class responsible for handling exceptions related to invalid token crendentials.

    This exception is raised when a token-based credentials cannot be validated.
    Likewise, when a JWT token is missing, malformed, or does not contain required data.

    Class Attributes:
        None

    Instance Attributes:
        message (str): The error message describing the token-based failure.
        status_code (int): The HTTP status code associated with the exception (default: 401 Not Authorized).
    """

    def __init__(
        self,
        message: str = "No se pudieron validar las credenciales del token.",
        status_code: int = status.HTTP_401_UNAUTHORIZED,
    ):
        self.headers = {"WWW-Authenticate": "Bearer"}
        super().__init__(message, status_code)

class ErrorTokenException(BasedException):
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