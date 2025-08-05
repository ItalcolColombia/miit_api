from typing import Optional

from core.di.repository_injection import get_user_repository
from core.enums.user_role_enum import UserRoleEnum
from core.exceptions.base_exception import BasedException
from database.models import Usuarios, RolesPermisos
from utils.jwt_util import JWTUtil, JWTBearer
from utils.any_utils import AnyUtils
from repositories.usuarios_repository import UsuariosRepository
from schemas.usuarios_schema import UsuariosResponse, VUsuariosRolResponse
from fastapi import Depends, status
from core.exceptions.auth_exception import InvalidCredentialsException, InvalidTokenCredentialsException
from typing import Annotated
from core.settings import get_settings

from utils.logger_util import LoggerUtil
log = LoggerUtil()

class AuthService:
    def __init__(self, user_repository: UsuariosRepository) -> None:
        self._user_repo = user_repository

    async def login(self, username: str, password: str) -> Optional[str]:
        """
        Authenticate a user and return a JWT token upon successful login.

        Args:
            username (str): The username provided for login.
            password (str): The password provided for login.

        Returns:
            Optional[str]: A JWT token if authentication is successful, None otherwise.

        Raises:
            InvalidCredentialsException: If the credentials are invalid.
            InvalidTokenCredentialsException: If the user is inactive.
            BasedException: For other unexpected errors.
        """
        try:
            if username != get_settings().API_USER_ADMINISTRATOR:
                user = await self._user_repo.get_by_username(username)

            else:
                user = AuthService.get_su()

            if not user or not self._verify_password(password, user.clave):
                log.info(f"Credenciales inválidas para {username}!")
                raise InvalidCredentialsException("Credenciales inválidas")

            if not user.estado:
                raise InvalidTokenCredentialsException(
                    message="Usuario inactivo",
                    status_code=status.HTTP_403_FORBIDDEN
                )

            return self.create_token(
                sub=user.nick_name,
                email=user.email,
                fullname=user.full_name,
                role=user.rol,
                is_active=user.estado
            )
        except InvalidCredentialsException as e:
            raise e
        except InvalidTokenCredentialsException as e:
            raise e
        except Exception as e:
            log.error(f"Error durante el login: {e}")
            raise BasedException(
                message=f"Error inesperado durante la autenticación {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @staticmethod
    def create_token(sub: str, email: Optional[str], fullname: str, role:  Optional[str], is_active: bool) -> Optional[str]:
        """
        Create a JWT token with the provided user data.

        Args:
            sub (str): The subject (usually username) for the token.
            email (Optional[str]): The user's email address.
            fullname (str): The user's full name.
            role (Optional[str]): The user's role.
            is_active (bool): The user's active status.

        Returns:
            Optional[str]: The generated JWT token, or None if creation fails.

        Raises:
            BasedException: If token creation fails.
        """
        try:
            token_data = {
                'sub': sub,
                'email': email,
                'fullname': fullname,
                'role': role,
                'is_active': is_active
            }
            return JWTUtil.create_token(token_data)
        except Exception as e:
            log.error(f"Error al formar el token: {e}")
            raise BasedException(
                message="Creación de token fallida",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    async def refresh_token(self, refresh_token: str) -> Optional[str]:
        """
            Refresh a JWT token using a provided refresh token.

            Args:
                refresh_token (str): The refresh token to validate and use for generating a new token.

            Returns:
                Optional[str]: A new JWT token if refresh is successful, None otherwise.

            Raises:
                BasedException: If token refresh fails.
        """
        try:
            # 1. Verificar y decodificar el token de refresco
            payload = JWTUtil.verify_token(refresh_token)
            if not payload:
                log.info("Token de refresco inválido o expirado")
                return None

            username = payload.get("sub")

            # 2. Obtener la información del usuario
            if username != get_settings().API_USER_ADMINISTRATOR:
                user = await self._user_repo.get_by_username(username)
            else:
                user = AuthService.get_su()

            # 3. Si no se obtiene se retorna vacío
            if not user:
                log.warning(f"No se encontró información del usuario para generar el token {username}")
                return None

            # 4. Se forma y crea el token
            token_data = {
                'sub': user.nick_name,
                'email': user.email,
                'fullname': user.full_name,
                'role': user.rol,
                'is_active': user.estado
            }

            return JWTUtil.create_refresh_token(token_data)

        except InvalidTokenCredentialsException as e:
            raise e
        except Exception as e:
            log.error(f"Error durante el refresco del token: {e}")
            raise BasedException(
                message=f"Refresco del fallído {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _verify_email(self, email: str) -> Optional[UsuariosResponse]:
        """
        Check if an email exists in the database.

        Args:
            email (str): The email address to check.

        Returns:
            Optional[UsuariosResponse]: The user instance if found, otherwise None.

        Raises:
            BasedException: If an unexpected error occurs during email verification.
        """
        try:
            user = self._user_repo.get_by_email(email)
            return user if user else None
        except Exception as e:
            log.error(f"Error verificando email {email}: {e}")
            raise BasedException(
                message="Error al verificar el email",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @staticmethod
    def _verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify if the provided password matches the stored hashed password.

        Args:
            plain_password (str): The password provided in the login request.
            hashed_password (str): The hashed password stored in the database.

        Returns:
            bool: True if the passwords match, otherwise False.

        Raises:
            BasedException: If an unexpected error occurs during password verification.
        """
        try:
            return AnyUtils.check_password_hash(plain_password, hashed_password)
        except Exception as e:
            log.error(f"Error al verificar la contraseña: {e}")
            raise BasedException(
                message="Error al verificar la contraseña",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @staticmethod
    async def get_current_user(
            token: Annotated[str, Depends(JWTBearer())],
            user_repository: UsuariosRepository = Depends(get_user_repository)
    ) -> Usuarios:
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

    @staticmethod
    def get_su() -> VUsuariosRolResponse:
        return VUsuariosRolResponse(
            nick_name=get_settings().API_USER_ADMINISTRATOR,
            full_name='SysAdmin',
            cedula=99999999,
            email='admin@metalteco.com',
            clave=get_settings().API_PASSWORD_ADMINISTRATOR,
            rol_id=99,
            rol=UserRoleEnum.SUPER_ADMINISTRATOR,
            recuperacion=None,
            estado=True,
            estado_rol=True
        )

    @staticmethod
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

    @staticmethod
    async def _check_permiso(current_user: Usuarios, permission: str, user_repo: UsuariosRepository = Depends(get_user_repository)):
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


    @staticmethod
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

        async def checker(current_user: Usuarios = Depends(AuthService.get_current_user),
                          user_repo: UsuariosRepository = Depends(get_user_repository)
        ):
            try:

                #Validación SU
                if current_user.rol == UserRoleEnum.SUPER_ADMINISTRATOR:
                    return  current_user

                else:
                    # 1. Validar rol
                    AuthService._check_rol(current_user, roles)

                    # 2. Se consulta el permiso si este se especifica
                    if permiso is not None:
                       await  AuthService._check_permiso(current_user,permiso, user_repo)

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