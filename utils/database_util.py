import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.exc import OperationalError

from core.settings import Settings
from database.configuration import DatabaseConfigurationUtil

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
        self.__database_type = Settings().DB_TYPE
        self.__engine = create_async_engine(_db_url)  # Use create_async_engine

    async def check_connection(self) -> None:  # Define as async
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
            async with self.__engine.connect() as connection:  # Use async with
                print(
                    f"\033[32m\033[1m\nDatabase -> {checked_database_type} connection successful!\n\033[0m"
                )
        except OperationalError as e:
            print(
                f"\033[31m\033[1m\nDatabase connection failed!\n\033[0m Error: {str(e)}"
            )
            raise

# Example usage (in main.py or another async context):
async def main():
    db_util = DatabaseUtil()
    await db_util.check_connection()

if __name__ == "__main__":
    asyncio.run(main())