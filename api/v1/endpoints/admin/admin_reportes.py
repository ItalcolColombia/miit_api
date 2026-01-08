"""
Endpoints de administración de reportes.

Permite gestionar permisos de reportes por rol.
Solo accesible para administradores.
"""

from fastapi import APIRouter, Depends, status, Path
from typing import List

from services.auth_service import AuthService
from repositories.reportes.reportes_repository import ReportesRepository
from schemas.reportes.reportes_schema import (
    PermisoReporteResponse,
    AsignarPermisosRequest,
    PermisosRolResponse,
    ReporteResponse
)
from schemas.usuarios_schema import VUsuariosRolResponse
from core.di.repository_injection import get_reportes_repository
from core.exceptions.base_exception import BasedException
from core.enums.user_role_enum import UserRoleEnum

router = APIRouter(
    prefix="/admin/reportes",
    tags=["Admin - Reportes"],
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Sin permisos de administrador"}
    }
)


# ============================================================
# ENDPOINTS DE CONSULTA
# ============================================================

@router.get(
    "/catalogo",
    response_model=List[ReporteResponse],
    summary="Listar catálogo completo de reportes",
    description="""
    Obtiene el catálogo completo de reportes del sistema.
    Incluye reportes activos e inactivos.

    **Solo administradores.**
    """
)
async def listar_catalogo_reportes(
        current_user: VUsuariosRolResponse = Depends(
            AuthService.require_access([UserRoleEnum.ADMINISTRADOR])
        ),
        reportes_repo: ReportesRepository = Depends(get_reportes_repository)
):
    """
    Lista todos los reportes del catálogo para administración.
    """
    reportes = await reportes_repo.get_all_reportes(solo_activos=False)
    return reportes


@router.get(
    "/permisos/roles/{rol_id}",
    response_model=PermisosRolResponse,
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
        reportes_repo: ReportesRepository = Depends(get_reportes_repository)
):
    """
    Obtiene los permisos de reportes para un rol específico.
    """
    # Obtener permisos del rol
    permisos = await reportes_repo.get_permisos_rol(rol_id)

    # Contar reportes con acceso
    reportes_con_acceso = sum(1 for p in permisos if p.puede_ver)

    # Obtener total de reportes
    todos_reportes = await reportes_repo.get_all_reportes(solo_activos=True)

    # TODO: Obtener nombre del rol desde la base de datos
    rol_nombre = f"Rol #{rol_id}"

    return PermisosRolResponse(
        rol_id=rol_id,
        rol_nombre=rol_nombre,
        permisos=[PermisoReporteResponse.model_validate(p) for p in permisos],
        total_reportes=len(todos_reportes),
        reportes_con_acceso=reportes_con_acceso
    )


# ============================================================
# ENDPOINTS DE MODIFICACIÓN
# ============================================================

@router.put(
    "/permisos/roles/{rol_id}",
    summary="Asignar permisos a un rol",
    description="""
    Asigna o actualiza los permisos de reportes para un rol.

    Permite configurar:
    - `puede_ver`: Si el rol puede visualizar el reporte
    - `puede_exportar`: Si el rol puede exportar el reporte

    **Solo administradores.**
    """,
    status_code=status.HTTP_200_OK
)
async def asignar_permisos_rol(
        rol_id: int = Path(..., description="ID del rol", ge=1),
        request: AsignarPermisosRequest = ...,
        current_user: VUsuariosRolResponse = Depends(
            AuthService.require_access([UserRoleEnum.ADMINISTRADOR])
        ),
        reportes_repo: ReportesRepository = Depends(get_reportes_repository)
):
    """
    Asigna o actualiza permisos de reportes para un rol.
    """
    resultados = []

    for permiso in request.permisos_reportes:
        resultado = await reportes_repo.asignar_permiso(
            rol_id=rol_id,
            codigo_reporte=permiso.codigo_reporte,
            puede_ver=permiso.puede_ver,
            puede_exportar=permiso.puede_exportar,
            usuario_id=current_user.id
        )
        resultados.append({
            "codigo_reporte": permiso.codigo_reporte,
            "puede_ver": resultado.puede_ver,
            "puede_exportar": resultado.puede_exportar,
            "actualizado": True
        })

    return {
        "message": f"Permisos actualizados para rol {rol_id}",
        "permisos_actualizados": len(resultados),
        "detalle": resultados
    }


