import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

from fastapi import status

from core.config.filtros_reportes_config import (
    get_filtros_reporte,
    get_campos_filtro_validos,
    get_operadores_permitidos_por_campo,
)
from core.exceptions.base_exception import BasedException
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
from utils.time_util import now_local

logger = logging.getLogger(__name__)

OPERADORES_VALIDOS = {"eq", "ne", "gte", "lte", "in", "contains", "is_null", "is_not_null"}


class ReportesService:
    """
    Servicio para la lógica de negocio de reportes.
    Coordina entre el repositorio y los endpoints.
    """

    def __init__(self, reportes_repo: ReportesRepository):
        self.reportes_repo = reportes_repo

    @staticmethod
    def _build_filter_error(code: str, message: str, detail: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "code": code,
            "message": message,
            "detail": detail,
        }

    @staticmethod
    def _parse_bool_value(value: Any) -> bool:
        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            lower = value.strip().lower()
            if lower == "true":
                return True
            if lower == "false":
                return False

        raise ValueError("boolean inválido")

    @staticmethod
    def _try_parse_datetime_value(value: Any) -> Any:
        if isinstance(value, datetime):
            if value.tzinfo is not None:
                return value.replace(tzinfo=None)
            return value

        if isinstance(value, str):
            try:
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                if dt.tzinfo is not None:
                    dt = dt.replace(tzinfo=None)
                return dt
            except ValueError:
                return value

        return value

    def _parse_filter_value(self, operador: str, valor: Any) -> Any:
        if operador == "in":
            if isinstance(valor, str):
                parts = [part.strip() for part in valor.split(",") if part.strip()]
            elif isinstance(valor, list):
                parts = valor
            else:
                raise ValueError("valor inválido para operador in")

            if not parts:
                raise ValueError("lista vacía para operador in")

            parsed = []
            for part in parts:
                try:
                    parsed.append(self._parse_bool_value(part))
                except ValueError:
                    parsed.append(part)
            return parsed

        if operador in {"is_null", "is_not_null"}:
            parsed_bool = self._parse_bool_value(valor)
            if parsed_bool is not True:
                raise ValueError("is_null/is_not_null requiere valor true")
            return True

        if operador in {"eq", "ne"}:
            try:
                return self._parse_bool_value(valor)
            except ValueError:
                return valor

        if operador in {"gte", "lte"}:
            return self._try_parse_datetime_value(valor)

        return valor

    def _normalizar_filtros_dinamicos(
            self,
            codigo_reporte: str,
            filtros: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Normaliza filtros dinámicos legacy y explícitos hacia una estructura
        única basada en operadores.
        """
        filtros_norm = filtros.copy()

        filtros_legacy = filtros_norm.get('filtros_columna', {}) or {}
        filtros_explicitos = filtros_norm.get('filtros_explicitos', {}) or {}

        campos_validos = get_campos_filtro_validos(codigo_reporte)
        operadores_por_campo = get_operadores_permitidos_por_campo(codigo_reporte)
        filtros_config = get_filtros_reporte(codigo_reporte)
        tipo_por_campo = {f.campo: f.tipo_filtro for f in filtros_config}

        filtros_operadores: List[Dict[str, Any]] = []

        for campo, valor in filtros_legacy.items():
            if campo not in campos_validos:
                raise BasedException(
                    message=self._build_filter_error(
                        code="INVALID_FILTER_VALUE",
                        message="Campo de filtro no permitido para este reporte",
                        detail={"campo": campo, "valor": valor}
                    ),
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            operador_default = "contains" if tipo_por_campo.get(campo) == "search" else "eq"
            if operador_default not in operadores_por_campo.get(campo, []):
                operador_default = "eq"

            try:
                parsed_value = self._parse_filter_value(operador_default, valor)
            except ValueError as exc:
                raise BasedException(
                    message=self._build_filter_error(
                        code="INVALID_FILTER_VALUE",
                        message="Valor de filtro inválido",
                        detail={"campo": campo, "operador": operador_default, "valor": valor, "error": str(exc)}
                    ),
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            filtros_operadores.append({
                "campo": campo,
                "operador": operador_default,
                "valor": parsed_value
            })

        for campo, operadores in filtros_explicitos.items():
            if campo not in campos_validos:
                raise BasedException(
                    message=self._build_filter_error(
                        code="INVALID_FILTER_VALUE",
                        message="Campo de filtro no permitido para este reporte",
                        detail={"campo": campo, "valor": operadores}
                    ),
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            for operador, valor in (operadores or {}).items():
                operador_norm = str(operador).strip().lower()
                if operador_norm not in OPERADORES_VALIDOS:
                    raise BasedException(
                        message=self._build_filter_error(
                            code="INVALID_FILTER_OPERATOR",
                            message="Operador de filtro inválido",
                            detail={"campo": campo, "operador": operador}
                        ),
                        status_code=status.HTTP_400_BAD_REQUEST
                    )

                permitidos = operadores_por_campo.get(campo, [])
                if operador_norm not in permitidos:
                    raise BasedException(
                        message=self._build_filter_error(
                            code="INVALID_FILTER_OPERATOR",
                            message="Operador no permitido para el campo",
                            detail={"campo": campo, "operador": operador_norm, "permitidos": permitidos}
                        ),
                        status_code=status.HTTP_400_BAD_REQUEST
                    )

                try:
                    parsed_value = self._parse_filter_value(operador_norm, valor)
                except ValueError as exc:
                    raise BasedException(
                        message=self._build_filter_error(
                            code="INVALID_FILTER_VALUE",
                            message="Valor de filtro inválido",
                            detail={"campo": campo, "operador": operador_norm, "valor": valor, "error": str(exc)}
                        ),
                        status_code=status.HTTP_400_BAD_REQUEST
                    )

                filtros_operadores.append({
                    "campo": campo,
                    "operador": operador_norm,
                    "valor": parsed_value
                })

        filtros_norm['filtros_operadores'] = filtros_operadores
        return filtros_norm

    def _aplicar_regla_permanencia_activa(
            self,
            codigo_reporte: str,
            filtros: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Para RPT_PERMANENCIA + en_puerto=true fuerza filtros de activos del día UTC.
        """
        if codigo_reporte != "RPT_PERMANENCIA":
            return filtros

        filtros_actualizados = filtros.copy()
        filtros_operadores = list(filtros_actualizados.get('filtros_operadores', []))

        en_puerto_activo = any(
            f.get('campo') == 'en_puerto' and f.get('operador') == 'eq' and f.get('valor') is True
            for f in filtros_operadores
        )

        if not en_puerto_activo:
            return filtros_actualizados

        filtros_salida = [
            f for f in filtros_operadores if f.get('campo') == 'fecha_salida_puerto'
        ]
        for filtro in filtros_salida:
            if not (filtro.get('operador') == 'is_null' and filtro.get('valor') is True):
                raise BasedException(
                    message=self._build_filter_error(
                        code="CONFLICTING_FILTERS",
                        message="Conflicto con regla de permanencia activa",
                        detail={
                            "campo": "fecha_salida_puerto",
                            "filtro_conflictivo": filtro,
                            "regla": "en_puerto=true requiere fecha_salida_puerto IS NULL"
                        }
                    ),
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        ahora_utc = datetime.now(timezone.utc)
        inicio_dia_utc = datetime(
            year=ahora_utc.year,
            month=ahora_utc.month,
            day=ahora_utc.day,
            tzinfo=timezone.utc
        ).replace(tzinfo=None)
        fin_dia_utc = (inicio_dia_utc + timedelta(days=1)) - timedelta(milliseconds=1)

        filtros_operadores = [
            f for f in filtros_operadores
            if f.get('campo') not in {'fecha_llegada_puerto', 'fecha_salida_puerto'}
        ]

        filtros_operadores.extend([
            {"campo": "fecha_llegada_puerto", "operador": "gte", "valor": inicio_dia_utc},
            {"campo": "fecha_llegada_puerto", "operador": "lte", "valor": fin_dia_utc},
            {"campo": "fecha_salida_puerto", "operador": "is_null", "valor": True},
        ])

        filtros_actualizados['filtros_operadores'] = filtros_operadores
        return filtros_actualizados

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
        filtros_normalizados = self._normalizar_filtros_dinamicos(codigo_reporte, filtros_normalizados)
        filtros_normalizados = self._aplicar_regla_permanencia_activa(codigo_reporte, filtros_normalizados)
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

            if filtros_normalizados.get('orden_campo'):
                campos_ordenables = {col.campo for col in columnas if col.ordenable}
                if filtros_normalizados['orden_campo'] not in campos_ordenables:
                    raise BasedException(
                        message=self._build_filter_error(
                            code="INVALID_FILTER_VALUE",
                            message="Campo de ordenamiento no permitido",
                            detail={"campo": filtros_normalizados['orden_campo']}
                        ),
                        status_code=status.HTTP_400_BAD_REQUEST
                    )

            # Agregar codigo_reporte a filtros para que el repositorio pueda determinar tipos de filtro
            filtros_normalizados['codigo_reporte'] = codigo_reporte

            # Obtener columnas totalizables (antes de get_reporte_data)
            columnas_totalizables = await self.reportes_repo.get_columnas_totalizables(codigo_reporte)

            # Obtener datos
            datos, total_registros = await self.reportes_repo.get_reporte_data(
                vista_nombre=reporte.vista_nombre,
                campo_fecha=reporte.campo_fecha,
                filtros=filtros_normalizados,
                page=page,
                page_size=page_size,
                campos_agrupacion=reporte.campos_agrupacion,
                columnas_totalizables=columnas_totalizables if reporte.campos_agrupacion else None,
                tipo_consulta=reporte.tipo_consulta or 'normal'
            )
            logger.debug(f"Datos obtenidos: {total_registros} registros")

            # Calcular totales si hay columnas totalizables
            totales = None

            if columnas_totalizables:
                totales = await self.reportes_repo.get_totales_reporte(
                    vista_nombre=reporte.vista_nombre,
                    campo_fecha=reporte.campo_fecha,
                    columnas_totalizables=columnas_totalizables,
                    filtros=filtros_normalizados,
                    tipo_consulta=reporte.tipo_consulta or 'normal',
                    campos_agrupacion=reporte.campos_agrupacion
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
                    fecha_generacion=now_local(),
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
                tipo_filtro=TipoFiltro(config.tipo_filtro),
                operadores_permitidos=config.operadores_permitidos,
                tipo_dato_filtro=config.tipo_dato_filtro
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
        filtros_normalizados = self._normalizar_filtros_dinamicos(codigo_reporte, filtros_normalizados)
        filtros_normalizados = self._aplicar_regla_permanencia_activa(codigo_reporte, filtros_normalizados)
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

        columnas_totalizables = await self.reportes_repo.get_columnas_totalizables(codigo_reporte)

        # Obtener TODOS los datos (sin límite práctico)
        datos, total = await self.reportes_repo.get_reporte_data(
            vista_nombre=reporte.vista_nombre,
            campo_fecha=reporte.campo_fecha,
            filtros=filtros_normalizados,
            page=1,
            page_size=1000000,  # Sin límite práctico
            campos_agrupacion=reporte.campos_agrupacion,
            columnas_totalizables=columnas_totalizables if reporte.campos_agrupacion else None,
            tipo_consulta=reporte.tipo_consulta or 'normal'
        )

        # Obtener totales
        totales = None

        if columnas_totalizables:
            totales = await self.reportes_repo.get_totales_reporte(
                vista_nombre=reporte.vista_nombre,
                campo_fecha=reporte.campo_fecha,
                columnas_totalizables=columnas_totalizables,
                filtros=filtros_normalizados,
                tipo_consulta=reporte.tipo_consulta or 'normal',
                campos_agrupacion=reporte.campos_agrupacion
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