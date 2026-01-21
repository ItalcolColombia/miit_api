from typing import List, Optional

from fastapi_pagination import Page, Params
from sqlalchemy import func
from starlette import status

from core.exceptions.base_exception import BasedException
from core.exceptions.entity_exceptions import (
    EntityAlreadyRegisteredException,
)
from repositories.usuarios_repository import UsuariosRepository
from schemas.usuarios_schema import UsuariosResponse, UsuarioCreate, UsuarioUpdate
from utils.any_utils import AnyUtils
from utils.logger_util import LoggerUtil

log = LoggerUtil()

class UsuariosService:

    def __init__(self, usuario_repository: UsuariosRepository) -> None:
        self._repo = usuario_repository

    async def validate_username(self, username: str) -> None:
        """
        Validate if a username is already registered.

        Args:
            username (str): The username to check for existence.

        Raises:
            EntityAlreadyRegisteredException: If the username is already registered.
            BasedException: If validation fails due to unexpected errors.
        """
        try:
            if await self.get_username(username):
                raise EntityAlreadyRegisteredException(f"Usuario '{username}' ya se encuentra registrado")
        except EntityAlreadyRegisteredException as e:
            raise e
        except Exception as e:
            log.error(f"Error validando nombre de usuario {username}: {e}")
            raise BasedException(
                message=f"Error al validar el nombre de usuario {username}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_username(self, username: str) -> Optional[UsuariosResponse]:
        """
        Retrieve a user by their username.

        Args:
            username (str): The username to search for.

        Returns:
            Optional[UsuariosResponse]: The user object if found, or None if not found.

        Raises:
            BasedException: If retrieval fails due to unexpected errors.
        """
        try:
            user = await self._repo.get_by_username(username)
            # repo returns None when not found; propagate None so callers can handle absence
            return user
        except Exception as e:
            log.error(f"Error obteniendo usuario con nombre {username}: {e}")
            raise BasedException(
                message=f"Error al obtener el usuario con nombre {username}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_user(self, usr_id: int) -> Optional[UsuariosResponse]:
        """
        Retrieve a user by their ID.

        Args:
            usr_id (int): The ID of the user to retrieve.

        Returns:
            Optional[UsuariosResponse]: The user object if found, None otherwise.

        Raises:
            BasedException: If retrieval fails due to database or other errors.
        """
        try:
            return await self._repo.get_by_id(usr_id)
        except Exception as e:
            log.error(f"Error obteniendo usuario con ID {usr_id}: {e}")
            raise BasedException(
                message=f"Error al obtener el usuario con ID {usr_id}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_all_users(self) -> List[UsuariosResponse]:
        """
        Retrieve all users from the database.

        Returns:
            List[UsuariosResponse]: A list of all user objects.

        Raises:
            BasedException: If retrieval fails due to database or other errors.
        """
        try:
            return await self._repo.get_all()
        except Exception as e:
            log.error(f"Error obteniendo todos los usuarios: {e}")
            raise BasedException(
                message="Error al obtener todos los usuarios",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_paginated_users(self, params: Params = Params()) -> Page[UsuariosResponse]:
        """
        Retrieve a paginated list of users.

        Args:
            params (Params): Pagination parameters.

        Returns:
            Page[UsuariosResponse]: A paginated list of user objects.

        Raises:
            BasedException: If retrieval fails due to database or other errors.
        """
        try:
            return await self._repo.get_all_paginated(params=params)
        except Exception as e:
            log.error(f"Error obteniendo usuarios paginados: {e}")
            raise BasedException(
                message="Error al obtener usuarios paginados",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def create_user(self, user: UsuarioCreate, user_id : int) -> UsuariosResponse:
        """
        Create a new user in the database.

        Args:
            user (UsuarioCreate): The user data to create, including username and password.
            user_id (int): The ID of the user performing the creation, extracted from JWT.

        Returns:
            UsuariosResponse: The created user object.

        Raises:
            EntityAlreadyRegisteredException: If the username is already registered.
            BasedException: If creation fails due to database or other errors.
        """
        try:
            # Validar longitud de nick_name para evitar errores de truncamiento en BD
            if user.nick_name and len(user.nick_name) > 10:
                raise BasedException(
                    message=f"El campo 'nick_name' excede la longitud máxima permitida de 10 caracteres",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            # Validar si el usuario existe
            await self.validate_username(user.nick_name)

            # Hashear la contraseña
            user.clave = AnyUtils.generate_password_hash(user.clave)
            user.fecha_hora = func.now()
            user.usuario_id = user_id


            # Crear el usuario
            return await self._repo.create(user)
        except EntityAlreadyRegisteredException as e:
            raise e
        except BasedException as e:
            # Re-raise BasedException para que el manejador global lo procese con el status_code correcto
            raise e
        except Exception as e:
            log.error(f"Error creando usuario con nombre {user.nick_name}: {e}")
            raise BasedException(
                message=f"Error al crear el usuario con nombre {user.nick_name}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def update_user(self, usr_id: int, user: UsuarioUpdate) -> Optional[UsuariosResponse]:
        """
        Update an existing user by ID.

        Args:
            usr_id (int): The ID of the user to update.
            user (UsuarioUpdate): The updated user data.

        Returns:
            Optional[UsuariosResponse]: The updated user object, or None if not found.

        Raises:
            BasedException: If update fails due to database or other errors.
        """
        try:
            return await self._repo.update(usr_id, user)
        except Exception as e:
            log.error(f"Error actualizando usuario con ID {usr_id}: {e}")
            raise BasedException(
                message=f"Error al actualizar el usuario con ID {usr_id}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def delete_user(self, usr_id: int) -> bool:
        """
        Delete a user by ID.

        Args:
            usr_id (int): The ID of the user to delete.

        Returns:
            bool: True if deletion was successful, False otherwise.

        Raises:
            BasedException: If deletion fails due to database or other errors.
        """
        try:
            return await self._repo.delete(usr_id)
        except Exception as e:
            log.error(f"Error eliminando usuario con ID {usr_id}: {e}")
            raise BasedException(
                message=f"Error al eliminar el usuario con ID {usr_id}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )