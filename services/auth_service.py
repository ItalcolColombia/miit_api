from typing import Optional
from datetime import datetime, timedelta
from jose import jwt
from repositories.user_repository import UsuarioRepository
from schemas.usuarios_schema import UsuarioResponse, UsuarioResponseWithToken
from core.settings import settings
from fastapi import HTTPException, status
import bcrypt 

class AuthService:
    def __init__(self, user_repository: UsuarioRepository) -> None:
        self._user_repo = user_repository

    async def login(self, username: str, password: str) -> Optional[UsuarioResponseWithToken]:

        user = await self._user_repo.get_by_username(username)
        if not user or not self._verify_password(password, user.clave):
            return None
            
        try:
            access_token = self._create_access_token(user)
            return UsuarioResponseWithToken(
                access_token=access_token,
                expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not create access token"
            )

    def _create_access_token(self, user: UsuarioResponse) -> str:
        try:
            expires_delta = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
            expire = datetime.utcnow() + expires_delta
            
            to_encode = {
                "sub": str(user.id),
                "exp": expire,
                "username": user.nick_name
            }
            
            return jwt.encode(
                to_encode,
                settings.JWT_SECRET_KEY,
                algorithm=settings.JWT_ALGORITHM
            )
        except Exception as e:
            print(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token creation failed"
            )

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        from utils.any_utils import AnyUtils
        print(f"Hashed password from database: {hashed_password}")  # Debugging
        return AnyUtils.check_password_hash(plain_password, hashed_password)