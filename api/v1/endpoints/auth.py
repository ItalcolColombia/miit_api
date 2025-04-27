from fastapi import APIRouter, Depends, HTTPException, status
from core.di.service_injection import get_auth_service
from services.auth_service import AuthService
from schemas.usuarios_schema import UserAuth, Token  # You'll need to create these
from utils.response_util import ResponseUtil

router = APIRouter(prefix="/auth", tags=["Autenticación"])

response_json = ResponseUtil().json_response

@router.post("", response_model=Token)
async def login(
    login_data: UserAuth,
    auth_service: AuthService = Depends(get_auth_service),
):
    token = await auth_service.login(login_data.nick_name, login_data.clave)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return response_json(
        status_code=status.HTTP_200_OK,
        message="Inicio de sesión exitoso",
        token=token
    )


@router.post("/token/refresh", response_model=Token)  # Usa el mismo schema Token
async def refresh_token(
    token: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    token_data = await auth_service.refresh_token(token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data