from fastapi import APIRouter, Depends, Query, Response, status, Request
from typing import Optional
from datetime import datetime

from services.reportes.reportes_service import ReportesService
from services.reportes.exportacion_service import ExportacionService
from services.auth_service import AuthService
from schemas.reportes.reportes_schema import (
    ListaReportesResponse,
    ReporteDataResponse,
    ReporteMetadataResponse,
    FormatoExportacion,
    OrdenDireccion
)
from schemas.usuarios_schema import VUsuariosRolResponse
from core.di.service_injection import get_reportes_service, get_exportacion_service
from core.exceptions.base_exception import BasedException
from core.enums.user_role_enum import UserRoleEnum

router = APIRouter(prefix="/reportes", tags=["Reportes"])


# ============================================================
# ENDPOINTS PRINCIPALES
# ============================================================

@router.get(
    "",
    response_model=ListaReportesResponse,
    summary="Listar reportes disponibles",
    description="""
    Obtiene la lista de todos los reportes del sistema con información de permisos.

    Cada reporte incluye:
    - Información básica (código, nombre, descripción, icono)
    - Configuración (permite exportar PDF/Excel/CSV, requiere fechas, etc.)
    - Permisos del usuario (puede_ver, puede_exportar)

    Los reportes se ordenan por el campo 'orden' definido en el catálogo.
    """
)
async def listar_reportes(
        solo_con_acceso: bool = Query(
            False,
            description="Si True, solo retorna reportes a los que el usuario tiene acceso"
        ),
        current_user: VUsuariosRolResponse = Depends(AuthService.get_current_user),
        reportes_service: ReportesService = Depends(get_reportes_service)
):
    """
    Lista todos los reportes disponibles para el usuario actual.
    """
    if solo_con_acceso:
        return await reportes_service.listar_reportes_con_acceso(
            rol_id=current_user.rol_id
        )

    return await reportes_service.listar_reportes_disponibles(
        rol_id=current_user.rol_id
    )


@router.get(
    "/{codigo_reporte}",
    response_model=ReporteDataResponse,
    summary="Consultar datos de un reporte",
    description="""
    Consulta los datos de un reporte específico aplicando filtros opcionales.

    **Filtros disponibles:**
    - `material_id`: Filtrar por un material específico
    - `fecha_inicio` / `fecha_fin`: Rango de fechas
    - `orden_campo` / `orden_direccion`: Ordenamiento
    - **Filtros dinámicos**: Cualquier campo filtrable del reporte (ver metadata)

    **Paginación:**
    - `page`: Número de página (default: 1)
    - `page_size`: Registros por página (default: 50, máx: 500)

    **Filtros dinámicos de columna:**
    Se pueden agregar filtros adicionales basados en las columnas del reporte.
    Consulte `/reportes/{codigo}/metadata` para ver los filtros disponibles.
    
    Ejemplo: `?codigo_material=MAT001&nombre_almacenamiento=Bodega%20A`

    **Respuesta incluye:**
    - Información del reporte
    - Definición de columnas
    - Datos paginados
    - Totales (si aplica)
    - Información de paginación
    """
)
async def consultar_reporte(
        request: Request,
        codigo_reporte: str,
        material_id: Optional[int] = Query(
            None,
            description="ID del material para filtrar"
        ),
        fecha_inicio: Optional[datetime] = Query(
            None,
            description="Fecha inicial del rango (ISO 8601)"
        ),
        fecha_fin: Optional[datetime] = Query(
            None,
            description="Fecha final del rango (ISO 8601)"
        ),
        orden_campo: Optional[str] = Query(
            None,
            description="Campo para ordenar los resultados"
        ),
        orden_direccion: OrdenDireccion = Query(
            OrdenDireccion.DESC,
            description="Dirección de ordenamiento"
        ),
        page: int = Query(
            1,
            ge=1,
            description="Número de página"
        ),
        page_size: int = Query(
            50,
            ge=1,
            le=500,
            description="Registros por página"
        ),
        current_user: VUsuariosRolResponse = Depends(AuthService.get_current_user),
        reportes_service: ReportesService = Depends(get_reportes_service)
):
    """
    Consulta datos de un reporte específico con filtros y paginación.
    Soporta filtros dinámicos de columna basados en la metadata del reporte.
    """
    # Parámetros conocidos que no son filtros de columna
    known_params = {
        'page', 'page_size', 'material_id', 'fecha_inicio', 'fecha_fin',
        'orden_campo', 'orden_direccion'
    }

    # Extraer filtros dinámicos de columna
    all_params = dict(request.query_params)
    filtros_columna = {
        k: v for k, v in all_params.items()
        if k not in known_params
    }

    filtros = {
        'material_id': material_id,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'orden_campo': orden_campo,
        'orden_direccion': orden_direccion.value if orden_direccion else 'desc'
    }

    # Limpiar filtros None
    filtros = {k: v for k, v in filtros.items() if v is not None}

    # Agregar filtros dinámicos de columna
    if filtros_columna:
        filtros['filtros_columna'] = filtros_columna

    return await reportes_service.obtener_reporte(
        codigo_reporte=codigo_reporte,
        rol_id=current_user.rol_id,
        filtros=filtros,
        page=page,
        page_size=page_size
    )


