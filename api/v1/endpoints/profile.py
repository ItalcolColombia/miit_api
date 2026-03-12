from fastapi import APIRouter, Depends, HTTPException, status

from core.di.service_injection import get_user_service
from schemas.usuarios_schema import CambiarClave, ProfileUpdate, UsuariosResponse, VUsuariosRolResponse
from services.auth_service import AuthService
from services.usuarios_service import UsuariosService

router = APIRouter(
    prefix="/profile",
    tags=["Perfil"],
    dependencies=[Depends(AuthService.get_current_user)]
)


@router.get(
    "/me",
    response_model=UsuariosResponse,
    summary="Obtener mi perfil",
    description="Devuelve la información del usuario autenticado.",
    responses={
        200: {"description": "Perfil del usuario autenticado"},
        401: {"description": "No autenticado"},
    },
    operation_id="get_my_profile"
)
async def get_my_profile(
    current_user: VUsuariosRolResponse = Depends(AuthService.get_current_user),
    user_service: UsuariosService = Depends(get_user_service)
):
    user = await user_service.get_user(current_user.id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return user


@router.put(
    "/me",
    response_model=UsuariosResponse,
    summary="Actualizar mi perfil",
    description="Actualiza la información personal del usuario autenticado. No permite cambiar rol ni estado.",
    responses={
        200: {"description": "Perfil actualizado correctamente"},
        400: {"description": "No se enviaron campos para actualizar"},
        401: {"description": "No autenticado"},
        404: {"description": "Usuario no encontrado"},
        409: {"description": "El nick_name ya está registrado"},
    },
    operation_id="update_my_profile"
)
async def update_my_profile(
    profile_data: ProfileUpdate,
    current_user: VUsuariosRolResponse = Depends(AuthService.get_current_user),
    user_service: UsuariosService = Depends(get_user_service)
):
    update_data = profile_data.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se enviaron campos para actualizar")

    user = await user_service.update_user_partial(current_user.id, update_data)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return user


@router.patch(
    "/me/change-password",
    status_code=status.HTTP_200_OK,
    summary="Cambiar mi contraseña",
    description="Permite al usuario autenticado cambiar su propia contraseña.",
    responses={
        200: {"description": "Contraseña actualizada correctamente"},
        400: {"description": "La nueva contraseña no cumple los requisitos de complejidad"},
        401: {"description": "No autenticado o contraseña actual incorrecta"},
    },
    operation_id="change_my_password"
)
async def change_my_password(
    password_data: CambiarClave,
    current_user: VUsuariosRolResponse = Depends(AuthService.get_current_user),
    user_service: UsuariosService = Depends(get_user_service)
):
    await user_service.change_password(
        current_user.id,
        password_data.clave_actual,
        password_data.clave_nueva
    )
    return {"message": "Contraseña actualizada correctamente"}
