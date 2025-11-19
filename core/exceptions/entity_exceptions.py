from starlette import status

from core.exceptions.base_exception import BasedException


class EntityAlreadyRegisteredException(BasedException):
    """
       Class responsible for handling exceptions when an entity is found.

       This exception is raised when an contracts already exist in the database.

       Class Args:
           message (str): The error message describing the issue.
           status_code (int): The HTTP status code associated with the exception (default: 409 CONFLICT).
       """

    def __init__(self, entity_name: str):
        super().__init__(
            message=f'{entity_name} registrado en la base de datos.',
            status_code=status.HTTP_409_CONFLICT
        )


class EntityNotFoundException(BasedException):
    """
      Class responsible for handling exceptions when an entity is not found.

      This exception is raised when an contracts with an optional ID does not exist
      in the database.

      Class Args:
          entity_name (str): The name of the contracts that was not found.
          entity_id (int, optional): The unique identifier of the contracts (default: None).
      """
    def __init__(self, entity_name: str, entity_id: int | None = None):

        if entity_id is not None:
            message = f'{entity_name} con id {entity_id} no encontrada.'
        else:
            message = f'{entity_name} no encontrada.'

        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND
        )
