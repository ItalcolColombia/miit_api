from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal
from typing import Optional

class PesadaBase(BaseModel):
    transaccion_id: Optional[int] = None
    consecutivo: float
    bascula_id: Optional[int] = None
    fecha_hora: datetime
    peso_meta: Optional[Decimal] = None
    peso_real: Decimal
    peso_vuelo: Optional[Decimal] = None
    peso_fino: Optional[Decimal] = None

class PesadaCreate(PesadaBase):
    transaccion_id: Optional[int] = None
    consecutivo: Optional[float] = None
    bascula_id: Optional[int] = None
    fecha_hora: Optional[datetime] = None
    peso_meta: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)
    peso_real: Decimal = Field(..., max_digits=10, decimal_places=2)
    peso_vuelo: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)
    peso_fino: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)

    class Config:
        json_schema_extra = {
            "example": {
                "transaccion_id": 225124,
                "consecutivo": 6,
                "bascula_id": 1,
                "fecha_hora": datetime(2024, 5, 17),
                "peso_meta": 0.00,
                "peso_real": 2150.00,
                "peso_vuelo": 0.00,
                "peso_fino": 0.00
            }
        }

class PesadaUpdate(PesadaCreate):
    transaccion_id: Optional[int] = None
    consecutivo: Optional[float] = None
    bascula_id: Optional[int] = None
    fecha_hora: Optional[datetime] = None
    peso_meta: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)
    peso_real: Decimal = Field(..., max_digits=10, decimal_places=2)
    peso_vuelo: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)
    peso_fino: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)

class PesadaResponse(PesadaBase):
    id: int

    class Config:
        from_attributes = True