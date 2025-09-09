from datetime import datetime
import random
from typing import Any, Optional, Dict
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import InstrumentedAttribute,ColumnProperty, RelationshipProperty

import bcrypt
from sqlalchemy.orm.base import class_mapper


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
        Convert a SQLAlchemy ORM object to a dictionary, optionally excluding specified fields.

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
            # Get the mapper for the object to inspect its columns and relationships
            mapper = class_mapper(type(obj))
            columns = [col.key for col in mapper.columns]

            # Build a dictionary with only serializable column data
            result = {}
            for column in columns:
                if hasattr(obj, column):
                    value = getattr(obj, column)
                    # Handle datetime objects
                    if hasattr(value, 'isoformat'):
                        value = value.isoformat()
                    # Handle JSON columns (already dict/list)
                    elif isinstance(value, (dict, list)):
                        value = value
                    # Skip relationships/lazy-loaded attributes to avoid session issues
                    elif not isinstance(value, (int, float, str, bool, type(None))):
                        value = str(value)  # Fallback to string representation
                    result[column] = value

            # Optionally include ID and other metadata
            if hasattr(obj, 'id'):
                result['id'] = obj.id

            return result
        except Exception as e:
            raise ValueError(f"Failed to serialize ORM object: {str(e)}")