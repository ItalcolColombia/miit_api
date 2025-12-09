from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import create_async_engine
from starlette import status

from core.config.settings import get_settings
from core.exceptions.base_exception import BasedException
from database.configuration import DatabaseConfigurationUtil
from utils.logger_util import LoggerUtil

import asyncio
import os

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
        Verify the database connection with retries.

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
        # Leer parámetros de reintento desde variables de entorno (útil en CI/compose)
        max_retries = int(os.getenv('DB_CHECK_RETRIES', '12'))
        delay = float(os.getenv('DB_CHECK_DELAY', '2'))

        checked_database_type = (
            DatabaseConfigurationUtil().check_database_type(self.__database_type)
        )

        last_exception = None
        for attempt in range(1, max_retries + 1):
            try:
                async with self.__engine.connect() as connection:
                    log.info(f"Database -> {checked_database_type} connection successful!")
                    print(
                        f"\033[32m\033[1m\nDatabase -> {checked_database_type} connection successful!\n\033[0m"
                    )
                    return
            except OperationalError as e:
                last_exception = e
                log.warning(f"Attempt {attempt}/{max_retries} - DB not ready: {e}")
            except Exception as e:
                last_exception = e
                log.warning(f"Attempt {attempt}/{max_retries} - unexpected error: {e}")

            if attempt < max_retries:
                await asyncio.sleep(delay)

        # Si llegamos aquí, agotamos los reintentos
        log.error(f"Database connection failed after {max_retries} attempts: {last_exception}")
        raise BasedException(
            message=f"Error inesperado al verificar la conexión a la base de datos: {last_exception}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
