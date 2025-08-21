from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal
from typing import Optional

class PesadaBase(BaseModel):
    transaccion_id: Optional[int] = None
    consecutivo: float
    bascula_id: Optional[int] = None
    peso_meta: Optional[Decimal] = None
    peso_real: Decimal
    peso_vuelo: Optional[Decimal] = None
    peso_fino: Optional[Decimal] = None
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None


class PesadaCreate(PesadaBase):
    transaccion_id: Optional[int] = None
    consecutivo: Optional[float] = None
    bascula_id: Optional[int] = None
    peso_meta: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)
    peso_real: Decimal = Field(..., max_digits=10, decimal_places=2)
    peso_vuelo: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)
    peso_fino: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "transaccion_id": 225123,
                "consecutivo": 16,
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
    peso_meta: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)
    peso_real: Decimal = Field(..., max_digits=10, decimal_places=2)
    peso_vuelo: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)
    peso_fino: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None

class PesadaResponse(PesadaBase):
    id: int

    class Config:
        from_attributes = True


class VPesadasAcumResponse(BaseModel):
    referencia: str
    consecutivo: int
    transaccion: int
    pit: int
    material: str
    peso: Decimal = Field(..., max_digits=10, decimal_places=2)
    puerto_id: Optional[str] = None
    fecha_hora: datetime
    usuario_id: int


    class Config:
        from_attributes = True