@router.delete(
    "/permisos/roles/{rol_id}/{codigo_reporte}",
    summary="Eliminar permiso específico",
    description="""
    Elimina el permiso de un reporte específico para un rol.

    **Solo administradores.**
    """,
    status_code=status.HTTP_200_OK
)
async def eliminar_permiso(
        rol_id: int = Path(..., description="ID del rol", ge=1),
        codigo_reporte: str = Path(..., description="Código del reporte"),
        current_user: VUsuariosRolResponse = Depends(
            AuthService.require_access([UserRoleEnum.ADMINISTRADOR])
        ),
        reportes_repo: ReportesRepository = Depends(get_reportes_repository)
):
    """
    Elimina el permiso de un reporte para un rol.
    """
    eliminado = await reportes_repo.eliminar_permiso(rol_id, codigo_reporte)

    if not eliminado:
        raise BasedException(
            message=f"No se encontró el permiso para rol {rol_id} y reporte {codigo_reporte}",
            status_code=status.HTTP_404_NOT_FOUND
        )

    return {
        "message": "Permiso eliminado exitosamente",
        "rol_id": rol_id,
        "codigo_reporte": codigo_reporte
    }


# ============================================================
# ENDPOINTS DE ACTIVACIÓN/DESACTIVACIÓN
# ============================================================

@router.patch(
    "/{codigo_reporte}/activar",
    summary="Activar un reporte",
    description="""
    Activa un reporte desactivado.

    **Solo administradores.**
    """,
    status_code=status.HTTP_200_OK
)
async def activar_reporte(
        codigo_reporte: str = Path(..., description="Código del reporte"),
        current_user: VUsuariosRolResponse = Depends(
            AuthService.require_access([UserRoleEnum.ADMINISTRADOR])
        ),
        reportes_repo: ReportesRepository = Depends(get_reportes_repository)
):
    """
    Activa un reporte del catálogo.
    """
    reporte = await reportes_repo.get_reporte_by_codigo(codigo_reporte)

    if not reporte:
        raise BasedException(
            message=f"Reporte '{codigo_reporte}' no encontrado",
            status_code=status.HTTP_404_NOT_FOUND
        )

    if reporte.activo:
        return {
            "message": f"El reporte '{codigo_reporte}' ya está activo",
            "codigo": codigo_reporte,
            "activo": True
        }

    # Actualizar estado
    reporte.activo = True
    await reportes_repo.db.commit()

    return {
        "message": f"Reporte '{codigo_reporte}' activado exitosamente",
        "codigo": codigo_reporte,
        "activo": True
    }


@router.patch(
    "/{codigo_reporte}/desactivar",
    summary="Desactivar un reporte",
    description="""
    Desactiva un reporte. Los usuarios no podrán acceder a él.

    **Solo administradores.**
    """,
    status_code=status.HTTP_200_OK
)
async def desactivar_reporte(
        codigo_reporte: str = Path(..., description="Código del reporte"),
        current_user: VUsuariosRolResponse = Depends(
            AuthService.require_access([UserRoleEnum.ADMINISTRADOR])
        ),
        reportes_repo: ReportesRepository = Depends(get_reportes_repository)
):
    """
    Desactiva un reporte del catálogo.
    """
    reporte = await reportes_repo.get_reporte_by_codigo(codigo_reporte)

    if not reporte:
        raise BasedException(
            message=f"Reporte '{codigo_reporte}' no encontrado",
            status_code=status.HTTP_404_NOT_FOUND
        )

    if not reporte.activo:
        return {
            "message": f"El reporte '{codigo_reporte}' ya está desactivado",
            "codigo": codigo_reporte,
            "activo": False
        }

    # Actualizar estado
    reporte.activo = False
    await reportes_repo.db.commit()

    return {
        "message": f"Reporte '{codigo_reporte}' desactivado exitosamente",
        "codigo": codigo_reporte,
        "activo": False
    }
