from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import Field

from schemas.base_schema import BaseSchema


class MaterialesResponse(BaseSchema):
    id: int
    codigo : str
    nombre: str
    tipo: str
    densidad: Optional[Decimal] = None
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None

    class Config:
        from_attributes  = True

class MaterialesCreate(BaseSchema):
    codigo: str = Field(..., max_length=10)
    nombre: str = Field(..., max_length=100)
    tipo: str = Field(..., max_length=50)
    densidad: Optional[Decimal] = Field(default=Decimal("0.60"), max_digits=4, decimal_places=2)
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "codigo": "TORSOYUSA",
                "nombre": "TORTA DE SOYA USA",
                "tipo" : "Ceral",
                "densidad": 0.60
            }
        }

class MaterialesUpdate(BaseSchema):
    codigo: Optional[str] = Field(None, max_length=10)
    nombre: Optional[str] = Field(None, max_length=100)
    tipo: Optional[str] = Field(None, max_length=50)
    densidad: Optional[Decimal] = Field(None, max_digits=4, decimal_places=2)
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None

