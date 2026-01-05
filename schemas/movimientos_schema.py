from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class MovimientosResponse(BaseModel):
    transaccion_id: Optional[int] = None
    almacenamiento_id: int
    material_id: int
    tipo: str
    accion: str
    observacion: Optional[str] = None
    peso: Decimal
    saldo_anterior: Decimal
    saldo_nuevo: Optional[Decimal] = None
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None

    class Config:
        from_attributes = True

class MovimientosCreate(MovimientosResponse):
    transaccion_id: Optional[int] = None
    almacenamiento_id: Optional[int] = None
    material_id: Optional[int] = None
    tipo: Optional[str] = Field(None, max_length=50)
    accion: Optional[str] = Field(None, max_length=50)
    observacion: Optional[str] = Field(None, max_length=50)
    peso: Optional[Decimal] = Field(..., max_digits=14, decimal_places=2)
    saldo_anterior: Optional[Decimal] = Field(..., max_digits=14, decimal_places=2)
    saldo_nuevo: Optional[Decimal] = Field(..., max_digits=14, decimal_places=2)
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "transaccion_id": 225124,
                "almacenamiento_id": 106,
                "material_id": 12,
                "tipo": "Salida",
                "accion": "Automático",
                "observacion": None,
                "fecha_hora": datetime(2022, 1, 1),
                "peso": 33420.00,
                "saldo_anterior": 334291.22,
                "saldo_nuevo": 300871.22
            }
        }

class MovimientosUpdate(MovimientosCreate):
    pass
