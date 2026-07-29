from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import Field, model_validator

from schemas.base_schema import BaseSchema


class AjusteCreate(BaseSchema):
    almacenamiento: str = Field(..., max_length=50, description="Nombre del almacenamiento")
    saldo_nuevo: Optional[Decimal] = Field(None, max_digits=14, decimal_places=2)
    delta: Optional[Decimal] = Field(None, max_digits=14, decimal_places=2, description="Cantidad a sumar (positivo) o restar (negativo)")
    material_id: Optional[int] = Field(None, description="ID del material a ajustar. Obligatorio si el almacenamiento tiene 2+ materiales y se usa delta")
    motivo: Optional[str] = Field(None, max_length=255)

    @model_validator(mode='after')
    def validar_ajuste(self):
        if self.saldo_nuevo is not None and self.delta is not None:
            raise ValueError('Debe proporcionar solo saldo_nuevo o delta, no ambos')
        if self.saldo_nuevo is None and self.delta is None:
            raise ValueError('Debe proporcionar saldo_nuevo o delta')
        return self

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
