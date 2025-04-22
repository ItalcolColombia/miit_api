from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional


class AlmacenamientoResponse(BaseModel):
    nombre: str
    capacidad: Decimal
    poli_material: Optional[bool] = False

    class Config:
        from_attributes  = True

class AlmacenamientoCreate(AlmacenamientoResponse):
    nombre: str = Field(..., max_length=50)
    capacidad: Decimal = Field(..., max_digits=10, decimal_places=2)
    poli_material: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "nombre": "SILO 5",
                "capacidad": 1500.00,
                "poli_material": False
            }
        }

class AlmacenamientoUpdate(AlmacenamientoResponse):
    nombre: str = Field(..., max_length=50)
    capacidad: Decimal = Field(..., max_digits=10, decimal_places=2)
    poli_material: bool = False
