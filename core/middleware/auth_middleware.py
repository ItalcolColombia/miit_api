from fastapi.security import HTTPBearer
from core.di.repository_injection import get_user_repository
from core.enums.user_role_enum import UserRoleEnum
from core.exceptions.base_exception import BasedException
from database.models import Usuarios
from utils.jwt_util import JWTUtil, JWTBearer
from repositories.usuarios_repository import UsuariosRepository
from schemas.usuarios_schema import VUsuariosRolResponse
from fastapi import Depends, status
from core.exceptions.auth_exception import InvalidCredentialsException, InvalidTokenCredentialsException
from typing import Annotated, Optional
from core.config.settings import get_settings
from core.config import context
from services.auth_service import AuthService

from utils.logger_util import LoggerUtil
log = LoggerUtil()

security = HTTPBearer()


async def get_current_user(
        token: Annotated[str, Depends(JWTBearer())],
        user_repository: UsuariosRepository = Depends(get_user_repository)
) -> VUsuariosRolResponse:
    """
    Retrieve the current authenticated user based on the provided JWT token.

    Args:
        token (Annotated[str, Depends(JWTBearer())]): The JWT token provided in the request.
        user_repository (UsuariosRepository): The repository for user-related database operations.

    Returns:
        Usuarios: The authenticated user object.

    Raises:
        InvalidTokenCredentialsException: If the token is invalid or the user is inactive.
        InvalidCredentialsException: If the user is not found.
        BasedException: For other unexpected errors.
    """
    try:
        # 1. Verificar y decodificar el token JWT
        payload = JWTUtil.verify_token(token)
        username: str = payload.get("sub")

        if username is None:
            raise InvalidTokenCredentialsException()

        if username != get_settings().API_USER_ADMINISTRATOR:
            # 2. Buscar el usuario en la base de datos
            user = await user_repository.get_by_username(username)

            # 3. Realizar validaciones al usuario
            if user is None:
                raise InvalidCredentialsException("Credenciales inválidas")

            if not user.estado:
                raise InvalidCredentialsException(
                    message="Usuario inactivo. Contacte al administrador.",
                    status_code=status.HTTP_403_FORBIDDEN
                )
            # Set user_id in context
            context.current_user_id.set(user.id)
            return user
        else:
            return AuthService.get_su()

    except InvalidTokenCredentialsException as e:
        raise e
    except InvalidCredentialsException as e:
        raise e
    except Exception as e:
        log.error(f"Error al validar usuario actual: {e}")
        raise InvalidTokenCredentialsException("Error inesperado al validar el token.")

def _check_rol(current_user: Usuarios, roles: list[str]):
    """
    Validate if the authenticated user has one of the required roles.

     Args:
         current_user (Usuarios): The authenticated user object.
         roles (list[str]): List with role names required to access to the endpoint.

     Raises:
         BasedException: If the user does not have the required roles or an unexpected error occurs.
    """
    try:
        if current_user.rol not in roles:
            raise BasedException(
                message="Acceso denegado, rol no autorizado para este recurso.",
                status_code=status.HTTP_403_FORBIDDEN
            )
    except BasedException as e:
        raise e
    except Exception as e:
        log.error(f"Error al verificar rol: {e}")
        raise BasedException(
            message=f"Error al verificar el rol del usuario {current_user.nick_name}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


async def _check_permiso(current_user: Usuarios, permission: str,
                         user_repo: UsuariosRepository = Depends(get_user_repository)):
    """
     Validate if the authenticated user has one of the required roles.

      Args:
          current_user (Usuarios): The authenticated user object.
          permission (str): The permission name required to access to the endpoint.
          user_repo (UsuariosRepository): The repository for user-related database operations.

      Raises:
          BasedException: If the user does not have the required roles or an unexpected error occurs.
    """
    try:
        permisos = await user_repo.get_rol_permission(rol_id=current_user.rol_id)
        permisos_nombres = [p.permiso for p in permisos]

        if permission not in permisos_nombres:
            raise BasedException(
                message=f"Acceso denegado, no cuenta con los permisos suficientes para este recurso.",
                status_code=status.HTTP_403_FORBIDDEN
            )
    except BasedException as e:
        raise e

    except Exception as e:
        log.error(f"Error en validación de permiso: {e}")
        raise BasedException(
            message="Error interno en validación de permisos",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def require_access(roles: list[str], permiso: Optional[str] = None):
    """
    Validate if the authenticated user has one of the required roles and the specify permission (optional).

    Args:
        *roles (list[str]): List with role names required to access the endpoint.
        permiso (str, optional): Name of specify permission.

    Returns:
        function: Dependency function that checks if the current user has one of the allowed roles and related permission.

    Raises:
        BasedException: If the user does not have the required roles and permission or an unexpected error occurs.
    """

    async def checker(current_user: Usuarios = Depends(get_current_user),
                      user_repo: UsuariosRepository = Depends(get_user_repository)
                      ):
        try:

            # Validación SU
            if current_user.rol == UserRoleEnum.SUPER_ADMINISTRATOR:
                return current_user

            else:
                # 1. Validar rol
                _check_rol(current_user, roles)

                # 2. Se consulta el permiso si este se especifica
                if permiso is not None:
                    await  _check_permiso(current_user, permiso, user_repo)

                return current_user

        except BasedException as e:
            raise e
        except Exception as e:
            log.error(f"Error en validación de acceso: {e}")
            raise BasedException(
                message="Error interno en validación de acceso del usuario",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    return checker