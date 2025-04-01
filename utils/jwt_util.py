
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException
from jwt.exceptions import (
    ExpiredSignatureError,
    InvalidKeyError,
    InvalidTokenError,
)

from core.settings import Settings
from core.exceptions.jwt_exception import UnauthorizedToken
from utils.logger_util import LoggerUtil

log = LoggerUtil()

# Env variables Setup
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = (
    Settings().JWT_ACCESS_TOKEN_EXPIRE_MINUTES
)
JWT_SECRET_KEY = Settings().JWT_SECRET_KEY
JWT_ALGORITHM = Settings().JWT_ALGORITHM


class JWTUtil:
    """
    Class responsible for handling JSON Web Token (JWT) operations.

    This class provides methods for creating, verifying, and decoding JWT tokens.

    Class Args:
        None
    """

    @staticmethod
    def create_token(
        data: dict, expires_delta: timedelta | None = None
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

        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (
            expires_delta or timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM
        )
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
                token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM]
            )
            return payload
        except ExpiredSignatureError:
            raise UnauthorizedToken("Token expired!")
        except InvalidTokenError:
            raise UnauthorizedToken("Invalid token!")
        except InvalidKeyError:
            raise UnauthorizedToken("Invalid signing key!")
        except Exception as e:
            log.error(f"Unexpected error in verify_token: {e}")
            raise HTTPException(
                status_code=500, detail=f"JWT decoding error: {str(e)}"
            )
