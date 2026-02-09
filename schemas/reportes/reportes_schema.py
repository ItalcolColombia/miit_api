from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field, ConfigDict


# ============================================================
# ENUMS
# ============================================================

class FormatoExportacion(str, Enum):
    """Formatos de exportación disponibles"""
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"


class OrdenDireccion(str, Enum):
    """Dirección de ordenamiento"""
    ASC = "asc"
    DESC = "desc"


class TipoDato(str, Enum):
    """Tipos de datos para columnas"""
    STRING = "string"
    NUMBER = "number"
    DATE = "date"
    DATETIME = "datetime"
    BOOLEAN = "boolean"


class TipoTotalizacion(str, Enum):
    """Tipos de totalización"""
    SUM = "sum"
    AVG = "avg"
    COUNT = "count"
    MIN = "min"
    MAX = "max"


class CategoriaReporte(str, Enum):
    """Categorías de reportes"""
    OPERACIONAL = "operacional"
    INVENTARIO = "inventario"


class TipoFiltro(str, Enum):
    """Tipos de filtro para columnas"""
    SELECT = "select"
    SEARCH = "search"


# ============================================================
# SCHEMAS BASE
# ============================================================

class ReporteBase(BaseModel):
    """Schema base para Reporte"""
    codigo: str = Field(..., max_length=50, description="Código único del reporte")
    nombre: str = Field(..., max_length=200, description="Nombre del reporte")
    descripcion: Optional[str] = Field(None, description="Descripción del reporte")


class ReporteColumnaBase(BaseModel):
    """Schema base para columna de reporte"""
    campo: str = Field(..., max_length=100)
    nombre_mostrar: str = Field(..., max_length=200)
    tipo_dato: TipoDato


# ============================================================
# SCHEMAS DE FILTROS DINÁMICOS
# ============================================================

class OpcionFiltro(BaseModel):
    """Opción individual para filtros tipo select"""
    valor: str = Field(..., description="Valor de la opción")
    etiqueta: str = Field(..., description="Texto a mostrar")


class FiltroColumna(BaseModel):
    """Definición de un filtro de columna"""
    campo: str = Field(..., description="Nombre del campo en la vista")
    nombre_mostrar: str = Field(..., description="Etiqueta a mostrar en el UI")
    tipo_filtro: TipoFiltro = Field(..., description="Tipo de filtro: select o search")
    opciones: Optional[List[OpcionFiltro]] = Field(
        None,
        description="Opciones para filtros tipo select"
    )
    placeholder: Optional[str] = Field(
        None,
        description="Placeholder para filtros tipo search"
    )


# ============================================================
# SCHEMAS DE RESPUESTA
# ============================================================

class ReporteResponse(BaseModel):
    """Schema para respuesta de reporte"""
    id: int
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    vista_nombre: str
    campo_fecha: str
    icono: str
    orden: int
    color: str
    categoria: str
    permite_exportar_pdf: bool
    permite_exportar_excel: bool
    permite_exportar_csv: bool
    requiere_rango_fechas: bool
    permite_filtrar_material: bool
    activo: bool

    model_config = ConfigDict(from_attributes=True)


class ReporteConPermisosResponse(ReporteResponse):
    """Schema para reporte con información de permisos"""
    puede_ver: bool = False
    puede_exportar: bool = False


class ReporteColumnaResponse(BaseModel):
    """Schema para respuesta de columna"""
    campo: str
    nombre_mostrar: str
    tipo_dato: str
    orden: int
    visible: bool
    ordenable: bool
    filtrable: bool
    es_totalizable: bool
    tipo_totalizacion: Optional[str] = None
    alineacion: str
    formato: Optional[str] = None
    prefijo: Optional[str] = None
    sufijo: Optional[str] = None
    decimales: int
    ancho_minimo: int

    model_config = ConfigDict(from_attributes=True)


class MaterialFiltroResponse(BaseModel):
    """Schema para material en filtros"""
    id: int
    nombre: str
    codigo: str


class RangoFechasResponse(BaseModel):
    """Schema para rango de fechas disponible"""
    fecha_minima: Optional[datetime] = None
    fecha_maxima: Optional[datetime] = None


class FiltrosDisponiblesResponse(BaseModel):
    """Schema para filtros disponibles"""
    materiales: List[MaterialFiltroResponse] = []
    rango_fechas: RangoFechasResponse


class PaginacionResponse(BaseModel):
    """Schema para información de paginación"""
    pagina_actual: int
    paginas_totales: int
    registros_por_pagina: int
    total_registros: int


# ============================================================
# SCHEMAS DE LISTA DE REPORTES
# ============================================================

class ListaReportesResponse(BaseModel):
    """Schema para lista de reportes"""
    reportes: List[ReporteConPermisosResponse]
    total: int


# ============================================================
# SCHEMAS DE DATOS DE REPORTE
# ============================================================

class ReporteInfoResponse(BaseModel):
    """Información básica del reporte en la respuesta"""
    codigo: str
    nombre: str
    fecha_generacion: datetime
    filtros_aplicados: Dict[str, Any]


class ReporteDataResponse(BaseModel):
    """Schema para respuesta de consulta de reporte"""
    reporte: ReporteInfoResponse
    columnas: List[ReporteColumnaResponse]
    datos: List[Dict[str, Any]]
    totales: Optional[Dict[str, Any]] = None
    paginacion: PaginacionResponse


# ============================================================
# SCHEMAS DE METADATA
# ============================================================

class ReporteMetadataResponse(BaseModel):
    """Schema para metadata de un reporte"""
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    columnas: List[ReporteColumnaResponse]
    filtros_disponibles: FiltrosDisponiblesResponse
    totalizables: List[str]
    filtros_columnas: List[FiltroColumna] = Field(
        default=[],
        description="Filtros dinámicos disponibles para las columnas del reporte"
    )

# ============================================================
# SCHEMAS DE REQUEST (Query Parameters)
# ============================================================

class FiltrosReporteRequest(BaseModel):
    """Schema para filtros de reporte"""
    material_id: Optional[int] = Field(None, description="ID del material para filtrar")
    fecha_inicio: Optional[datetime] = Field(None, description="Fecha inicial del rango")
    fecha_fin: Optional[datetime] = Field(None, description="Fecha final del rango")
    orden_campo: Optional[str] = Field(None, description="Campo para ordenar")
    orden_direccion: OrdenDireccion = Field(OrdenDireccion.DESC, description="Dirección de orden")

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario excluyendo valores None"""
        return {k: v for k, v in self.model_dump().items() if v is not None}


class ConsultaReporteRequest(FiltrosReporteRequest):
    """Schema para consulta de reporte con paginación"""
    page: int = Field(1, ge=1, description="Número de página")
    page_size: int = Field(50, ge=1, le=500, description="Registros por página")


# ============================================================
# SCHEMAS DE PERMISOS
# ============================================================

class PermisoReporteBase(BaseModel):
    """Schema base para permiso de reporte"""
    codigo_reporte: str = Field(..., max_length=50)
    puede_ver: bool = True
    puede_exportar: bool = True


class PermisoReporteCreate(PermisoReporteBase):
    """Schema para crear permiso de reporte"""
    rol_id: int


class PermisoReporteUpdate(BaseModel):
    """Schema para actualizar permiso de reporte"""
    puede_ver: Optional[bool] = None
    puede_exportar: Optional[bool] = None


class PermisoReporteResponse(PermisoReporteBase):
    """Schema para respuesta de permiso"""
    id: int
    rol_id: int
    fecha_hora: datetime

    model_config = ConfigDict(from_attributes=True)


class AsignarPermisosRequest(BaseModel):
    """Schema para asignar múltiples permisos"""
    permisos_reportes: List[PermisoReporteBase]


class PermisosRolResponse(BaseModel):
    """Schema para permisos de un rol"""
    rol_id: int
    rol_nombre: str
    permisos: List[PermisoReporteResponse]
    total_reportes: int
    reportes_con_acceso: int


# ============================================================
# SCHEMAS DE EXPORTACIÓN
# ============================================================

class ExportacionRequest(BaseModel):
    """Schema para solicitud de exportación"""
    formato: FormatoExportacion
    filtros: Optional[FiltrosReporteRequest] = None


class ExportacionResponse(BaseModel):
    """Schema para respuesta de exportación (metadata)"""
    nombre_archivo: str
    formato: FormatoExportacion
    registros_exportados: int
    fecha_generacion: datetime


# ============================================================
# SCHEMAS DE ADMINISTRACIÓN
# ============================================================

class ReporteCreate(ReporteBase):
    """Schema para crear un reporte"""
    vista_nombre: str = Field(..., max_length=100)
    campo_fecha: str = Field("fecha", max_length=50)
    icono: str = Field("assessment", max_length=50)
    orden: int = Field(0)
    color: str = Field("#1976d2", max_length=20)
    categoria: CategoriaReporte = CategoriaReporte.OPERACIONAL
    permite_exportar_pdf: bool = True
    permite_exportar_excel: bool = True
    permite_exportar_csv: bool = True
    requiere_rango_fechas: bool = True
    permite_filtrar_material: bool = True


class ReporteUpdate(BaseModel):
    """Schema para actualizar un reporte"""
    nombre: Optional[str] = Field(None, max_length=200)
    descripcion: Optional[str] = None
    icono: Optional[str] = Field(None, max_length=50)
    orden: Optional[int] = None
    color: Optional[str] = Field(None, max_length=20)
    categoria: Optional[CategoriaReporte] = None
    permite_exportar_pdf: Optional[bool] = None
    permite_exportar_excel: Optional[bool] = None
    permite_exportar_csv: Optional[bool] = None
    requiere_rango_fechas: Optional[bool] = None
    permite_filtrar_material: Optional[bool] = None
    activo: Optional[bool] = None


class ReporteColumnaCreate(ReporteColumnaBase):
    """Schema para crear columna de reporte"""
    reporte_id: int
    visible: bool = True
    orden: int = 0
    ancho_minimo: int = 100
    alineacion: str = "left"
    ordenable: bool = True
    filtrable: bool = False
    formato: Optional[str] = None
    prefijo: Optional[str] = None
    sufijo: Optional[str] = None
    decimales: int = 2
    es_totalizable: bool = False
    tipo_totalizacion: Optional[TipoTotalizacion] = None


class ReporteColumnaUpdate(BaseModel):
    """Schema para actualizar columna de reporte"""
    nombre_mostrar: Optional[str] = Field(None, max_length=200)
    visible: Optional[bool] = None
    orden: Optional[int] = None
    ordenable: Optional[bool] = None
    filtrable: Optional[bool] = None
    es_totalizable: Optional[bool] = None
    tipo_totalizacion: Optional[TipoTotalizacion] = None