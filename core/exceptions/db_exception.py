
from fastapi import status

from core.exceptions.base_exception import BasedException


class DatabaseConnectionException(BasedException):
    """
    Class responsible for handling database connection failures.

    This exception is raised when the application fails to establish a connection
    with the database due to incorrect credentials, network issues, or an unavailable server.

    Class Args:
        message (str): The error message describing the connection failure.
        status_code (int): The HTTP status code associated with the exception.
    """

    def __init__(
        self, message: str, status_code: int = status.HTTP_502_BAD_GATEWAY
    ):
        """
        Constructor method for DatabaseConnectionException.

        Initializes the exception with a message and an optional status code.

        Args:
            message (str): The error message describing the exception.
            status_code (int, optional): The HTTP status code to return (default: 502 Bad Gateway).
        """

        super().__init__(
            message,
            status_code,
        )


class DatabaseInvalidConfigurationException(BasedException):
    """
    Class responsible for handling invalid or missing database configurations.

    This exception is raised when the application detects an issue with the
    database configuration, such as missing environment variables, incorrect
    connection strings, or unsupported database types.

    Class Args:
        message (str): The error message describing the configuration issue.
        status_code (int): The HTTP status code associated with the exception (default: 500 Internal Error).
    """

    def __init__(
        self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        """
        Constructor method for DatabaseInvalidConfigurationException.

        Initializes the exception with a message and an optional status code.

        Args:
            message (str): The error message describing the exception.
            status_code (int, optional): The HTTP status code to return (default: 404 Not Found).
        """

        super().__init__(
            message,
            status_code,
        )