from fastapi import status

from core.exceptions.base_exception import BasedException


class UnauthorizedToken(BasedException):
    """
    Class responsible for handling exceptions related to unauthorized tokens.

    This exception is raised when an authentication token is invalid, expired,
    or lacks the necessary permissions to access a resource.

    Class Args:
        message (str): The error message describing the authentication failure.
        status_code (int): The HTTP status code associated with the exception (default: 401 Unauthorized).
        headers (dict): The HTTP header associated with the exception (default: {"WWW-Authenticate": "Bearer"}).
    """

    def __init__(
        self, message: str, status_code: int = status.HTTP_401_UNAUTHORIZED, headers: dict | None = None
    ):
        """
        Constructor method for UnauthorizedToken.

        Initializes the exception with a message and an optional status code.

        Args:
            message (str): The error message describing the exception.
            status_code (int, optional): The HTTP status code to return (default: 401 Unauthorized).
            headers (dict | optional): The HTTP headers related (default: {"WWW-Authenticate": "Bearer"}).
        """
        if headers is None:
            headers = {"WWW-Authenticate": "Bearer"}
        super().__init__(message, status_code,headers)