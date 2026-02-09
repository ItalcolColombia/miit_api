from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import Field

from schemas.base_schema import BaseSchema


class AjusteCreate(BaseSchema):
    almacenamiento_id: int
    material_id: int
    saldo_nuevo: Decimal = Field(..., ge=0, max_digits=14, decimal_places=2)
    motivo: Optional[str] = Field(None, max_length=255)  # Ahora opcional; el service puede asignar un valor por defecto

class AjusteResponse(BaseSchema):
    id: int
    almacenamiento_id: int
    material_id: int
    saldo_anterior: Decimal
    saldo_nuevo: Decimal
    delta: Decimal
    motivo: str
    usuario_id: int
    movimiento_id: Optional[int] = None
    fecha_hora: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "almacenamiento_id": 106,
                "material_id": 12,
                "saldo_anterior": 1000.00,
                "saldo_nuevo": 1500.00,
                "delta": 500.00,
                "motivo": "Corrección inventario mensual",
                "usuario_id": 2,
                "movimiento_id": 1234,
                "fecha_hora": "2025-12-26T10:00:00Z"
            }
        }
