import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.exc import OperationalError
from starlette import status

from core.exceptions.base_exception import BasedException
from core.settings import get_settings
from database.configuration import DatabaseConfigurationUtil

from utils.logger_util import LoggerUtil
log = LoggerUtil()

class DatabaseUtil:
    """
    Class responsible for handling database utility operations.

    This class provides methods for checking database connections and managing administrative operations.

    Attributes:
        __database_type (str): The type of the database (e.g., PostgreSQL, MySQL).
        __engine (AsyncEngine): The SQLAlchemy async engine for database connections.
    """

    def __init__(self):
        """
        Initialize the DatabaseUtil with database configuration.

        Initializes the database utility by obtaining the database connection URL and setting up the
        database engine using SQLAlchemy's async engine.

        Args:
        None

        Raises:
            BasedException: If the database URL is invalid or engine initialization fails.
        """
        try:
            _db_url = DatabaseConfigurationUtil().get_url()
            self.__database_type = get_settings().DB_TYPE
            self.__engine = create_async_engine(_db_url)
        except Exception as e:
            raise BasedException(
                message=f"Error en database_util:{e}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def check_connection(self) -> None:
        """
        Verify the database connection.

        Attempts to establish a connection with the database using the configured async engine.
        Logs and prints a success message if the connection is successful, or raises an exception
        with a failure message if the connection fails.

        Args:
        None

        Returns:
            None

        Raises:
            OperationalError: If the database connection fails due to connectivity issues.
            BasedException: For other unexpected errors during the connection attempt.
        """
        try:
            checked_database_type = (
                DatabaseConfigurationUtil().check_database_type(
                    self.__database_type
                )
            )

            async with self.__engine.connect() as connection:
                log.info(f"Database -> {checked_database_type} connection successful!")
                print(
                    f"\033[32m\033[1m\nDatabase -> {checked_database_type} connection successful!\n\033[0m"
                )
        except OperationalError as e:
            log.error(f"Database connection failed: {str(e)}")
            print(
                f"\033[31m\033[1m\nDatabase connection failed!\n\033[0m Error: {str(e)}"
            )
            raise
        except Exception as e:
            log.error(f"Error inesperado al verificar la conexión a la base de datos: {e}")
            raise BasedException(
                message="Error inesperado al verificar la conexión a la base de datos.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )