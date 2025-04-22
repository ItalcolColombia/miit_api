from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from core.settings import Settings
from database.models import Usuarios
from services.usuarios_service import UsuariosService
from core.di.service_injection import get_user_service
from utils.response_util import ResponseUtil


# Env variables Setup
SECRET_KEY = Settings().JWT_SECRET_KEY
ALGORITHM = Settings().JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = Settings().JWT_ACCESS_TOKEN_EXPIRE_MINUTES

security = HTTPBearer()

response_json = ResponseUtil().json_response


credentials_exception = HTTPException(status_code= status.HTTP_401_UNAUTHORIZED,
                        detail="could not validate credentials",
                        headers={"WWW-Authenticate": "Bearer"},)



async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        user_service: UsuariosService = Depends(get_user_service)
) -> Usuarios:


    try:
        token = credentials.credentials
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        user_id: str = payload.get("user")
        if user_id is None:
            raise credentials_exception
    except (JWTError, ValueError):
        raise credentials_exception

    user = await user_service.get_user(int(user_id))
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