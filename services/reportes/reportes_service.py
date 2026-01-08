from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import status

from repositories.reportes.reportes_repository import ReportesRepository
from schemas.reportes.reportes_schema import (
    ReporteConPermisosResponse,
    ReporteDataResponse,
    ReporteInfoResponse,
    ReporteColumnaResponse,
    ReporteMetadataResponse,
    PaginacionResponse,
    FiltrosDisponiblesResponse,
    MaterialFiltroResponse,
    RangoFechasResponse,
    ListaReportesResponse
)
from core.exceptions.base_exception import BasedException


class ReportesService:
    """
    Servicio para la lógica de negocio de reportes.
    Coordina entre el repositorio y los endpoints.
    """

    def __init__(self, reportes_repo: ReportesRepository):
        self.reportes_repo = reportes_repo

    # ========================================================
    # LISTADO DE REPORTES
    # ========================================================

    async def listar_reportes_disponibles(
            self,
            rol_id: int
    ) -> ListaReportesResponse:
        """
        Lista todos los reportes disponibles para un rol específico.
        Incluye información de permisos (puede_ver, puede_exportar).

        Args:
            rol_id: ID del rol del usuario

        Returns:
            ListaReportesResponse con reportes y total
        """
        reportes_data = await self.reportes_repo.get_reportes_con_permisos(rol_id)

        reportes = [
            ReporteConPermisosResponse(**reporte)
            for reporte in reportes_data
        ]

        return ListaReportesResponse(
            reportes=reportes,
            total=len(reportes)
        )

    async def listar_reportes_con_acceso(
            self,
            rol_id: int
    ) -> ListaReportesResponse:
        """
        Lista solo los reportes a los que el usuario tiene acceso.

        Args:
            rol_id: ID del rol del usuario

        Returns:
            ListaReportesResponse con reportes accesibles
        """
        reportes_data = await self.reportes_repo.get_reportes_con_permisos(rol_id)

        # Filtrar solo los que puede ver
        reportes = [
            ReporteConPermisosResponse(**reporte)
            for reporte in reportes_data
            if reporte.get('puede_ver', False)
        ]

        return ListaReportesResponse(
            reportes=reportes,
            total=len(reportes)
        )

    # ========================================================
    # CONSULTA DE REPORTES
    # ========================================================

    async def obtener_reporte(
            self,
            codigo_reporte: str,
            rol_id: int,
            filtros: Dict[str, Any],
            page: int = 1,
            page_size: int = 50
    ) -> ReporteDataResponse:
        """
        Obtiene los datos de un reporte específico con filtros y paginación.

        Args:
            codigo_reporte: Código del reporte (ej: 'RPT_BASCULA')
            rol_id: ID del rol del usuario
            filtros: Diccionario con filtros a aplicar
            page: Número de página
            page_size: Registros por página

        Returns:
            ReporteDataResponse con datos, columnas, totales y paginación

        Raises:
            BasedException: Si no tiene permisos o el reporte no existe
        """
        # Verificar acceso
        tiene_acceso = await self.reportes_repo.verificar_acceso(
            rol_id=rol_id,
            codigo_reporte=codigo_reporte
        )

        if not tiene_acceso:
            raise BasedException(
                message="No tiene permisos para acceder a este reporte",
                status_code=status.HTTP_403_FORBIDDEN
            )

        # Obtener configuración del reporte
        reporte = await self.reportes_repo.get_reporte_by_codigo(codigo_reporte)

        if not reporte:
            raise BasedException(
                message=f"Reporte '{codigo_reporte}' no encontrado",
                status_code=status.HTTP_404_NOT_FOUND
            )

        if not reporte.activo:
            raise BasedException(
                message=f"El reporte '{codigo_reporte}' no está activo",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Obtener columnas
        columnas_data = await self.reportes_repo.get_columnas_reporte(codigo_reporte)
        columnas = [ReporteColumnaResponse(**col) for col in columnas_data]

        # Obtener datos
        datos, total_registros = await self.reportes_repo.get_reporte_data(
            vista_nombre=reporte.vista_nombre,
            campo_fecha=reporte.campo_fecha,
            filtros=filtros,
            page=page,
            page_size=page_size
        )

        # Calcular totales si hay columnas totalizables
        totales = None
        columnas_totalizables = await self.reportes_repo.get_columnas_totalizables(codigo_reporte)

        if columnas_totalizables:
            totales = await self.reportes_repo.get_totales_reporte(
                vista_nombre=reporte.vista_nombre,
                campo_fecha=reporte.campo_fecha,
                columnas_totalizables=columnas_totalizables,
                filtros=filtros
            )

        # Calcular paginación
        paginas_totales = (total_registros + page_size - 1) // page_size if total_registros > 0 else 1

        paginacion = PaginacionResponse(
            pagina_actual=page,
            paginas_totales=paginas_totales,
            registros_por_pagina=page_size,
            total_registros=total_registros
        )

        # Construir respuesta
        return ReporteDataResponse(
            reporte=ReporteInfoResponse(
                codigo=reporte.codigo,
                nombre=reporte.nombre,
                fecha_generacion=datetime.now(),
                filtros_aplicados=filtros
            ),
            columnas=columnas,
            datos=datos,
            totales=totales,
            paginacion=paginacion
        )

    # ========================================================
    # METADATA DE REPORTES
    # ========================================================

    async def obtener_metadata_reporte(
            self,
            codigo_reporte: str,
            rol_id: int
    ) -> ReporteMetadataResponse:
        """
        Obtiene los metadatos de un reporte (columnas, filtros disponibles, etc.)

        Args:
            codigo_reporte: Código del reporte
            rol_id: ID del rol del usuario

        Returns:
            ReporteMetadataResponse con toda la metadata

        Raises:
            BasedException: Si no tiene permisos o el reporte no existe
        """
        # Verificar acceso
        tiene_acceso = await self.reportes_repo.verificar_acceso(
            rol_id=rol_id,
            codigo_reporte=codigo_reporte
        )

        if not tiene_acceso:
            raise BasedException(
                message="No tiene permisos para acceder a este reporte",
                status_code=status.HTTP_403_FORBIDDEN
            )

        # Obtener reporte
        reporte = await self.reportes_repo.get_reporte_by_codigo(codigo_reporte)

        if not reporte:
            raise BasedException(
                message=f"Reporte '{codigo_reporte}' no encontrado",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Obtener columnas
        columnas_data = await self.reportes_repo.get_columnas_reporte(codigo_reporte)
        columnas = [ReporteColumnaResponse(**col) for col in columnas_data]

        # Obtener materiales para filtro
        materiales_data = []
        if reporte.permite_filtrar_material:
            materiales_data = await self.reportes_repo.get_materiales_filtro()

        materiales = [MaterialFiltroResponse(**mat) for mat in materiales_data]

        # Obtener rango de fechas
        rango_fechas_data = {"fecha_minima": None, "fecha_maxima": None}
        if reporte.requiere_rango_fechas:
            rango_fechas_data = await self.reportes_repo.get_rango_fechas_vista(
                vista_nombre=reporte.vista_nombre,
                campo_fecha=reporte.campo_fecha
            )

        rango_fechas = RangoFechasResponse(**rango_fechas_data)

        filtros_disponibles = FiltrosDisponiblesResponse(
            materiales=materiales,
            rango_fechas=rango_fechas
        )

        # Obtener campos totalizables
        columnas_totalizables = await self.reportes_repo.get_columnas_totalizables(codigo_reporte)
        totalizables = [col['campo'] for col in columnas_totalizables]

        return ReporteMetadataResponse(
            codigo=reporte.codigo,
            nombre=reporte.nombre,
            descripcion=reporte.descripcion,
            columnas=columnas,
            filtros_disponibles=filtros_disponibles,
            totalizables=totalizables
        )

    # ========================================================
    # VERIFICACIÓN DE PERMISOS
    # ========================================================

    async def verificar_permiso_exportacion(
            self,
            rol_id: int,
            codigo_reporte: str
    ) -> bool:
        """
        Verifica si un rol tiene permiso para exportar un reporte.

        Args:
            rol_id: ID del rol
            codigo_reporte: Código del reporte

        Returns:
            True si puede exportar
        """
        return await self.reportes_repo.verificar_acceso(
            rol_id=rol_id,
            codigo_reporte=codigo_reporte,
            requiere_exportacion=True
        )

    async def verificar_formato_exportacion(
            self,
            codigo_reporte: str,
            formato: str
    ) -> bool:
        """
        Verifica si un formato de exportación está permitido para un reporte.

        Args:
            codigo_reporte: Código del reporte
            formato: Formato de exportación (pdf, excel, csv)

        Returns:
            True si el formato está permitido
        """
        reporte = await self.reportes_repo.get_reporte_by_codigo(codigo_reporte)

        if not reporte:
            return False

        formato_lower = formato.lower()
        if formato_lower == 'pdf':
            return reporte.permite_exportar_pdf
        elif formato_lower == 'excel':
            return reporte.permite_exportar_excel
        elif formato_lower == 'csv':
            return reporte.permite_exportar_csv

        return False

    # ========================================================
    # OBTENER DATOS PARA EXPORTACIÓN
    # ========================================================

    async def obtener_datos_para_exportar(
            self,
            codigo_reporte: str,
            rol_id: int,
            filtros: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Obtiene todos los datos de un reporte para exportación (sin paginación).

        Args:
            codigo_reporte: Código del reporte
            rol_id: ID del rol del usuario
            filtros: Filtros a aplicar

        Returns:
            Diccionario con datos, columnas, totales y configuración del reporte

        Raises:
            BasedException: Si no tiene permisos de exportación
        """
        # Verificar permiso de exportación
        puede_exportar = await self.verificar_permiso_exportacion(rol_id, codigo_reporte)

        if not puede_exportar:
            raise BasedException(
                message="No tiene permisos para exportar este reporte",
                status_code=status.HTTP_403_FORBIDDEN
            )

        # Obtener reporte
        reporte = await self.reportes_repo.get_reporte_by_codigo(codigo_reporte)

        if not reporte:
            raise BasedException(
                message=f"Reporte '{codigo_reporte}' no encontrado",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Obtener columnas
        columnas = await self.reportes_repo.get_columnas_reporte(codigo_reporte)

        # Obtener TODOS los datos (sin límite práctico)
        datos, total = await self.reportes_repo.get_reporte_data(
            vista_nombre=reporte.vista_nombre,
            campo_fecha=reporte.campo_fecha,
            filtros=filtros,
            page=1,
            page_size=1000000  # Sin límite práctico
        )

        # Obtener totales
        totales = None
        columnas_totalizables = await self.reportes_repo.get_columnas_totalizables(codigo_reporte)

        if columnas_totalizables:
            totales = await self.reportes_repo.get_totales_reporte(
                vista_nombre=reporte.vista_nombre,
                campo_fecha=reporte.campo_fecha,
                columnas_totalizables=columnas_totalizables,
                filtros=filtros
            )

        return {
            "reporte": {
                "codigo": reporte.codigo,
                "nombre": reporte.nombre,
                "descripcion": reporte.descripcion
            },
            "columnas": columnas,
            "datos": datos,
            "totales": totales,
            "total_registros": total
        }

    # ========================================================
    # ADMINISTRACIÓN
    # ========================================================

    async def refrescar_vistas(self) -> None:
        """
        Refresca todas las vistas materializadas de reportes.
        """
        await self.reportes_repo.refresh_todas_vistas()

    async def refrescar_vista_reporte(self, codigo_reporte: str) -> None:
        """
        Refresca la vista materializada de un reporte específico.

        Args:
            codigo_reporte: Código del reporte

        Raises:
            BasedException: Si el reporte no existe
        """
        reporte = await self.reportes_repo.get_reporte_by_codigo(codigo_reporte)

        if not reporte:
            raise BasedException(
                message=f"Reporte '{codigo_reporte}' no encontrado",
                status_code=status.HTTP_404_NOT_FOUND
            )

        await self.reportes_repo.refresh_vista(reporte.vista_nombre)