from datetime import datetime
from passlib.context import CryptContext
from passlib.hash import bcrypt
import random

# Create a CryptContext for password hashing
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)

class AnyUtils:

    """
    Class responsible for providing utility functions.

    This class contains static methods for generating formatted timestamps, unique IDs,
    password hashing, and password verification.

    Class Args:
        None
    """


    @staticmethod
    def generate_formatted_datetime() -> str:
        """
        Static method responsible for generating a formatted timestamp.

        This method generates a timestamp formatted as `%y-%m-%d %H:%M:%S`
        for database storage.

        Args:
            None

        Returns:
            str: The formatted timestamp.
        """

        now = datetime.now()
        formatted_datetime = now.strftime("%d-%m-%Y %H:%M:%S")
        return formatted_datetime

    @staticmethod
    def generate_unique_id() -> str:
        """
        Static method responsible for generating a unique ID.

        This method generates a unique identifier using the current date-time
        and a randomly generated hexadecimal value.

        Args:
            None

        Returns:
            str: The generated unique ID.
        """

        now = datetime.now()
        sorted_value = random.randint(0, 0xFFFF)
        hex_value = f"{sorted_value:04X}"
        date_time_now = now.strftime("%d%m%Y%H%M%S")
        return date_time_now + hex_value

    @staticmethod
    def generate_password_hash(password: str) -> str:
        """
        Static method responsible for hashing a password.

        This method hashes a given password using the PBKDF2-SHA256 algorithm.

        Args:
            password (str): The plain-text password to hash.

        Returns:
            str: The hashed password.
        """

        return pwd_context.hash(password)

    @staticmethod
    def check_password_hash(plain_password: str, hashed_password: str) -> bool:
        """
        Static method responsible for verifying a password.

        This method checks if a provided password matches a stored hashed password.

        Args:
            plain_password (str): The plain-text password entered by the user.
            hashed_password (str): The hashed password stored in the database.

        Returns:
            bool: True if the passwords match, otherwise False.
        """
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except ValueError as ve:
            raise ValueError(f"Password verification failed: {ve}")
