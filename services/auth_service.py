from typing import Optional

from core.di.repository_injection import get_user_repository
from core.exceptions.base_exception import BasedException
from database.models import Usuarios
from utils.jwt_util import JWTUtil, JWTBearer
from utils.any_utils import AnyUtils
from repositories.usuarios_repository import UsuariosRepository
from schemas.usuarios_schema import UsuariosResponse
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
                    role=user.rol_nombre,
                    is_active=user.estado
                )
            else:
                if not self._verify_password(password, get_settings.API_PASSWORD_ADMINISTRATOR):
                    raise InvalidCredentialsException("Credenciales inválidas para superadmin")

                return self.create_token(
                    sub='superadmin',
                    email='admin@metalteco.com',
                    fullname='SysAdmin',
                    role='SuperAdministrador',
                    is_active=True
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
            payload = JWTUtil.verify_token(refresh_token)
            if not payload:
                log.info("Token de refresco inválido o expirado")
                return None

            username = payload.get("sub")
            user = await self._user_repo.get_by_username(username)
            if not user:
                log.info(f"Usuario no encontrado para el token: {username}")
                return None

            token_data = {
                'sub': user.nick_name,
                'email': user.email,
                'fullname': user.full_name,
                'role': user.rol_nombre,
                'is_active': user.estado
            }

            return JWTUtil.create_refresh_token(token_data)
        except Exception as e:
            log.error(f"Error refreshing token: {e}")
            raise BasedException(
                message="Refrescado de token fallido",
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

        except InvalidTokenCredentialsException as e:
            raise e
        except InvalidCredentialsException as e:
            raise e
        except Exception as e:
            log.error(f"Error al validar usuario actual: {e}")
            raise InvalidTokenCredentialsException("Error inesperado al validar el token.")

    async def get_current_super_user(self: Usuarios = Depends(get_current_user)) -> Usuarios:
        """
        Verify if the current user is a superuser (rol_id == 4).

        Args:
            self (Usuarios): The authenticated user object from get_current_user.

        Returns:
            Usuarios: The authenticated superuser object.

        Raises:
            BasedException: If the user does not have sufficient permissions.
        """
        try:
            if not self.rol_id == 4:
                raise BasedException(
                    message="No cuenta con permisos suficientes",
                    status_code=status.HTTP_403_FORBIDDEN
                )
            return self
        except Exception as e:
            log.error(f"Error al verificar superusuario: {e}")
            raise BasedException(
                message="Error al verificar permisos de superusuario",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @staticmethod
    def require_roles(*roles: str):
        """
        Validate if the authenticated user has one of the required roles.

        Args:
            *roles (str): One or more role names required to access the endpoint.

        Returns:
            function: Dependency function that checks if the current user has one of the allowed roles.

        Raises:
            BasedException: If the user does not have the required roles or an unexpected error occurs.
        """

        async def role_checker(current_user: Usuarios = Depends(AuthService.get_current_user)):
            try:
                if current_user.rol not in roles:
                    raise BasedException(
                        message="Acceso denegado, no dispone de permisos para obtener acceso a este recurso",
                        status_code=status.HTTP_403_FORBIDDEN
                    )
                return current_user
            except BasedException as e:
                raise e
            except Exception as e:
                log.error(f"Error al verificar roles: {e}")
                raise BasedException(
                    message="Error al verificar permisos del rol",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return role_checker