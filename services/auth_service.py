from typing import Optional
from datetime import datetime, timedelta
from jose import jwt
from repositories.usuarios_repository import UsuariosRepository
from schemas.usuarios_schema import UsuariosResponse, UsuarioResponseWithToken
from core.settings import settings
from fastapi import HTTPException, status
from core.exceptions.auth_exception import InvalidCredentialsException
from utils.jwt_util import JWTUtil
from utils.any_utils import AnyUtils
from utils.logger_util import LoggerUtil
import bcrypt 

log = LoggerUtil()


class AuthService:
    def __init__(self, user_repository: UsuariosRepository) -> None:
        self._user_repo = user_repository

    async def login(self, username: str, password: str) -> Optional[UsuarioResponseWithToken]:

        user = await self._user_repo.get_by_username(username)
        if not user or not self._verify_password(password, user.clave):
            log.info(
                    f"Invalid user or password {username}!"
                )
            raise InvalidCredentialsException("Invalid credentials!")

        try:
            token_data = {"user": user.id, "role": user.rol_id}
            access_token = JWTUtil.create_token(token_data)
            refresh_token = JWTUtil.create_refresh_token(token_data) # Genera el refresh token
            return UsuarioResponseWithToken(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not create access token"
            )

    async def refresh_token(self, refresh_token: str) -> Optional[UsuarioResponseWithToken]:
        try:
            payload = JWTUtil.verify_token(refresh_token)
            if not payload:
                return None  # Invalid token

            #Verifica si el usuario existe
            user_id = payload.get("user")
            user = await self._user_repo.get_by_id(user_id)
            if not user:
                return None  # User not found

            token_data = {"user": user.id, "role": user.rol_id}
            access_token = JWTUtil.create_token(token_data)
            refresh_token = JWTUtil.create_refresh_token(token_data)
            return UsuarioResponseWithToken(access_token=access_token, refresh_token=refresh_token)
        except Exception as e:
            log.error(f"Error refreshing token: {e}")
            return None  # Handle errors gracefully

    # def _create_access_token(self, user: UsuarioResponse) -> str:
    #     try:
    #         expires_delta = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    #         expire = datetime.utcnow() + expires_delta
            
    #         to_encode = {
    #             "sub": str(user.id),
    #             "exp": expire,
    #             "username": user.nick_name
    #         }
            
    #         return jwt.encode(
    #             to_encode,
    #             settings.JWT_SECRET_KEY,
    #             algorithm=settings.JWT_ALGORITHM
    #         )
    #     except Exception as e:
    #         print(e)
    #         raise HTTPException(
    #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #             detail="Token creation failed"
    #         )

    def __verify_email(self, email: str) -> UsuariosResponse | None:
        """
        Private method responsible for checking if an email exists in the database.

        Args:
            email (str): The email address to check.

        Returns:
            UserModel | None: The user instance if found, otherwise None.
        """

        user = self._user_repo.get_by_email(email)

        if user:
            return user
        return None
    
    @staticmethod
    def _verify_password(plain_password: str, hashed_password: str) -> bool:
        from utils.any_utils import AnyUtils
        """
        Private method responsible for verifying if the provided password matches the stored password.

        Args:
            plain_password (str): The password provided in the login request.
            hashed_password (str): The hashed password stored in the database.
s
        Returns:
            bool: True if the passwords match, otherwise False.
        """
        return AnyUtils.check_password_hash(plain_password, hashed_password)