
from enum import Enum


class UserPermissionEnum(str, Enum):
    """
    Enumerated class for user permissions.

    This enum defines the possible actions that a user can perform in the system.

    Class Args:
        None

    Members:
        CREATE (str): Permission to create new resources.
        READ (str): Permission to read/view existing resources.
        UPDATE (str): Permission to update or modify resources.
        DELETE (str): Permission to delete resources.
    """

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"