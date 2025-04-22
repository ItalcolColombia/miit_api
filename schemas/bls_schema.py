from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

class BlsResponse(BaseModel):
    id: int
    flota_id : int
    material_id : int
    no_bl: str
    peso: Decimal

    class Config:
        from_attributes  = True

class BlsCreate(BaseModel):
    id: int
    flota_id: int
    material_id: int
    no_bl: str = Field(..., max_length=100)
    peso: Decimal = Field(..., max_digits=10, decimal_places=2)

    class Config:
        json_schema_extra = {
            "example": {
                "flota_id": 24330,
                "material": "TORTA SOYA USA",
                "no_bl": "SSF034576272",
                "peso": 15462.00,
            }
        }
