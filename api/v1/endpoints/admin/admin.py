from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from core.di.service_injection import get_user_service
from core.enums.user_role_enum import UserRoleEnum
from schemas.usuarios_schema import UsuarioCreate, UsuariosResponse, UsuarioUpdate, VUsuariosRolResponse
from services.auth_service import AuthService
from services.usuarios_service import UsuariosService
from utils.response_util import ResponseUtil

response_json = ResponseUtil().json_response
router = APIRouter(
    prefix="/admin",
    tags=["Administrador"],
    dependencies=[Depends(AuthService.require_access(roles=[UserRoleEnum.SUPER_ADMINISTRATOR, UserRoleEnum.ADMINISTRADOR]))]
)


@router.post(
    "/create",
    response_model=UsuariosResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario",
    description="Crea un nuevo usuario. Requiere rol SUPER_ADMINISTRATOR o ADMINISTRADOR.",
    responses={
        201: {
            "description": "Usuario creado correctamente",
            "content": {
                "application/json": {
                    "example": {
                        "id": 123,
                        "username": "jdoe",
                        "email": "jdoe@example.com",
                        "roles": ["ADMINISTRADOR"],
                        "is_active": True,
                        "created_at": "2026-01-17T10:00:00Z"
                    }
                }
            },
        },
        400: {"description": "Petición inválida"},
        401: {"description": "No autenticado"},
        403: {"description": "Sin permisos"}
    },
    operation_id="register_user"
)
async def register_user(
    user_data: UsuarioCreate,
    current_user: VUsuariosRolResponse = Depends(AuthService.get_current_user),
    user_service: UsuariosService = Depends(get_user_service)
):
    created_user = await user_service.create_user(user_data, current_user.id)
    return created_user


@router.get(
    "/{user_id}",
    response_model=UsuariosResponse,
    summary="Obtener usuario por id",
    description="Devuelve la información de un usuario por su id.",
    responses={
        200: {
            "description": "Usuario encontrado",
            "content": {
                "application/json": {
                    "example": {
                        "id": 123,
                        "username": "jdoe",
                        "email": "jdoe@example.com",
                        "roles": ["ADMINISTRADOR"],
                        "is_active": True,
                        "created_at": "2026-01-17T10:00:00Z"
                    }
                }
            }
        },
        404: {"description": "User not found"},
        401: {"description": "No autenticado"},
        403: {"description": "Sin permisos"}
    },
    operation_id="get_user"
)
async def get_user(
    user_id: int,
    user_service: UsuariosService = Depends(get_user_service)
):
    user = await user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get(
    "/",
    response_model=List[UsuariosResponse],
    summary="Listar usuarios",
    description="Devuelve la lista de usuarios. Soporta paginación/filtrado si se implementa en el servicio.",
    responses={
        200: {
            "description": "Lista de usuarios",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 123,
                            "username": "jdoe",
                            "email": "jdoe@example.com",
                            "roles": ["ADMINISTRADOR"],
                            "is_active": True,
                            "created_at": "2026-01-17T10:00:00Z"
                        },
                        {
                            "id": 124,
                            "username": "asmith",
                            "email": "asmith@example.com",
                            "roles": ["SUPER_ADMINISTRATOR"],
                            "is_active": True,
                            "created_at": "2026-01-15T09:00:00Z"
                        }
                    ]
                }
            }
        },
        401: {"description": "No autenticado"},
        403: {"description": "Sin permisos"}
    },
    operation_id="list_users"
)
async def list_users(
    user_service: UsuariosService = Depends(get_user_service)
):
    all_users = await user_service.get_all_users()
    return all_users


@router.put(
    "/{user_id}",
    response_model=UsuariosResponse,
    summary="Actualizar usuario",
    description="Actualiza los campos de un usuario existente.",
    responses={
        200: {
            "description": "Usuario actualizado",
            "content": {
                "application/json": {
                    "example": {
                        "id": 123,
                        "username": "jdoe",
                        "email": "jdoe.updated@example.com",
                        "roles": ["ADMINISTRADOR"],
                        "is_active": True,
                        "created_at": "2026-01-17T10:00:00Z"
                    }
                }
            }
        },
        404: {"description": "User not found"},
        400: {"description": "Petición inválida"},
        401: {"description": "No autenticado"},
        403: {"description": "Sin permisos"}
    },
    operation_id="update_user"
)
async def update_user(
    user_id: int,
    user_data: UsuarioUpdate,
    user_service: UsuariosService = Depends(get_user_service)
):
    user = await user_service.update_user(user_id, user_data)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar usuario",
    description="Elimina un usuario por id. Responde 204 en caso de éxito.",
    responses={
        204: {"description": "User deleted successfully"},
        404: {"description": "User not found"},
        401: {"description": "No autenticado"},
        403: {"description": "Sin permisos"}
    },
    operation_id="delete_user"
)
async def delete_user(
    user_id: int,
    user_service: UsuariosService = Depends(get_user_service)
):
    user_deleted = await user_service.delete_user(user_id)
    if not user_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"message": "User deleted successfully"}
