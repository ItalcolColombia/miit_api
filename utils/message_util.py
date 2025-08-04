from starlette import status

from core.exceptions.base_exception import BasedException
from core.settings import get_settings

from utils.logger_util import LoggerUtil
log = LoggerUtil()

class MessageUtil:
    """
    Class responsible for displaying API startup messages.

    This class formats and prints startup information about the API,
    including its name, version, and running host/port.

    Class Args:
        None

    Attributes:
        __api_name (str): The name of the API from settings.
        __api_host (str): The host address of the API from settings.
        __api_port (int): The port number of the API from settings.
        __api_version (str): The version of the API from settings.
    """

    def __init__(self):
        """
        Constructor method for MessageUtil.

        Initializes the utility by loading API configurations.

        Args:
        None
        Raises:
            BasedException: If initialization fails due to invalid or missing configuration settings.
        """
        try:
            self.__api_name = get_settings().API_NAME
            self.__api_host = get_settings().API_HOST
            self.__api_port = get_settings().API_PORT
            self.__api_version = get_settings().API_VERSION
            self.__api_str_version = get_settings().API_V1_STR
        except Exception as e:
            log.error(f"Error en message_util: {e}")
            raise BasedException(
                message=f"Error en message_util: {e}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def on_startup(self):
        """
        Public method responsible for displaying API startup messages.

        This method prints a formatted banner with API details, including its
        name, version, and running URL.


        Returns:
            None
        """

        width = 80
        border = "=" * width

        def center_text(text):
            """
            Helper function to center text within the formatted message.

            Args:
                text (str): The text to be centered.

            Returns:
                str: The formatted string with centered text.
            """

            return f"|{text.center(width - 2)}|"

        print("\n" + border)
        print(center_text(""))
        print(center_text(f"API: {self.__api_name}"))
        print(center_text(f"Version: {self.__api_str_version} Release: {self.__api_version}"))
        print(
            center_text(
                f"Running on: {self.__api_host}:{self.__api_port}/api/{self.__api_str_version}"
            )
        )
        print(center_text(""))
        print(border + "\n")