"""
Schemas para administración de roles.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime


# ============================================================
# SCHEMAS DE RESPUESTA
# ============================================================

class RolAdminResponse(BaseModel):
    """Schema para respuesta de rol en administración"""
    id: int
    nombre: str
    estado: bool
    cantidad_usuarios: int = 0
    permisos_reportes: List[str] = []

    model_config = ConfigDict(from_attributes=True)


class RolesListResponse(BaseModel):
    """Schema para lista de roles"""
    roles: List[RolAdminResponse]


class PermisoReporteAdminResponse(BaseModel):
    """Schema para permiso de reporte en administración"""
    id: int
    rol_id: int
    codigo_reporte: str
    puede_ver: bool
    puede_exportar: bool
    fecha_hora: datetime

    model_config = ConfigDict(from_attributes=True)


class PermisosRolListResponse(BaseModel):
    """Schema para lista de permisos de un rol"""
    permisos: List[PermisoReporteAdminResponse]


# ============================================================
# SCHEMAS DE REQUEST
# ============================================================

class RolCreateRequest(BaseModel):
    """Schema para crear un rol"""
    nombre: str = Field(..., min_length=1, max_length=100, description="Nombre del rol")
    estado: bool = Field(True, description="Estado del rol (activo/inactivo)")


class RolUpdateRequest(BaseModel):
    """Schema para actualizar un rol"""
    nombre: Optional[str] = Field(None, min_length=1, max_length=100, description="Nuevo nombre del rol")
    estado: Optional[bool] = Field(None, description="Nuevo estado del rol")


class PermisoReporteRequest(BaseModel):
    """Schema para un permiso de reporte individual"""
    codigo_reporte: str = Field(..., description="Código del reporte")
    puede_ver: bool = Field(False, description="Si el rol puede ver el reporte")
    puede_exportar: bool = Field(False, description="Si el rol puede exportar el reporte")


class AsignarPermisosRolRequest(BaseModel):
    """Schema para asignar permisos a un rol"""
    permisos_reportes: List[PermisoReporteRequest] = Field(
        ...,
        description="Lista de permisos a asignar"
    )


# ============================================================
# SCHEMAS DE MENSAJES
# ============================================================

class MessageResponse(BaseModel):
    """Schema para respuestas de mensaje simple"""
    message: str
