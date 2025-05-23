# /src/utils/console_logger_util.py

import logging
import os

from colorlog import ColoredFormatter
from database.connection import AsyncSession 
from core.settings import Settings


class LoggerUtil:
    """
    Class responsible for configuring and managing the application logging.

    This class sets up a logger that writes logs to both a console (with colors)
    and a log file. The log level can be determined from an environment variable.

    Class Args:
        None
    """

    def __init__(self):
        """
        Constructor method for LoggerUtil.

        Initializes and configures the logger with file and console handlers.

        Args:
            None
        """

        self.__api_name = Settings().API_NAME
        self.__api_log_level = Settings().API_LOG_LEVEL
        self.__app_log_dir = Settings().APP_LOG_DIR

        self.__valid_log_levels = [
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
        ]

        # Directory and path for the log file
        _project_root = os.path.abspath(os.path.dirname(__file__))
        #_log_dir = os.path.join(_project_root, "/logs")
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


    def _log_to_db(self, level: str, message: str, resource: str = None):
        db: AsyncSession = AsyncSession()
        try:
            db_log = Log(level=level, message=message, resource=resource, timestamp=datetime.utcnow())
            db.add(db_log)
            db.commit()
        except Exception as e:
            self.logger.error(f"Error al escribir log en la base de datos: {e}")
            db.rollback()
        finally:
            db.close()


    def info(self, message: str) -> None:
        """
        Public method responsible for logging an 'INFO' level message.

        Args:
            message (str): The message to be logged.

        Returns:
            None
        """

        self.__logger.info(message)

    def error(self, message: str) -> None:
        """
        Public method responsible for logging an 'ERROR' level message.

        Args:
            message (str): The message to be logged.
            exc_info (bool): The boolean value to pass trace exception.

        Returns:
            None
        """

        self.__logger.error(message)

    def debug(self, message: str) -> None:
        """
        Public method responsible for logging a 'DEBUG' level message.

        Args:
            message (str): The message to be logged.

        Returns:
            None
        """

        self.__logger.debug(message)

    def warning(self, message: str) -> None:
        """
        Public method responsible for logging a 'WARNING' level message.

        Args:
            message (str): The message to be logged.

        Returns:
            None
        """

        self.__logger.warning(message)

    def __get_log_level_variable(self) -> str:
        """
        Private method responsible for obtaining the log level from the configuration.

        This method retrieves the log level from the `api_log_level` variable.
        If the value is missing or invalid, it defaults to 'INFO'.

        Args:
            None

        Returns:
            str: The log level ('DEBUG', 'INFO', 'WARNING', 'ERROR', or 'CRITICAL').
        """

        default_level = "INFO"
        obtained_log_level = self.__api_log_level.upper()

        yellow = "\033[33m"
        reset = "\033[0m"

        if not obtained_log_level:
            print(
                f"{yellow}Empty or invalid ‘LOG_LEVEL’ value found. Using default value '{default_level}'!{reset}"
            )
            return default_level

        if obtained_log_level not in self.__valid_log_levels:
            print(
                f"{yellow}Invalid value for 'LOG_LEVEL' found: {self.__api_log_level}! Using the default value '{default_level}{reset}!"
            )
            return default_level

        return obtained_log_level