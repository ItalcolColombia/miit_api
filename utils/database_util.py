from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

from core.settings import get_settings
from database.configuration import (
    DatabaseConfigurationUtil,
)


class DatabaseUtil:
    """
    Class responsible for handling database utility operations.

    This class provides methods for checking database connections
    and managing administrative operations.

    Class Args:
        None
    """

    def __init__(self):
        """
        Constructor method for DatabaseUtil.

        Initializes the database utility by obtaining the database connection URL
        and setting up the database engine.

        Args:
            None
        """

        _db_url = DatabaseConfigurationUtil().get_url()
        self.__database_type = get_settings().database_type
        self.__engine = create_engine(_db_url)

    def check_connection(self) -> None:
        """
        Public method responsible for verifying the database connection.

        This method attempts to establish a connection with the database
        and prints a success or failure message.

        Returns:
            None

        Raises:
            OperationalError: If the database connection fails.
        """

        checked_database_type = (
            DatabaseConfigurationUtil().check_database_type(
                self.__database_type
            )
        )

        try:
            with self.__engine.connect():
                print(
                    f"\033[32m\033[1m\nDatabase -> {checked_database_type} connection successful!\n\033[0m"
                )
        except OperationalError as e:
            print(
                f"\033[31m\033[1m\nDatabase connection failed!\n\033[0m Error: {str(e)}"
            )
            raise