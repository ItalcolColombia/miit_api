from pydantic import BaseModel, Field
from schemas.base_schema import BaseSchema
from datetime import datetime
from decimal import Decimal
from typing import Optional



class MaterialesResponse(BaseSchema):
    id: int
    nombre: str
    tipo: str
    densidad: Optional[Decimal] = None
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None

    class Config:
        from_attributes  = True

class MaterialesCreate(BaseSchema):
    nombre: str = Field(..., max_length=100)
    tipo: str = Field(..., max_length=50)
    densidad: Decimal = Field(..., max_digits=4, decimal_places=2)
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "nombre": "TORTA DE SOYA USA",
                "tipo" : "Harina",
                "densidad": 0.60
            }
        }

class MaterialesUpdate(BaseSchema):
    nombre: Optional[str] = Field(None, max_length=100)
    tipo: Optional[str] = Field(None, max_length=50)
    densidad: Optional[Decimal] = Field(None, max_digits=4, decimal_places=2)
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None

