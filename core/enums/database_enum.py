# /src/core/enums/data_base_enum.py

from enum import Enum


class DatabaseTypeEnum(str, Enum):
    """
    Enumerated class for supported database types.

    This enum defines the possible database engines that can be used in the application.

    Class Args:
        None

    Members:
        POSTGRESQL (str): Represents a PostgreSQL database.
        MYSQL (str): Represents a MySQL database.
        MSSQL (str): Represents a SQLServer database.
        SQLITE (str): Represents an SQLite database.
    """

    POSTGRESQL = "PostgreSQL"
    MYSQL = "MySQL"
    MSSQL = "MSSQL"
    SQLITE = "SQLite"