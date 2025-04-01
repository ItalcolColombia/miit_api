# /src/core/enums/user_status_enum.py

from enum import Enum


class UserStatusEnum(str, Enum):
    """
    Enumerated class for user account status.

    This enum defines the possible states of a user account in the system.

    Class Args:
        None

    Members:
        ACTIVE (str): Represents an active user with full access.
        INACTIVE (str): Represents a user who has been deactivated and cannot access the system.
        SUSPENDED (str): Represents a user temporarily suspended due to policy violations or other reasons.
    """

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"