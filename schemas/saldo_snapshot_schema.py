from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import Field

from schemas.base_schema import BaseSchema


class SaldoSnapshotBase(BaseSchema):
    pesada_id: int
    almacenamiento_id: Optional[int] = None
    material_id: Optional[int] = None
    saldo_anterior: Decimal = Field(..., max_digits=15, decimal_places=3)
    saldo_nuevo: Decimal = Field(..., max_digits=15, decimal_places=3)
    fecha_registro: Optional[datetime] = None


class SaldoSnapshotCreate(SaldoSnapshotBase):
    pass


class SaldoSnapshotResponse(SaldoSnapshotBase):
    id: int

    class Config:
        from_attributes = True

