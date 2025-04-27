from datetime import timedelta
from fastapi import Depends, HTTPException, Request, status
from core.settings import Settings
from database.models import Usuarios
from schemas.usuarios_schema import Token
from services.usuarios_service import UsuariosService
from core.di.service_injection import get_user_service
from utils.response_util import ResponseUtil
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from utils.jwt_util import JWTUtil
from typing import Annotated


# bearer_scheme = HTTPBearer()

response_json = ResponseUtil().json_response

credentials_exception = HTTPException(status_code= status.HTTP_401_UNAUTHORIZED,
                        detail="could not validate credentials",
                        headers={"WWW-Authenticate": "Bearer"},)



class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(scheme_name="JWT-Auth", description="Enter JWT token",  auto_error=auto_error)

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


async def get_current_user(
        #credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
        token : Annotated[Token, Depends(JWTBearer())],
        user_service: UsuariosService = Depends(get_user_service)
) -> Usuarios:

    payload = JWTUtil.verify_token(token)
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception


    user = await user_service.get_username(username)
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
        current_user: Usuarios = Depends(get_current_user)
) -> Usuarios:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_super_user(
        current_user: Usuarios = Depends(get_current_user)
) -> Usuarios:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough privileges"
        )
    return current_user