
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from jwt import exceptions as jwt_exceptions
from jwt.exceptions import (
    ExpiredSignatureError,
    InvalidKeyError,
    InvalidTokenError,
)

from core.exceptions.base_exception import BasedException
from core.settings import get_settings
from core.exceptions.jwt_exception import UnauthorizedToken
from utils.logger_util import LoggerUtil

log = LoggerUtil()

JWT_ACCESS_TOKEN_EXPIRE_MINUTES = get_settings().JWT_ACCESS_TOKEN_EXPIRE_MINUTES
JWT_REFRESH_TOKEN_EXPIRE_DAYS = get_settings().JWT_REFRESH_TOKEN_EXPIRE_DAYS
JWT_SECRET_KEY = get_settings().JWT_SECRET_KEY
JWT_ALGORITHM = get_settings().JWT_ALGORITHM
JWT_ISSUER = get_settings().JWT_ISSUER
JWT_AUDIENCE = get_settings().JWT_AUDIENCE

class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        """
                Initialize the JWTBearer security scheme.

                Args:
                    auto_error (bool): If True, automatically raises HTTPException on authentication errors.
                        Defaults to True.

                Raises:
                    BasedException: If initialization fails due to unexpected errors.
                """
        try:
            super(JWTBearer, self).__init__(
                scheme_name="JWT-Auth",
                description="Enter JWT token",
                auto_error=auto_error
            )
        except Exception as e:
            log.error(f"Error al inicializar jwt_util: {e}")
            raise BasedException(
                message=f"Error inesperado en jwt_util: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=403, detail="Invalid authentication scheme.")
            if not JWTUtil.verify_token(credentials.credentials):
                raise HTTPException(status_code=403, detail="Invalid token or expired token.")
            return credentials.credentials
        else:
            raise HTTPException(status_code=403, detail="Invalid authorization code.")


class JWTUtil:
    """
    Class responsible for handling JSON Web Token (JWT) operations.

    This class provides methods for creating, verifying, and decoding JWT tokens.

    Class Args:
        None
    """

    @staticmethod
    def create_token(
        data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Static method responsible for creating a JWT access token.

        This method encodes user-related data into a JWT token with an expiration time.

        Args:
            data (dict): The payload to be encoded in the token.
            expires_delta (timedelta | None, optional): The time until the token expires.
                Defaults to `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`.

        Returns:
            str: The generated JWT token.
        """
    
        try:
            to_encode = data.copy()
            expire = datetime.now(timezone.utc) + (
                    expires_delta or timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
            )
            to_encode.update({"iat": int(datetime.now().timestamp()),
                              "exp": expire,
                              "aud": JWT_AUDIENCE,
                              "iss": JWT_ISSUER})
            encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
            return encoded_jwt
        except Exception as e:
            # General exception handling
            print(f"Ocurrió un error al crear el token: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al crear token"
            )

    @staticmethod
    def create_refresh_token(data: dict, expires_delta: timedelta = None) -> str:
        """
               Static method responsible for refreshing a JWT token.

               This method refresh a JWT token, ensuring its validity.

               Args:
                   data (dict): The JWT token to be refreshed.
                   expires_delta: Expiration  time

               Returns:
                   dict: The encoded token.

               Raises:
                   UnauthorizedToken: If the token is expired, invalid, or has an incorrect signature.
                   HTTPException: If an unexpected error occurs during verification.
               """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"iat": int(datetime.now().timestamp()),
                          "exp": expire,
                          "aud": JWT_AUDIENCE,
                          "iss": JWT_ISSUER })
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> dict:
        """
        Static method responsible for verifying and decoding a JWT token.

        This method decodes a JWT token, ensuring its validity and integrity.

        Args:
            token (str): The JWT token to be verified.

        Returns:
            dict: The decoded token payload.

        Raises:
            UnauthorizedToken: If the token is expired, invalid, or has an incorrect signature.
            HTTPException: If an unexpected error occurs during verification.
        """

        try:
            payload = jwt.decode(
                token,
                JWT_SECRET_KEY,
                algorithms=[JWT_ALGORITHM],
                audience="MIIT-API",
                issuer="MIIT-API-Authentication"
            )
            return payload
        except ExpiredSignatureError:
            raise UnauthorizedToken("El token ha expirado.")
        except InvalidTokenError:
            raise UnauthorizedToken("El token es inválido.")
        except InvalidKeyError:
            raise UnauthorizedToken("La clave de firma es inválida.")
        except Exception as e:
            log.error(f"Error al validar token: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error al validar el token: {str(e)}"
            )
