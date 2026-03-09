from datetime import datetime
from typing import Optional

from pydantic import Field

from schemas.base_schema import BaseSchema

class MaterialesResponse(BaseSchema):
    id: int
    codigo : str
    nombre: str
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None

    class Config:
        from_attributes  = True

class MaterialesCreate(BaseSchema):
    codigo: str = Field(..., max_length=10)
    nombre: str = Field(..., max_length=100)
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "codigo": "TORSOYUSA",
                "nombre": "TORTA DE SOYA USA",
            }
        }

class MaterialesUpdate(BaseSchema):
    codigo: Optional[str] = Field(None, max_length=10)
    nombre: Optional[str] = Field(None, max_length=100)
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None

