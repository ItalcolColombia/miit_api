from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import Field, ConfigDict

from schemas.base_schema import BaseSchema


class ConsumosEntradaParcialResponse(BaseSchema):
    id: int
    puerto_id: str
    bl_id: int
    no_bl: str
    material_id: int
    consecutivo: int
    peso_bl: Decimal
    peso_prorrateado_acumulado: Decimal
    peso_enviado_anterior: Decimal
    delta_peso: Decimal
    fecha_hora: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ConsumosEntradaParcialCreate(BaseSchema):
    puerto_id: str = Field(..., max_length=50)
    bl_id: int
    no_bl: str = Field(..., max_length=100)
    material_id: int
    consecutivo: int
    peso_bl: Decimal = Field(..., max_digits=10, decimal_places=2)
    peso_prorrateado_acumulado: Decimal = Field(..., max_digits=10, decimal_places=2)
    peso_enviado_anterior: Decimal = Field(..., max_digits=10, decimal_places=2)
    delta_peso: Decimal = Field(..., max_digits=10, decimal_places=2)

    class Config:
        json_schema_extra = {
            "example": {
                "puerto_id": "VOY2024008",
                "bl_id": 1,
                "no_bl": "SSF010448001",
                "material_id": 1,
                "consecutivo": 1,
                "peso_bl": 50478.00,
                "peso_prorrateado_acumulado": 25000.00,
                "peso_enviado_anterior": 15000.00,
                "delta_peso": 10000.00,
            }
        }
