from core.exceptions.base_exception import BaseException

class EntityAlreadyRegisteredException(BaseException):
    """
       Class responsible for handling exceptions when an entity is not found.

       This exception is raised when an entity does not exist in the database.

       Class Args:
           message (str): The error message describing the issue.
           status_code (int): The HTTP status code associated with the exception (default: 404 Not Found).
       """

    def __init__(self, entity_name: str):
        super().__init__(
            message=f'{entity_name} registrado en la base de datos.',
            status_code=400
        )


class EntityNotFoundException(BaseException):
    """
      Class responsible for handling exceptions when an entity is not found.

      This exception is raised when an entity with a specific ID does not exist
      in the database.

      Class Args:
          entity_name (str): The name of the entity that was not found.
          entity_id (int, optional): The unique identifier of the entity (default: None).
      """
    def __init__(self, entity_name: str, entity_id: int | None = None):

        if entity_id is not None:
            message = f'{entity_name} con id {entity_id} no encontrada.'
        else:
            message = f'{entity_name} no encontrada.'

        super().__init__(message=message, status_code=404)
