# /src/contracts/dot_env_util.py


from dotenv import find_dotenv


class DotEnvUtil:
    """
    Class responsible for handling `.env` file operations.

    This class provides methods to check whether the `.env` file is loaded or if
    the system is using default environment variables.

    Class Args:
        None
    """

    def __init__(self):
        """
        Constructor method for DotEnvUtil.

        Initializes the utility by locating the `.env` file path.

        Args:
        None
        """

        self.__env_path = find_dotenv()

    def check_dot_env(self) -> None:
        """
        Public method responsible for verifying if the `.env` file is loaded.

        This method checks for the presence of the `.env` file and prints a message
        indicating whether it was successfully loaded or if default environment
        variables are being used.

        Args:
        None

        Returns:
            None
        """

        additional_message = "ENV VARIABLES -> "

        if not self.__env_path:
            message = f"\n\033[32m\033[1m{additional_message}The environment variables are not set! ... running with default env variables\033[0m"
            print(message)
        else:
            message = f"\n\033[32m\033[1m{additional_message}The environment variables are set!\033[0m"
            print(message)