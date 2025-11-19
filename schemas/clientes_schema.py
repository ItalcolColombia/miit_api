from datetime import datetime
from typing import Optional

from pydantic import Field, ConfigDict

from schemas.base_schema import BaseSchema


class ClientesResponse(BaseSchema):
    id: int
    tipo_idetificacion: str
    num_identificacion: Optional[int] = None
    razon_social: str = Field(..., max_length=100)
    primer_nombre: Optional[str] = Field(None, max_length=30)
    segundo_nombre: Optional[str] = Field(None, max_length=30)
    primer_apellido: Optional[str] = Field(None, max_length=30)
    segundo_apellido: Optional[str] = Field(None, max_length=30)
    id_actividad: Optional[int] = None
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class ClienteCreate(BaseSchema):
    tipo_idetificacion: str
    num_identificacion: Optional[int] = None
    razon_social: str = Field(..., max_length=100)
    primer_nombre: Optional[str] = Field(None, max_length=30)
    segundo_nombre: Optional[str] = Field(None, max_length=30)
    primer_apellido: Optional[str] = Field(None, max_length=30)
    segundo_apellido: Optional[str] = Field(None, max_length=30)
    id_actividad: Optional[int] = None
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "tipo_id": "cc",
                "num_identificacion": "1098444130",
                "razon_social" : "COSME FULANITO",
                "primer_nombre": "Cosme",
                "segundo_nombre": None,
                "primer_apellido": "Fulanito",
                "segundo_apellido": None,
                "id_actividad": "999",
            }
        }

class ClienteUpdate(BaseSchema):
    razon_social: Optional[str] = Field(None, max_length=100)
    primer_nombre: Optional[str] = Field(None, max_length=30)
    segundo_nombre: Optional[str] = Field(None, max_length=30)
    primer_apellido: Optional[str] = Field(None, max_length=30)
    segundo_apellido: Optional[str] = Field(None, max_length=30)
    id_actividad: Optional[int] = None
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None

