from enum import Enum


class UserRoleEnum(str, Enum):
    """
    Enumerated class for user roles.

    This enum defines the different user roles available in the system.

    Class Args:
        None

    Members:
        SUPER_ADMINISTRATOR (str): Represents a super administrator with the highest level of access.
        ADMINISTRATOR (str): Represents an administrator with elevated privileges.
        DEFAULT (str): Represents a standard user with basic access rights.
    """

    SUPER_ADMINISTRATOR = "super_administrator"
    ADMINISTRATOR = "administrator"
    DEFAULT = "default"