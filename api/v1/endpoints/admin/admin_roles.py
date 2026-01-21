"""
Endpoints de administración de roles.

Permite gestionar roles y sus permisos de reportes.
Solo accesible para administradores.
"""

from fastapi import APIRouter, Depends, status, Path, HTTPException

from services.auth_service import AuthService
from repositories.roles_repository import RolesRepository
from schemas.roles_admin_schema import (
    RolAdminResponse,
    RolesListResponse,
    RolCreateRequest,
    RolUpdateRequest,
    PermisosRolListResponse,
    PermisoReporteAdminResponse,
    AsignarPermisosRolRequest,
    MessageResponse
)
from schemas.usuarios_schema import VUsuariosRolResponse
from core.di.repository_injection import get_roles_repository
from core.enums.user_role_enum import UserRoleEnum

router = APIRouter(
    prefix="/admin/roles",
    tags=["Admin - Roles"],
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Sin permisos de administrador"}
    }
)


# ============================================================
# ENDPOINTS DE CONSULTA DE ROLES
# ============================================================

@router.get(
    "",
    response_model=RolesListResponse,
    summary="Listar todos los roles",
    description="""
    Obtiene la lista de todos los roles del sistema con información adicional:
    - Cantidad de usuarios asignados
    - Lista de códigos de reportes que puede ver

    **Solo administradores.**
    """
)
async def listar_roles(
        current_user: VUsuariosRolResponse = Depends(
            AuthService.require_access([UserRoleEnum.ADMINISTRADOR])
        ),
        roles_repo: RolesRepository = Depends(get_roles_repository)
):
    """
    Lista todos los roles con información adicional.
    """
    roles = await roles_repo.get_all_roles()
    return RolesListResponse(roles=[RolAdminResponse(**rol) for rol in roles])


@router.get(
    "/{rol_id}",
    response_model=RolAdminResponse,
    summary="Obtener un rol",
    description="""
    Obtiene los detalles de un rol específico.

    **Solo administradores.**
    """
)
async def obtener_rol(
        rol_id: int = Path(..., description="ID del rol", ge=1),
        current_user: VUsuariosRolResponse = Depends(
            AuthService.require_access([UserRoleEnum.ADMINISTRADOR])
        ),
        roles_repo: RolesRepository = Depends(get_roles_repository)
):
    """
    Obtiene un rol por su ID.
    """
    rol = await roles_repo.get_rol_by_id(rol_id)

    if not rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rol con ID {rol_id} no encontrado"
        )

    return RolAdminResponse(**rol)


# ============================================================
# ENDPOINTS DE CREACIÓN Y MODIFICACIÓN DE ROLES
# ============================================================

@router.post(
    "",
    response_model=RolAdminResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo rol",
    description="""
    Crea un nuevo rol en el sistema.

    **Solo administradores.**
    """
)
async def crear_rol(
        request: RolCreateRequest,
        current_user: VUsuariosRolResponse = Depends(
            AuthService.require_access([UserRoleEnum.ADMINISTRADOR])
        ),
        roles_repo: RolesRepository = Depends(get_roles_repository)
):
    """
    Crea un nuevo rol.
    """
    rol = await roles_repo.create_rol(
        nombre=request.nombre,
        estado=request.estado,
        usuario_id=current_user.id
    )

    return RolAdminResponse(**rol)


@router.put(
    "/{rol_id}",
    response_model=RolAdminResponse,
    summary="Actualizar un rol",
    description="""
    Actualiza los datos de un rol existente.

    **Solo administradores.**
    """
)
async def actualizar_rol(
        rol_id: int = Path(..., description="ID del rol", ge=1),
        request: RolUpdateRequest = ...,
        current_user: VUsuariosRolResponse = Depends(
            AuthService.require_access([UserRoleEnum.ADMINISTRADOR])
        ),
        roles_repo: RolesRepository = Depends(get_roles_repository)
):
    """
    Actualiza un rol existente.
    """
    rol = await roles_repo.update_rol(
        rol_id=rol_id,
        nombre=request.nombre,
        estado=request.estado,
        usuario_id=current_user.id
    )

    if not rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rol con ID {rol_id} no encontrado"
        )

    return RolAdminResponse(**rol)


@router.delete(
    "/{rol_id}",
    response_model=MessageResponse,
    summary="Eliminar un rol",
    description="""
    Elimina un rol del sistema.
    
    **Nota:** Solo se puede eliminar si no tiene usuarios asignados.

    **Solo administradores.**
    """
)
async def eliminar_rol(
        rol_id: int = Path(..., description="ID del rol", ge=1),
        current_user: VUsuariosRolResponse = Depends(
            AuthService.require_access([UserRoleEnum.ADMINISTRADOR])
        ),
        roles_repo: RolesRepository = Depends(get_roles_repository)
):
    """
    Elimina un rol.
    """
    eliminado = await roles_repo.delete_rol(rol_id)

    if not eliminado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede eliminar el rol {rol_id}. Puede que no exista o tenga usuarios asignados."
        )

    return MessageResponse(message=f"Rol {rol_id} eliminado exitosamente")


# ============================================================
# ENDPOINTS DE PERMISOS DE REPORTES
# ============================================================

@router.get(
    "/{rol_id}/permisos-reportes",
    response_model=PermisosRolListResponse,
    summary="Obtener permisos de un rol",
    description="""
    Obtiene todos los permisos de reportes asignados a un rol específico.

    **Solo administradores.**
    """
)
async def obtener_permisos_rol(
        rol_id: int = Path(..., description="ID del rol", ge=1),
        current_user: VUsuariosRolResponse = Depends(
            AuthService.require_access([UserRoleEnum.ADMINISTRADOR])
        ),
        roles_repo: RolesRepository = Depends(get_roles_repository)
):
    """
    Obtiene los permisos de reportes de un rol.
    """
    # Verificar que el rol existe
    if not await roles_repo.verificar_rol_existe(rol_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rol con ID {rol_id} no encontrado"
        )

    permisos = await roles_repo.get_permisos_rol(rol_id)

    return PermisosRolListResponse(
        permisos=[PermisoReporteAdminResponse(**p) for p in permisos]
    )


@router.put(
    "/{rol_id}/permisos-reportes",
    response_model=MessageResponse,
    summary="Asignar permisos a un rol",
    description="""
    Asigna o actualiza los permisos de reportes para un rol.

    Esta operación reemplaza todos los permisos existentes con los nuevos.

    **Solo administradores.**
    """
)
async def asignar_permisos_rol(
        rol_id: int = Path(..., description="ID del rol", ge=1),
        request: AsignarPermisosRolRequest = ...,
        current_user: VUsuariosRolResponse = Depends(
            AuthService.require_access([UserRoleEnum.ADMINISTRADOR])
        ),
        roles_repo: RolesRepository = Depends(get_roles_repository)
):
    """
    Asigna permisos de reportes a un rol.
    """
    # Verificar que el rol existe
    if not await roles_repo.verificar_rol_existe(rol_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rol con ID {rol_id} no encontrado"
        )

    # Convertir request a lista de diccionarios
    permisos = [
        {
            "codigo_reporte": p.codigo_reporte,
            "puede_ver": p.puede_ver,
            "puede_exportar": p.puede_exportar
        }
        for p in request.permisos_reportes
    ]

    resultado = await roles_repo.asignar_permisos_rol(
        rol_id=rol_id,
        permisos=permisos,
        usuario_id=current_user.id
    )

    return MessageResponse(message=resultado["message"])
