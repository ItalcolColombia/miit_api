from fastapi import APIRouter, Depends, HTTPException, status

from core.di.service_injection import get_auth_service
from schemas.response_models import ErrorResponse
from schemas.usuarios_schema import UserAuth, Token  # You'll need to create these
from services.auth_service import AuthService
from utils.jwt_util import JWTUtil
from utils.logger_util import LoggerUtil
from utils.response_util import ResponseUtil

router = APIRouter(prefix="/auth", tags=["Autenticación"])

log = LoggerUtil()

response_json = ResponseUtil.json_response

@router.post("", status_code=status.HTTP_200_OK,
             summary="Iniciar sesión",
             description="Mécanismo de autenticación empleado para obtener acceso a los recursos protegidos.",
             response_model=Token,
             responses={
                 status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
                 status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
             })
async def login(
    login_data: UserAuth,
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        token = await auth_service.login(login_data.nick_name, login_data.clave)
        log.info(f"Login exitoso de usuario {login_data.nick_name}")
        return response_json(
            status_code=status.HTTP_200_OK,
            message=f"Inicio de sesión exitoso",
            token=token
        )
    except HTTPException as http_exc:
        log.error(f"Login de {login_data.nick_name} no exitoso: {http_exc.detail}")
        return response_json(
            status_code=http_exc.status_code,
            message=http_exc.detail,
        )

    except Exception as e:
        log.error(f"Error al procesar petición de login de usuario {login_data.nick_name}: {e}")
        return response_json(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=str(e)
        )

@router.post("/token/refresh",
             status_code=status.HTTP_200_OK,
             summary="Refrescar sesión",
             description="Mécanismo de autenticación empleado para renovar el acceso a los recursos protegidos.",
             response_model=Token,
             responses={
                 status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
                 status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
             })
async def refresh(
    auth_service: AuthService = Depends(get_auth_service),
    token = Depends(AuthService.get_token),
):
    payload = JWTUtil.verify_token(token)
    log.info(f"Payload recibido: Refrescar Token de {payload.get("sub")}")
    try:
        token_data = await auth_service.refresh_token(token)
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        log.info(f"Refrescado exitoso de token para usuario {payload.get("sub")}")
        return response_json(
            status_code=status.HTTP_200_OK,
            message=f"Refresco de sesión exitoso",
            token=token_data
        )
    except HTTPException as http_exc:
        log.error(f"Refrescado de token no exitoso: {http_exc.detail}")
        return response_json(
            status_code=http_exc.status_code,
            message=http_exc.detail
        )

    except Exception as e:
        log.error(f"Error al procesar petición de refrescar token de usuario {payload.get("sub")} : {e}")
        return response_json(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=str(e)
        )
