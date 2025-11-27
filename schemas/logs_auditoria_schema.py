from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import Field, ConfigDict

from schemas.base_schema import BaseSchema


class LogsAuditoriaResponse(BaseSchema):
    id: int
    entidad: str
    entidad_id: int
    accion: str
    valor_anterior: Dict[str, Any] = None
    valor_nuevo: Dict[str, Any] = None
    fecha_hora: Optional[datetime] = None
    usuario_id: int = None

    model_config = ConfigDict(from_attributes=True)

class LogsAuditoriaCreate(BaseSchema):
    entidad: str
    entidad_id: int
    accion: str
    valor_anterior: Optional[Dict[str, Any]] = None
    valor_nuevo: Optional[Dict[str, Any]] = None
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "entidad": "material",
                "entidad_id": "22",
                "accion" : "UPDATE",
                "valor_anterior": "TEST",
                "valor_nuevo": "TESTEO",
                "fecha_hora" : "2025-05-02 20:04:55",
                "usuario_id": "1",
            }
        }

class LogsAuditoriaUpdate(BaseSchema):
    entidad: Optional[str] = Field(None, max_length=100)
    entidad_id: Optional[int] = None
    accion: Optional[str] = Field(None, max_length=30)
    valor_anterior: Optional[Dict[str, Any]] = Field(None, max_length=30)
    valor_nuevo: Optional[Dict[str, Any]] = Field(None, max_length=30)
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None

