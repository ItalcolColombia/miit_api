import random
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict

import bcrypt
import orjson
from sqlalchemy.orm.base import class_mapper

from utils.time_util import format_iso_bogota


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
    def generate_password_hash(plain_password: str) -> str:
        """
        Static method responsible for hashing a password.

        This method hashes a given password using the PBKDF2-SHA256 algorithm.

        Args:
            plain_password (str): The plain-text password to hash.

        Returns:
            str: The hashed password.
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

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
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except ValueError as ve:
            raise ValueError(f"Password verification failed: {ve}")

    @staticmethod
    def serialize_orm_object(obj: Any) -> dict | None:
        """
        Serialize a SQLAlchemy ORM object to a JSON-serializable dictionary.

        Args:
            obj: The SQLAlchemy ORM object to serialize.

        Returns:
            Dict | None: A dictionary representation of the ORM object | None.

        Raises:
            ValueError: If serialization fails due to an invalid object or unhandled exception.
        """
        if obj is None:
            return None

        try:
            # Build a dictionary with only serializable column data
            result = {}

            # Get the mapper for the object to inspect its columns and relationships
            mapper = class_mapper(type(obj))
            columns = [col.key for col in mapper.columns]

            for column in columns:
                if hasattr(obj, column):
                    value = getattr(obj, column)
                    if isinstance(value, datetime):
                        result[column] = format_iso_bogota(value)
                    elif isinstance(value, Decimal):
                        result[column] = str(value)
                    elif isinstance(value, (dict, list)):
                        result[column] = value
                    elif isinstance(value, (int, float, str, bool)) or value is None:
                        result[column] = value
                    else:
                        result[column] = str(value)
            return result
        except Exception as e:
            raise ValueError(f"Failed to serialize ORM object: {str(e)}")

    @staticmethod
    def serialize_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure data is JSON-serializable."""

        def convert(obj):
            if isinstance(obj, datetime):
                return format_iso_bogota(obj)
            if isinstance(obj, Decimal):
                return str(obj)  # Convert Decimal to string to preserve precision
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        return orjson.loads(orjson.dumps(data, default=convert))

    @staticmethod
    def serialize_dict(data: Dict[str, Any] | None) -> Dict[str, Any] | None:
        """
        Serialize a dictionary to a JSON-serializable format, handling specific types.

        Args:
            data: The dictionary containing column names and values to serialize, or None.

        Returns:
            Dict | None: A JSON-serializable dictionary with processed values, or None if input is None.

        Raises:
            ValueError: If serialization fails due to an unhandled type or exception.
        """
        if data is None:
            return None

        try:
            result = {}
            for key, value in data.items():
                if isinstance(value, datetime):
                    result[key] = format_iso_bogota(value)  # Convert datetime to ISO string
                elif isinstance(value, Decimal):
                    result[key] = str(value)  # Convert Decimal to string
                elif isinstance(value, (dict, list)):
                    result[key] = value  # Keep JSON-compatible types as-is
                elif isinstance(value, (int, float, str, bool, )) or value is None:
                    result[key] = value  # Keep primitive types as-is
                else:
                    result[key] = str(value)  # Fallback to string for other types
            return result
        except Exception as e:
            raise ValueError(f"Failed to serialize dictionary: {str(e)}")