@router.get(
    "/{codigo_reporte}/metadata",
    response_model=ReporteMetadataResponse,
    summary="Obtener metadatos de un reporte",
    description="""
    Obtiene la información de configuración y estructura de un reporte.

    **Incluye:**
    - Definición de columnas (nombre, tipo, orden, opciones de formato)
    - Filtros disponibles (materiales, rango de fechas)
    - Lista de campos totalizables

    Útil para construir la interfaz de usuario dinámicamente.
    """
)
async def obtener_metadata_reporte(
        codigo_reporte: str,
        current_user: VUsuariosRolResponse = Depends(AuthService.get_current_user),
        reportes_service: ReportesService = Depends(get_reportes_service)
):
    """
    Obtiene los metadatos de configuración de un reporte.
    """
    return await reportes_service.obtener_metadata_reporte(
        codigo_reporte=codigo_reporte,
        rol_id=current_user.rol_id
    )


# ============================================================
# ENDPOINTS DE EXPORTACIÓN
# ============================================================

@router.get(
    "/{codigo_reporte}/exportar",
    summary="Exportar reporte",
    description="""
    Exporta un reporte en el formato especificado.

    **Formatos disponibles:**
    - `pdf`: Documento PDF
    - `excel`: Archivo Excel (.xlsx)
    - `csv`: Archivo CSV

    Los mismos filtros del endpoint de consulta aplican aquí.
    La exportación incluye TODOS los registros (sin paginación).

    **Nota:** Requiere permiso de exportación para el reporte.
    """,
    responses={
        200: {
            "content": {
                "application/pdf": {},
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {},
                "text/csv": {}
            },
            "description": "Archivo del reporte exportado"
        },
        403: {"description": "Sin permisos de exportación"},
        404: {"description": "Reporte no encontrado"}
    }
)
async def exportar_reporte(
        request: Request,
        codigo_reporte: str,
        formato: FormatoExportacion = Query(
            ...,
            description="Formato de exportación"
        ),
        material_id: Optional[int] = Query(None),
        fecha_inicio: Optional[datetime] = Query(None),
        fecha_fin: Optional[datetime] = Query(None),
        current_user: VUsuariosRolResponse = Depends(AuthService.get_current_user),
        reportes_service: ReportesService = Depends(get_reportes_service),
        exportacion_service: ExportacionService = Depends(get_exportacion_service)
):
    """
    Exporta un reporte en el formato especificado (PDF, Excel, CSV).
    Soporta filtros dinámicos de columna igual que el endpoint de consulta.
    """
    # Deshabilitar temporalmente exportación Excel
    if formato == FormatoExportacion.EXCEL:
        raise BasedException(
            message="Exportación Excel temporalmente deshabilitada. Use CSV o PDF.",
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # Verificar que el formato está permitido para este reporte
    formato_permitido = await reportes_service.verificar_formato_exportacion(
        codigo_reporte=codigo_reporte,
        formato=formato.value
    )

    if not formato_permitido:
        raise BasedException(
            message=f"El formato '{formato.value}' no está permitido para este reporte",
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # Parámetros conocidos que no son filtros de columna
    known_params = {
        'formato', 'material_id', 'fecha_inicio', 'fecha_fin'
    }

    # Extraer filtros dinámicos de columna
    all_params = dict(request.query_params)
    filtros_columna = {
        k: v for k, v in all_params.items()
        if k not in known_params
    }

    # Construir filtros
    filtros = {
        'material_id': material_id,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin
    }
    filtros = {k: v for k, v in filtros.items() if v is not None}

    # Agregar filtros dinámicos de columna
    if filtros_columna:
        filtros['filtros_columna'] = filtros_columna

    # Obtener datos para exportar
    datos_exportar = await reportes_service.obtener_datos_para_exportar(
        codigo_reporte=codigo_reporte,
        rol_id=current_user.rol_id,
        filtros=filtros
    )

    # Generar nombre de archivo
    fecha_actual = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    nombre_base = f"{codigo_reporte}_{fecha_actual}"

    # Exportar según formato
    if formato == FormatoExportacion.EXCEL:
        contenido = exportacion_service.exportar_excel(
            datos=datos_exportar['datos'],
            nombre_reporte=datos_exportar['reporte']['nombre'],
            columnas=datos_exportar['columnas'],
            totales=datos_exportar.get('totales')
        )
        return Response(
            content=contenido,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{nombre_base}.xlsx"'
            }
        )

    elif formato == FormatoExportacion.PDF:
        contenido = exportacion_service.exportar_pdf(
            datos=datos_exportar['datos'],
            nombre_reporte=datos_exportar['reporte']['nombre'],
            columnas=datos_exportar['columnas'],
            totales=datos_exportar.get('totales')
        )
        return Response(
            content=contenido,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{nombre_base}.pdf"'
            }
        )

    else:  # CSV
        contenido = exportacion_service.exportar_csv(
            datos=datos_exportar['datos'],
            columnas=datos_exportar['columnas']
        )
        return Response(
            content=contenido.encode('utf-8-sig'),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{nombre_base}.csv"'
            }
        )


