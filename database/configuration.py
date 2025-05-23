# /src/infrastructure/database/database_util.py
from typing import Optional
from core.settings import get_settings
from core.enums.database_enum import DatabaseTypeEnum


class DatabaseConfigurationUtil:
    """
    Class responsible for handling database configuration.

    This class manages the database connection settings by retrieving environment
    variables and constructing the appropriate database connection URL.

    Class Args:
        None
    """

    def __init__(self):
        """
        Constructor method for DatabaseConfigurationUtil.

        Initializes the database configuration with environment variables.

        Args:
            None
        """

        self.__api_name = get_settings().API_NAME
        self.__db_type = get_settings().DB_TYPE
        self.__db_name = get_settings().DB_NAME
        self.__db_host = get_settings().DB_HOST
        self.__db_port = get_settings().DB_PORT
        self.__db_user = get_settings().DB_USER
        self.__db_password = get_settings().DB_PASSWORD
        self.__db_type_default = DatabaseTypeEnum.SQLITE.value.upper()

    def get_url(self) -> str:
        """
        Method responsible for retrieving the database connection URL.

        This method verifies the database type and constructs the corresponding
        connection URL.

        Args:
            None

        Returns:
            str: The database connection URL.
        """

        try:
            _db_type = self.__db_type
            _db_url = None

            checked_database_type = self.check_database_type(_db_type)

            _db_url = self.__get_db_config(checked_database_type)

            return _db_url

        except Exception as error:
            message = (
                f"Error in the process of creating the database url: {error}"
            )
            print(message)
            return self.__get_db_config(self.__db_type_default)

    def check_database_type(self, db_type:  Optional[str] = None) -> str:
        """
        Method responsible for validating and retrieving the correct database type.

        If the database type is missing or invalid, it defaults to SQLite.

        Args:
            db_type (str | None): The database type retrieved from environment variables.

        Returns:
            str: The validated database type.
        """

        if (
            db_type is None
            or db_type not in DatabaseTypeEnum.__members__.values()
        ):
            print(
                "\033[33m\033[1m\n"
                + f"The DATABASE_TYPE was not loaded from the .env file, using {self.__db_type_default} as default!"
                + "\033[0m"
            )
            return DatabaseTypeEnum[self.__db_type_default].value
        else:
            return DatabaseTypeEnum[db_type.upper()].value

    def __get_db_config(self, db_type: str) -> str:
        """
        Private method responsible for constructing the database connection URL.

        This method returns the connection string based on the detected database type.

        Args:
            db_type (str): The database type (e.g., PostgreSQL, MySQL, SQLite).

        Returns:
            str: The database connection string.
        """

        _parse_url = f"{self.__db_user}:{self.__db_password}@{self.__db_host}:{self.__db_port}/{self.__db_name}"
        _parse_url_ODBC = f"Driver={{ODBC Driver 17 for SQL Server}};Server={self.__db_host},{self.__db_port};Database={self.__db_name};UID={self.__db_user};PWD={self.__db_password}"

        _db_identifier_config = {
            "PostgreSQL": f"postgresql+asyncpg://{_parse_url}",
            "MySQL": f"mysql+asyncmy://{_parse_url}",
            "MsSQL": f"mssql+aioodbc://{_parse_url_ODBC}",
            "SQLite": f"sqlite:///{self.__api_name}.db",
        }

        return _db_identifier_config.get(db_type, "SQLite")