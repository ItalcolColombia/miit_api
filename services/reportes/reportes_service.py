from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import status
import logging

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
    ListaReportesResponse,
    FiltroColumna,
    OpcionFiltro,
    TipoFiltro
)
from core.exceptions.base_exception import BasedException
from core.config.filtros_reportes_config import get_filtros_reporte, get_campos_filtro_validos

logger = logging.getLogger(__name__)


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

        reportes = []
        for reporte in reportes_data:
            # Deshabilitar temporalmente Excel
            reporte['permite_exportar_excel'] = False
            reportes.append(ReporteConPermisosResponse(**reporte))

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
        reportes = []
        for reporte in reportes_data:
            if reporte.get('puede_ver', False):
                # Deshabilitar temporalmente Excel
                reporte['permite_exportar_excel'] = False
                reportes.append(ReporteConPermisosResponse(**reporte))

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
        logger.info(f"Consultando reporte {codigo_reporte} con filtros: {filtros}")

        # Normalizar fechas en filtros (convertir datetime con timezone a naive datetime)
        filtros_normalizados = self._normalizar_filtros_fecha(filtros)
        logger.debug(f"Filtros normalizados: {filtros_normalizados}")

        try:
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

            # Agregar codigo_reporte a filtros para que el repositorio pueda determinar tipos de filtro
            filtros_normalizados['codigo_reporte'] = codigo_reporte

            # Obtener datos
            datos, total_registros = await self.reportes_repo.get_reporte_data(
                vista_nombre=reporte.vista_nombre,
                campo_fecha=reporte.campo_fecha,
                filtros=filtros_normalizados,
                page=page,
                page_size=page_size
            )
            logger.debug(f"Datos obtenidos: {total_registros} registros")

            # Calcular totales si hay columnas totalizables
            totales = None
            columnas_totalizables = await self.reportes_repo.get_columnas_totalizables(codigo_reporte)

            if columnas_totalizables:
                totales = await self.reportes_repo.get_totales_reporte(
                    vista_nombre=reporte.vista_nombre,
                    campo_fecha=reporte.campo_fecha,
                    columnas_totalizables=columnas_totalizables,
                    filtros=filtros_normalizados
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
        except BasedException:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo datos del reporte {codigo_reporte}: {e}", exc_info=True)
            raise BasedException(
                message=f"Error al consultar el reporte: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _normalizar_filtros_fecha(self, filtros: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza los filtros de fecha para asegurar compatibilidad con PostgreSQL.
        Convierte datetime con timezone a datetime naive (sin timezone).

        Args:
            filtros: Diccionario de filtros original

        Returns:
            Diccionario de filtros con fechas normalizadas
        """
        filtros_norm = filtros.copy()

        for campo in ['fecha_inicio', 'fecha_fin']:
            if campo in filtros_norm and filtros_norm[campo] is not None:
                valor = filtros_norm[campo]
                if isinstance(valor, datetime):
                    # Si tiene timezone, convertir a naive datetime (UTC)
                    if valor.tzinfo is not None:
                        valor = valor.replace(tzinfo=None)
                    filtros_norm[campo] = valor
                elif isinstance(valor, str):
                    # Intentar parsear la fecha string
                    try:
                        # Manejar formato ISO con Z
                        valor_str = valor.replace('Z', '+00:00')
                        dt = datetime.fromisoformat(valor_str)
                        # Convertir a naive datetime
                        if dt.tzinfo is not None:
                            dt = dt.replace(tzinfo=None)
                        filtros_norm[campo] = dt
                    except (ValueError, AttributeError) as e:
                        logger.warning(f"No se pudo parsear fecha {campo}={valor}: {e}")
                        # Mantener el valor original si falla el parseo

        return filtros_norm

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
        logger.info(f"Obteniendo metadata para reporte: {codigo_reporte}")

        # Verificar acceso
        try:
            tiene_acceso = await self.reportes_repo.verificar_acceso(
                rol_id=rol_id,
                codigo_reporte=codigo_reporte
            )

            if not tiene_acceso:
                raise BasedException(
                    message="No tiene permisos para acceder a este reporte",
                    status_code=status.HTTP_403_FORBIDDEN
                )
        except BasedException:
            raise
        except Exception as e:
            logger.error(f"Error verificando acceso para {codigo_reporte}: {e}", exc_info=True)
            raise BasedException(
                message=f"Error verificando permisos: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Obtener reporte
        try:
            reporte = await self.reportes_repo.get_reporte_by_codigo(codigo_reporte)

            if not reporte:
                raise BasedException(
                    message=f"Reporte '{codigo_reporte}' no encontrado",
                    status_code=status.HTTP_404_NOT_FOUND
                )
        except BasedException:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo reporte {codigo_reporte}: {e}", exc_info=True)
            raise BasedException(
                message=f"Error obteniendo configuración del reporte: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Obtener columnas - manejar caso de lista vacía
        columnas = []
        try:
            columnas_data = await self.reportes_repo.get_columnas_reporte(codigo_reporte)
            columnas = [ReporteColumnaResponse(**col) for col in columnas_data]
            logger.debug(f"Columnas obtenidas para {codigo_reporte}: {len(columnas)}")
        except Exception as e:
            logger.warning(f"Error obteniendo columnas para {codigo_reporte}: {e}")
            # Continuar con lista vacía de columnas

        # Obtener materiales para filtro con manejo de errores
        materiales = []
        try:
            if reporte.permite_filtrar_material:
                materiales_data = await self.reportes_repo.get_materiales_filtro()
                materiales = [MaterialFiltroResponse(**mat) for mat in materiales_data]
                logger.debug(f"Materiales disponibles para filtro: {len(materiales)}")
        except Exception as e:
            logger.warning(f"Error obteniendo materiales para filtro en {codigo_reporte}: {e}")
            # Continuar con lista vacía de materiales

        # Obtener rango de fechas con manejo de errores
        rango_fechas = RangoFechasResponse(fecha_minima=None, fecha_maxima=None)
        try:
            if reporte.requiere_rango_fechas and reporte.vista_nombre and reporte.campo_fecha:
                rango_fechas_data = await self.reportes_repo.get_rango_fechas_vista(
                    vista_nombre=reporte.vista_nombre,
                    campo_fecha=reporte.campo_fecha
                )
                rango_fechas = RangoFechasResponse(**rango_fechas_data)
                logger.debug(f"Rango de fechas para {codigo_reporte}: {rango_fechas_data}")
        except Exception as e:
            logger.warning(f"Error obteniendo rango de fechas para {codigo_reporte}: {e}")
            # Continuar con rango de fechas vacío

        filtros_disponibles = FiltrosDisponiblesResponse(
            materiales=materiales,
            rango_fechas=rango_fechas
        )

        # Obtener campos totalizables con manejo de errores
        totalizables = []
        try:
            columnas_totalizables = await self.reportes_repo.get_columnas_totalizables(codigo_reporte)
            totalizables = [col['campo'] for col in columnas_totalizables]
            logger.debug(f"Campos totalizables para {codigo_reporte}: {totalizables}")
        except Exception as e:
            logger.warning(f"Error obteniendo campos totalizables para {codigo_reporte}: {e}")
            # Continuar con lista vacía

        # Obtener filtros dinámicos de columnas
        filtros_columnas = []
        try:
            filtros_columnas = await self._obtener_filtros_columnas(
                codigo_reporte=codigo_reporte,
                vista_nombre=reporte.vista_nombre
            )
            logger.debug(f"Filtros columnas para {codigo_reporte}: {len(filtros_columnas)} filtros")
        except Exception as e:
            logger.warning(f"Error obteniendo filtros columnas para {codigo_reporte}: {e}")
            # Continuar con lista vacía

        logger.info(f"Metadata obtenida exitosamente para {codigo_reporte}")

        return ReporteMetadataResponse(
            codigo=reporte.codigo,
            nombre=reporte.nombre,
            descripcion=reporte.descripcion,
            columnas=columnas,
            filtros_disponibles=filtros_disponibles,
            totalizables=totalizables,
            filtros_columnas=filtros_columnas
        )

    async def _obtener_filtros_columnas(
            self,
            codigo_reporte: str,
            vista_nombre: str
    ) -> List[FiltroColumna]:
        """
        Obtiene la lista de filtros dinámicos para un reporte.

        Args:
            codigo_reporte: Código del reporte
            vista_nombre: Nombre de la vista del reporte

        Returns:
            Lista de FiltroColumna con opciones para filtros select
        """
        filtros_config = get_filtros_reporte(codigo_reporte)

        if not filtros_config:
            return []

        filtros_columnas = []

        for config in filtros_config:
            filtro = FiltroColumna(
                campo=config.campo,
                nombre_mostrar=config.nombre_mostrar,
                tipo_filtro=TipoFiltro(config.tipo_filtro)
            )

            if config.tipo_filtro == "select":
                # Obtener valores únicos para opciones
                try:
                    opciones_data = await self.reportes_repo.get_valores_unicos_columna(
                        vista_nombre=vista_nombre,
                        campo=config.campo
                    )
                    filtro.opciones = [
                        OpcionFiltro(valor=opt["valor"], etiqueta=opt["etiqueta"])
                        for opt in opciones_data
                    ]
                except Exception as e:
                    logger.warning(f"Error obteniendo opciones para {config.campo}: {e}")
                    filtro.opciones = []
            elif config.tipo_filtro == "search":
                filtro.placeholder = config.placeholder

            filtros_columnas.append(filtro)

        return filtros_columnas

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
        logger.info(f"Exportando reporte {codigo_reporte} con filtros: {filtros}")

        # Normalizar fechas en filtros
        filtros_normalizados = self._normalizar_filtros_fecha(filtros)
        logger.debug(f"Filtros normalizados para exportación: {filtros_normalizados}")

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

        # Agregar codigo_reporte a filtros para determinar tipos de filtro dinámico
        filtros_normalizados['codigo_reporte'] = codigo_reporte

        # Obtener TODOS los datos (sin límite práctico)
        datos, total = await self.reportes_repo.get_reporte_data(
            vista_nombre=reporte.vista_nombre,
            campo_fecha=reporte.campo_fecha,
            filtros=filtros_normalizados,
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
                filtros=filtros_normalizados
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