# /src/infrastructure/database/database_configuration.py

from typing import Any, AsyncGenerator

from asyncpg.exceptions import InvalidCachedStatementError
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

from core.exceptions.db_exception import DatabaseSQLAlchemyException
from database.configuration import (
    DatabaseConfigurationUtil,
)


class DatabaseConfiguration:
    """
    Class responsible for configuring and providing access to the database connection.

    This class initializes the database engine, session factory, and declarative base
    for defining database models. It also provides methods for retrieving database
    sessions and managing table creation.

    Class Args:
        None
    """

    _db_url = DatabaseConfigurationUtil().get_url()

    # Create the SQLAlchemy engine
    # Ensure the DB session timezone is set to America/Bogota so queries and
    # returned timestamp values reflect UTC-5 (Bogotá) when using TIMESTAMPTZ.
    # asyncpg accepts `server_settings` in connect_args to set session parameters
    # on connection (e.g. timezone).
    _engine = create_async_engine(
        _db_url,
        echo=False,
        future=True,
        max_overflow=10,
        pool_size=5,
        connect_args={"server_settings": {"timezone": "America/Bogota"}},
    )

    # Also ensure on raw SQLAlchemy connect we set the timezone in the session as a safety.
    @event.listens_for(_engine.sync_engine, "connect")
    def _on_connect(dbapi_connection, connection_record):
        try:
            # This uses a simple SQL command to set the timezone for the session.
            cursor = dbapi_connection.cursor()
            cursor.execute("SET TIME ZONE 'America/Bogota'")
            cursor.close()
        except Exception:
            # best-effort: if it fails (e.g., different DBAPI) ignore and rely on asyncpg server_settings
            pass

    # Create a session factory
    _async_session = sessionmaker( bind=_engine, class_=AsyncSession, autoflush=False, 
                                   expire_on_commit=False, future=True, autocommit=False
    )

    # Base class for defining models
    _base = declarative_base()

    @classmethod
    async def get_session(cls) -> AsyncGenerator[AsyncSession, None]:
        """
        Class method responsible for providing a database session.

        This method creates a new database session, yields it for use,
        and ensures proper cleanup by closing the session afterward.

        Yields:
            AsyncGenerator[Session, None]: A database async session.

        Raises:
            Exception: If an error occurs while managing the session.
        """

        async with cls._async_session() as session:
            try:
                yield session
            except InvalidCachedStatementError as err:
                await cls.dispose_engine()
            except DatabaseSQLAlchemyException:
                raise
            except Exception:
                raise
            finally:
                await session.close()

    @classmethod
    async def dispose_engine(cls):
        """
           Dispose and recreate the database engine and session.

           This method is called when the connection pool or prepared statements
           become invalid (e.g. after a database schema change).

           Raises:
               Exception: If the engine or session factory could not be recreated.
           """
        #Disposed the current engine
        await cls._engine.dispose()

        #Recreates engine and assign session
        # Recreate the engine preserving the server_settings so new connections
        # again set the session timezone to America/Bogota.
        cls._engine = create_async_engine(
            cls._db_url,
            echo=False,
            future=True,
            max_overflow=10,
            pool_size=5,
            connect_args={"server_settings": {"timezone": "America/Bogota"}},
        )
        @event.listens_for(cls._engine.sync_engine, "connect")
        def _on_connect_recreated(dbapi_connection, connection_record):
            try:
                cursor = dbapi_connection.cursor()
                cursor.execute("SET TIME ZONE 'America/Bogota'")
                cursor.close()
            except Exception:
                pass

        cls._async_session = sessionmaker(bind=cls._engine, class_=AsyncSession, autoflush=False,
                                   expire_on_commit=False, future=True, autocommit=False
        )

    @classmethod
    def create_all(cls) -> None:
        """
        Class method responsible for creating all database tables.

        This method initializes the database schema based on the defined models.

        Args:
            None

        Returns:
            None
        """

        cls._base.metadata.create_all(bind=cls._engine)

    @classmethod
    def base(cls) -> Any:
        """
        Class method responsible for returning the declarative base.

        This method provides access to the declarative base used for defining
        database models.

        Args:
            None

        Returns:
            Any: The declarative base instance.
        """

        return cls._base