# ============================================================
# ENDPOINTS DE ADMINISTRACIÓN
# ============================================================

@router.post(
    "/refresh",
    summary="Refrescar todas las vistas",
    description="""
    Refresca todas las vistas materializadas de reportes.

    **Nota:** Requiere rol de Administrador.
    Esta operación puede tardar varios segundos dependiendo del volumen de datos.
    """,
    status_code=status.HTTP_200_OK
)
async def refrescar_vistas(
        current_user: VUsuariosRolResponse = Depends(
            AuthService.require_access([UserRoleEnum.ADMINISTRADOR])
        ),
        reportes_service: ReportesService = Depends(get_reportes_service)
):
    """
    Refresca todas las vistas materializadas de reportes.
    Solo disponible para administradores.
    """
    await reportes_service.refrescar_vistas()

    return {
        "message": "Todas las vistas de reportes han sido refrescadas",
        "timestamp": datetime.now().isoformat()
    }


@router.post(
    "/{codigo_reporte}/refresh",
    summary="Refrescar vista de un reporte",
    description="""
    Refresca la vista materializada de un reporte específico.

    **Nota:** Requiere rol de Administrador.
    """,
    status_code=status.HTTP_200_OK
)
async def refrescar_vista_reporte(
        codigo_reporte: str,
        current_user: VUsuariosRolResponse = Depends(
            AuthService.require_access([UserRoleEnum.ADMINISTRADOR])
        ),
        reportes_service: ReportesService = Depends(get_reportes_service)
):
    """
    Refresca la vista materializada de un reporte específico.
    Solo disponible para administradores.
    """
    await reportes_service.refrescar_vista_reporte(codigo_reporte)

    return {
        "message": f"Vista del reporte '{codigo_reporte}' ha sido refrescada",
        "timestamp": datetime.now().isoformat()
    }