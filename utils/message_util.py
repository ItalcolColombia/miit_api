# /src/utils/message_util.py

from core.settings import Settings



class MessageUtil:
    """
    Class responsible for displaying API startup messages.

    This class formats and prints startup information about the API,
    including its name, version, and running host/port.

    Class Args:
        None
    """

    def __init__(self):
        """
        Constructor method for MessageUtil.

        Initializes the utility by loading API configurations.

        Args:
            None
        """

        self.__api_name = Settings().API_NAME
        self.__api_host = Settings().API_HOST
        self.__api_port = Settings().API_PORT
        self.__api_version = Settings().API_VERSION

    def on_startup(self):
        """
        Public method responsible for displaying API startup messages.

        This method prints a formatted banner with API details, including its
        name, version, and running URL.

        Args:
            None

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
        print(center_text(f"Version: {self.__api_version}"))
        print(
            center_text(
                f"Running on: {self.__api_host}:{self.__api_port}/api/{self.__api_version}"
            )
        )
        print(center_text(""))
        print(border + "\n")