from pydantic import Field, ConfigDict
from schemas.base_schema import BaseSchema
from decimal import Decimal
from typing import Optional

class BlsResponse(BaseSchema):
    id: int
    viaje_id : int
    material_id : int
    cliente_id: int
    no_bl: str
    peso_bl: Decimal

    model_config = ConfigDict(from_attributes=True)

class BlsCreate(BaseSchema):
    viaje_id: int
    material_id: int
    cliente_id: int
    no_bl: str = Field(..., max_length=100)
    peso_bl: Decimal = Field(..., max_digits=10, decimal_places=2)

    class Config:
        json_schema_extra = {
            "example": {
                "viaje_id": 24330,
                "material_id": "1",
                "cliente_id" : "1",
                "no_bl": "SSF010448001",
                "peso_bl": 50478.00,
            }
        }


class BlsUpdate(BaseSchema):
    viaje_id: int
    material_id: int
    cliente_id: int
    no_bl: str = Field(..., max_length=100)
    peso_bl: Decimal = Field(..., max_digits=10, decimal_places=2)


class BlsExtCreate(BaseSchema):
    puerto_id: str
    viaje_id: Optional[int] = None
    material_name: Optional[str] = None
    material_id: Optional[int] = None
    cliente_name: Optional[str] = None
    cliente_id: Optional[int] = None
    no_bl: str = Field(..., max_length=100)
    peso_bl: Decimal = Field(..., max_digits=10, decimal_places=2)

    class Config:
        json_schema_extra = {
            "example": {
                "puerto_id": "VOY2024001",
                "material_name": "TORTA SOYA USA",
                "cliente_name": "CUSTOMER COMPANY NAME",
                "no_bl": "SSF034576272",
                "peso_bl": 462000.00,
            }
        }