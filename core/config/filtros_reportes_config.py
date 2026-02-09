"""
Configuración de filtros dinámicos por reporte.

Este archivo define qué columnas son filtrables para cada reporte
y el tipo de filtro a usar (select o search).
"""
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class FiltroConfig:
    """Configuración de un filtro individual"""
    campo: str
    nombre_mostrar: str
    tipo_filtro: str  # "select" o "search"
    placeholder: str = None  # Solo para tipo "search"


# ============================================================
# CONFIGURACIÓN DE FILTROS POR REPORTE
# ============================================================

FILTROS_POR_REPORTE: Dict[str, List[FiltroConfig]] = {
    "RPT_BASCULA": [
        FiltroConfig("origen", "Origen", "select"),
        FiltroConfig("codigo_material", "Código Material", "select"),
        FiltroConfig("material", "Material", "search", "Buscar por nombre de material..."),
        FiltroConfig("placa", "Placa", "search", "Buscar por placa..."),
    ],

    "RPT_RECIBIDO_DESPACHADO": [
        FiltroConfig("buque", "Buque", "select"),
        FiltroConfig("codigo_material", "Código Material", "select"),
        FiltroConfig("material", "Material", "search", "Buscar por nombre de material..."),
    ],

    "RPT_SALDOS": [
        FiltroConfig("nombre_almacenamiento", "Almacenamiento", "select"),
        FiltroConfig("codigo_material", "Código Material", "select"),
        FiltroConfig("material", "Material", "search", "Buscar por nombre de material..."),
    ],

    "RPT_AJUSTES": [
        FiltroConfig("nombre_almacenamiento", "Almacenamiento", "select"),
        FiltroConfig("codigo_material", "Código Material", "select"),
        FiltroConfig("material", "Material", "search", "Buscar por nombre de material..."),
    ],

    "RPT_DESPACHO_CAMION": [
        FiltroConfig("nombre_almacenamiento", "Almacenamiento", "select"),
        FiltroConfig("buque", "Buque", "select"),
        FiltroConfig("codigo_material", "Código Material", "select"),
        FiltroConfig("material", "Material", "search", "Buscar por nombre de material..."),
        FiltroConfig("placa", "Placa", "search", "Buscar por placa..."),
    ],

    "RPT_RECEPCION": [
        FiltroConfig("nombre_almacenamiento", "Almacenamiento", "select"),
        FiltroConfig("buque", "Buque", "select"),
        FiltroConfig("cliente", "Cliente", "search", "Buscar por cliente..."),
        FiltroConfig("no_bl", "No. BL", "search", "Buscar por número de BL..."),
        FiltroConfig("codigo_material", "Código Material", "select"),
        FiltroConfig("material", "Material", "search", "Buscar por nombre de material..."),
    ],

    "RPT_TRASLADOS": [
        FiltroConfig("codigo_material", "Código Material", "select"),
        FiltroConfig("nombre_material", "Material", "search", "Buscar por nombre de material..."),
        FiltroConfig("almacenamiento_origen", "Almacenamiento Origen", "select"),
        FiltroConfig("almacenamiento_destino", "Almacenamiento Destino", "select"),
    ],

    "RPT_PESADAS": [
        FiltroConfig("tipo_transaccion", "Tipo Transacción", "select"),
        FiltroConfig("flota", "Flota", "search", "Buscar por flota..."),
        FiltroConfig("no_bl", "No. BL", "search", "Buscar por número de BL..."),
        FiltroConfig("nombre_almacenamiento", "Almacenamiento", "select"),
        FiltroConfig("codigo_material", "Código Material", "select"),
        FiltroConfig("material", "Material", "search", "Buscar por nombre de material..."),
    ],
}


def get_filtros_reporte(codigo_reporte: str) -> List[FiltroConfig]:
    """
    Obtiene la configuración de filtros para un reporte específico.

    Args:
        codigo_reporte: Código del reporte

    Returns:
        Lista de configuraciones de filtros o lista vacía si no hay
    """
    return FILTROS_POR_REPORTE.get(codigo_reporte, [])


def get_campos_filtro_validos(codigo_reporte: str) -> set:
    """
    Obtiene el conjunto de campos válidos para filtrar en un reporte.

    Args:
        codigo_reporte: Código del reporte

    Returns:
        Set con los nombres de los campos filtrables
    """
    filtros = get_filtros_reporte(codigo_reporte)
    return {f.campo for f in filtros}
