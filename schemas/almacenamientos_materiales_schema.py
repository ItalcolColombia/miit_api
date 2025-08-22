from datetime import datetime

from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional


class AlmacenamientoMaterialesResponse(BaseModel):
    almacenamiento_id: int
    material_id: int
    saldo: Decimal = Field(..., max_digits=10, decimal_places=2)
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None

    class Config:
        from_attributes  = True

class AlmacenamientoMaterialesCreate(AlmacenamientoMaterialesResponse):
    almacenamiento_id: int
    material_id: int
    saldo: Decimal = Field(..., max_digits=10, decimal_places=2)
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "almacenamiento_id": "101",
                "material_id": 2,
                "saldo": 5000
            }
        }

class AlmacenamientoMaterialesUpdate(AlmacenamientoMaterialesResponse):
    almacenamiento_id: str = Field(..., max_length=50)
    material_id: int
    saldo: Decimal = Field(..., max_digits=10, decimal_places=2)
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None

class VAlmMaterialesResponse(BaseModel):
    almacenamiento_id: int
    almacenamiento: str
    material_id: int
    material: str
    saldo: Decimal = Field(..., max_digits=10, decimal_places=2)
    fecha_hora: datetime
    usuario_id: int
    usuario: str


    class Config:
        json_schema_extra = {
            "example": {
                "almacenamiento": "SILO 1",
                "almacenamiento_id": "101",
                "material_id": 2,
                "material": "MAIUSA",
                "saldo": 5000,
                "fecha_hora": "2024-10-02 12:00:00",
                "usuario_id": 1
            }
        }

