
from datetime import datetime, timezone


def utc_from_timestamp(timestamp: float) -> datetime:
    """
        Class responsible for handling timestamp generation.

        This class returns datetime with the timezone.

        Class Args:
            None
        """
    return datetime.fromtimestamp(timestamp, timezone.utc)