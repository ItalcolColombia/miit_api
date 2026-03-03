# /src/contracts/console_logger_util.py

import logging
import os
import sys
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

from colorlog import ColoredFormatter
from starlette import status

from core.config.settings import get_settings
from core.exceptions.base_exception import BasedException


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

            # Determinar la ruta de logs inteligentemente
            _log_dir = self._get_log_directory()
            os.makedirs(_log_dir, exist_ok=True)

            # Nombre base del archivo de log (sin fecha, ya que TimedRotatingFileHandler la añade)
            _log_file_base = os.path.join(_log_dir, f"{self.__api_name}.log")

            # También crear archivo con fecha actual para referencia inmediata
            log_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            _log_file_dated = os.path.join(_log_dir, f"{self.__api_name}_{log_date}.log")

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

            # File formatter setup - formato más detallado para archivos
            _file_format = "%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
            _file_formatter = logging.Formatter(_file_format, datefmt=_date_format)

            # Initialize the logger
            self.__logger = logging.getLogger()

            if not self.__logger.hasHandlers():
                _level = self.__get_log_level_variable()

                # TimedRotatingFileHandler - crea un nuevo archivo cada día a medianoche
                _timed_handler = TimedRotatingFileHandler(
                    _log_file_base,
                    when='midnight',
                    interval=1,
                    backupCount=30,  # Mantener logs de los últimos 30 días
                    encoding='utf-8'
                )
                _timed_handler.suffix = "_%Y-%m-%d.log"
                _timed_handler.setFormatter(_file_formatter)
                _timed_handler.setLevel(logging.DEBUG)

                # RotatingFileHandler adicional para el archivo con fecha actual
                _file_handler = RotatingFileHandler(
                    _log_file_dated,
                    maxBytes=50*1024*1024,  # 50 MB
                    backupCount=5,
                    encoding='utf-8'
                )
                _file_handler.setFormatter(_file_formatter)
                _file_handler.setLevel(logging.DEBUG)

                # Console handler
                _stream_handler = logging.StreamHandler(sys.stdout)
                _stream_handler.setFormatter(_stream_formatter)
                _stream_handler.setLevel(logging.DEBUG)

                self.__logger.setLevel(_level)
                self.__logger.addHandler(_timed_handler)
                self.__logger.addHandler(_file_handler)
                self.__logger.addHandler(_stream_handler)

                # Log inicial indicando dónde se guardan los logs
                self.__logger.info(f"="*60)
                self.__logger.info(f"Sistema de logging inicializado")
                self.__logger.info(f"Directorio de logs: {_log_dir}")
                self.__logger.info(f"Archivo de log actual: {_log_file_dated}")
                self.__logger.info(f"Nivel de log: {_level}")
                self.__logger.info(f"="*60)

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

    def _get_log_directory(self) -> str:
        """
        Determina el directorio de logs a utilizar.

        Prioridad:
        1. APP_LOG_DIR configurado en settings (si existe y es accesible)
        2. Carpeta 'logs/miit_api' relativa al proyecto (para desarrollo local)

        Returns:
            str: La ruta del directorio de logs a utilizar.
        """
        configured_dir = self.__app_log_dir

        # Intentar usar el directorio configurado
        if configured_dir:
            try:
                # En Windows, verificar si la ruta es de estilo Unix (no válida)
                if os.name == 'nt' and configured_dir.startswith('/'):
                    # Ruta de estilo Unix en Windows - usar fallback
                    pass
                else:
                    # Verificar si el directorio padre existe o se puede crear
                    os.makedirs(configured_dir, exist_ok=True)
                    # Verificar si podemos escribir en el directorio
                    test_file = os.path.join(configured_dir, '.write_test')
                    with open(test_file, 'w') as f:
                        f.write('test')
                    os.remove(test_file)
                    return configured_dir
            except (OSError, PermissionError, FileNotFoundError):
                # No se puede usar el directorio configurado
                pass

        # Usar directorio relativo al proyecto (desarrollo local)
        # Obtener la raíz del proyecto (dos niveles arriba de utils/)
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        local_log_dir = os.path.join(project_root, 'logs', 'miit_api')

        return local_log_dir


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

    def flush(self) -> None:
        """
        Fuerza la escritura de los logs pendientes al disco.

        Returns:
            None
        """
        for handler in self.__logger.handlers:
            handler.flush()

    def get_log_directory(self) -> str:
        """
        Retorna el directorio donde se guardan los logs.

        Returns:
            str: Ruta del directorio de logs.
        """
        return self._get_log_directory()

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



