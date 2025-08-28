# /src/contracts/console_logger_util.py

import logging
import os

from colorlog import ColoredFormatter
from starlette import status

from core.exceptions.base_exception import BasedException
from core.config.settings import get_settings


class LoggerUtil:
    """
    Class responsible for configuring and managing the application logging.

    This class sets up a logger that writes logs to both a console (with colors)
    and a log file. The log level can be determined from an environment variable.
    It also supports logging to a database for persistent storage.

    Class Args:
        None


    Attributes:
        __api_name (str): The name of the API from settings.
        __api_log_level (str): The configured log level (e.g., DEBUG, INFO).
        __app_log_dir (str): The directory for storing log files.
        __valid_log_levels (list): List of valid log levels.
        __logger (logging.Logger): The configured logger instance.
    """

    def __init__(self):
        """
        Initialize the LoggerUtil with file and console handlers.

        Configures the logger with a file handler for persistent logs and a console handler
        with colored output. The log level is set based on configuration settings.

        Args:
        None

        Raises:
            BasedException: If logger initialization fails due to invalid configuration or file access issues.
        """
        try:
            self.__api_name = get_settings().API_NAME
            self.__api_log_level = get_settings().API_LOG_LEVEL
            self.__app_log_dir = get_settings().APP_LOG_DIR
            self.__valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

            # Directory and path for the log file
            _project_root = os.path.abspath(os.path.dirname(__file__))
            _log_dir = self.__app_log_dir
            os.makedirs(_log_dir, exist_ok=True)

            _log_file_name = f"{self.__api_name}.log"
            _log_file = os.path.join(_log_dir, _log_file_name)

            # Console format and message format
            _date_format = "%d-%m-%Y | %H:%M:%S"
            _stream_format = "%(asctime)s - %(log_color)s%(levelname)s%(reset)s - %(message)s"
            _log_colors = {
                "DEBUG": "blue",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            }

            # Console (stream) formatter setup
            _stream_formatter = ColoredFormatter(
                _stream_format, datefmt=_date_format, log_colors=_log_colors
            )

            # File formatter setup
            _file_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            _file_formatter = logging.Formatter(_file_format, datefmt=_date_format)

            # Initialize the logger
            self.__logger = logging.getLogger()

            if not self.__logger.hasHandlers():
                _level = self.__get_log_level_variable()

                # File handler and console handler configuration
                _file_handler = logging.FileHandler(_log_file)
                _file_handler.setFormatter(_file_formatter)

                _stream_handler = logging.StreamHandler()
                _stream_handler.setFormatter(_stream_formatter)

                self.__logger.setLevel(_level)
                self.__logger.addHandler(_file_handler)
                self.__logger.addHandler(_stream_handler)

                if _level != "DEBUG":
                    logging.getLogger("uvicorn.access").disabled = True
                    logging.getLogger("uvicorn.error").disabled = True
                    logging.getLogger("uvicorn").disabled = True
                    logging.getLogger("uvicorn").propagate = False
                    logging.getLogger("apscheduler").disabled = True
                    logging.getLogger("apscheduler").propagate = False

        except Exception as e:
            logging.getLogger().error(f"Error al inicializar LoggerUtil: {e}")
            raise BasedException(
                message=f"Error en logging_util: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    # def _log_to_db(self, level: str, message: str, resource: Optional[str] = None):
    #     """
    #            Log a message to the database.
    #
    #            Stores a log entry in the database with the specified level, message, and optional resource.
    #
    #            Args:
    #                level (str): The log level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL).
    #                message (str): The log message to store.
    #                resource (Optional[str]): The resource associated with the log, if any. Defaults to None.
    #
    #            Returns:
    #                None
    #     """
    #     db: AsyncSession = AsyncSession()
    #     try:
    #         db_log = Log(level=level, message=message, resource=resource, timestamp=datetime.now(timezone.utc))
    #         db.add(db_log)
    #         db.commit()
    #     except Exception as e:
    #         self.__logger.error(f"Error al escribir log en la base de datos: {e}")
    #         db.rollback()
    #     finally:
    #         db.close()

    def info(self, message: str) -> None:
        """
        Log an INFO level message.

        Args:
            message (str): The message to be logged.

        Returns:
            None

        Raises:
            BasedException: If logging fails due to unexpected errors.
        """
        try:
            self.__logger.info(message)
        except Exception as e:
            self.__logger.error(f"Error al registrar mensaje INFO: {e}")
            raise BasedException(
                message="Error inesperado al registrar mensaje INFO.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def error(self, message: str, exc_info: bool = False) -> None:
        """
        Log an ERROR level message.

        Args:
            message (str): The message to be logged.
            exc_info (bool): Whether to include exception traceback information. Defaults to False.

        Returns:
            None
        """
        try:
            self.__logger.error(message, exc_info=exc_info)
        except Exception as e:
            self.__logger.error(f"Error al registrar mensaje ERROR: {e}")

    def debug(self, message: str) -> None:
        """
        Log a DEBUG level message.

        Args:
            message (str): The message to be logged.

        Returns:
            None

        Raises:
            BasedException: If logging fails due to unexpected errors.
        """
        try:
            self.__logger.debug(message)
        except Exception as e:
            self.__logger.error(f"Error al registrar mensaje DEBUG: {e}")

    def warning(self, message: str) -> None:
        """
        Log a WARNING level message.

        Args:
            message (str): The message to be logged.

        Returns:
            None
        """
        try:
            self.__logger.warning(message)
        except Exception as e:
            self.__logger.error(f"Error al registrar mensaje WARNING: {e}")

    def __get_log_level_variable(self) -> str:
        """
        Retrieve the log level from configuration.

        Retrieves the log level from the `API_LOG_LEVEL` setting. If the value is missing or invalid,
        defaults to 'INFO' and logs a warning.

        Args:
        None

        Returns:
            str: The log level ('DEBUG', 'INFO', 'WARNING', 'ERROR', or 'CRITICAL').
        """
        try:
            default_level = "INFO"
            obtained_log_level = self.__api_log_level.upper()

            if not obtained_log_level:
                self.__logger.warning(
                    f"Empty or invalid 'LOG_LEVEL' value found. Using default value '{default_level}'."
                )
                return default_level

            if obtained_log_level not in self.__valid_log_levels:
                self.__logger.warning(
                    f"Invalid value for 'LOG_LEVEL' found: {self.__api_log_level}. Using default value '{default_level}'."
                )
                return default_level

            return obtained_log_level
        except Exception as e:
            self.__logger.error(f"Error al obtener el nivel de log: {e}")



